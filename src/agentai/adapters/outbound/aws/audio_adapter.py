import io
import os
import time
import uuid
from typing import Optional

import boto3
import httpx
from botocore.config import Config
from botocore.exceptions import ClientError
from agentai.core.ports.audio_port import IAudioPort

try:
    from dotenv import load_dotenv  # type: ignore
    _DOTENV_AVAILABLE = True
except Exception:
    _DOTENV_AVAILABLE = False

if _DOTENV_AVAILABLE:
    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../../../.env"))
    except Exception:
        pass


class AwsAudioAdapter(IAudioPort):
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION", "us-east-1")
        self.transcribe_client = boto3.client(
            service_name="transcribe",
            region_name=self.region_name,
            config=Config(retries={"total_max_attempts": 2, "mode": "standard"}),
        )
        self.polly_client = boto3.client(
            service_name="polly",
            region_name=self.region_name,
            config=Config(retries={"total_max_attempts": 2, "mode": "standard"}),
        )

        self.transcribe_role_arn = os.getenv("TRANSCRIBE_ROLE_ARN", "")
        self.language_code = os.getenv("TRANSCRIBE_LANGUAGE_CODE", "en-US")
        self.polly_voice_id = os.getenv("POLLY_VOICE_ID", "Joanna")
        self.polly_output_format = os.getenv("POLLY_OUTPUT_FORMAT", "mp3")
        self.polly_enabled = os.getenv("POLLY_ENABLED", "false").lower() == "true"

    def transcribe_audio(self, audio_uri: str) -> str:
        if not audio_uri:
            return ""

        if not audio_uri.startswith("s3://"):
            return (
                "Transcription requires an S3 URI (s3://bucket/path.wav) in this limited free-tier demo."
            )

        if not self.transcribe_role_arn:
            return (
                "TRANSCRIBE_ROLE_ARN is not configured, so audio transcription is disabled."
            )

        job_name = f"agentai-transcribe-{uuid.uuid4().hex[:8]}"
        media_format = self._infer_media_format(audio_uri)

        start_params = {
            "TranscriptionJobName": job_name,
            "LanguageCode": self.language_code,
            "MediaFormat": media_format,
            "Media": {"MediaFileUri": audio_uri},
            "Settings": {"ShowSpeakerLabels": False},
        }
        if self.transcribe_role_arn:
            start_params["JobExecutionSettings"] = {
                "DataAccessRoleArn": self.transcribe_role_arn
            }

        try:
            self.transcribe_client.start_transcription_job(**start_params)
        except ClientError as exc:
            return f"Failed to start transcription job: {exc.response.get('Error', {}).get('Message', str(exc))}"

        for _ in range(30):
            try:
                job = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )["TranscriptionJob"]
            except ClientError as exc:
                return f"Transcribe polling error: {exc.response.get('Error', {}).get('Message', str(exc))}"

            status = job.get("TranscriptionJobStatus")
            if status == "COMPLETED":
                break
            if status == "FAILED":
                return f"Transcribe job failed: {job.get('FailureReason', 'unknown')}."
            time.sleep(2)
        else:
            return "Transcribe job did not complete within timeout."

        transcript_uri = job.get("Transcript", {}).get("TranscriptFileUri")
        if not transcript_uri:
            return "Transcribe completed but transcript URI is unavailable."

        try:
            response = httpx.get(transcript_uri, timeout=30.0)
            response.raise_for_status()
            payload = response.json()
            transcripts = payload.get("results", {}).get("transcripts", [])
            return transcripts[0].get("transcript", "") if transcripts else ""
        except Exception as exc:
            return f"Failed to retrieve transcription result: {str(exc)}"

    def synthesize_speech(self, text: str, voice_id: str = "Joanna", output_format: str = "mp3") -> bytes:
        if not self.polly_enabled:
            return b""

        try:
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_id,
            )
            audio_stream = response.get("AudioStream")
            if audio_stream is None:
                return b""
            return audio_stream.read()
        except ClientError as exc:
            raise RuntimeError(
                f"Polly synthesis failed: {exc.response.get('Error', {}).get('Message', str(exc))}"
            ) from exc

    def _infer_media_format(self, audio_uri: str) -> str:
        extension = audio_uri.split(".")[-1].lower()
        if extension in {"mp3", "mp4", "wav", "flac", "ogg", "webm", "aac", "m4a"}:
            return extension
        return "wav"
