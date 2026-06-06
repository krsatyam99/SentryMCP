from base64 import b64decode, b64encode
from typing import Optional

from agentai.core.entities.audit_request import AuditRequest
from agentai.core.ports.audio_port import IAudioPort
from agentai.core.ports.mcp_port import IMcpClientPort
from agentai.core.ports.llm_port import ILlmPort
from agentai.core.use_cases.conversation_context import (
    format_conversation_for_llm,
    format_conversation_for_mcp,
)

_TRANSCRIPTION_ERROR_MARKERS = (
    "Transcription requires",
    "TRANSCRIBE_ROLE_ARN",
    "AUDIO_S3_BUCKET",
    "Failed to start transcription",
    "Failed to upload audio",
    "Transcribe job failed",
    "Transcribe polling error",
    "disabled",
    "did not complete within timeout",
)


def _is_transcription_error(text: str) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in _TRANSCRIPTION_ERROR_MARKERS)


class AnalyzeVoiceUseCase:
    def __init__(
        self,
        mcp_client: IMcpClientPort,
        llm_client: ILlmPort,
        audio_client: Optional[IAudioPort] = None,
        synthesize_audio: bool = False,
    ):
        self.mcp_client = mcp_client
        self.llm_client = llm_client
        self.audio_client = audio_client
        self.synthesize_audio = synthesize_audio

    def analyze(self, request: AuditRequest, force_vocalization: Optional[bool] = None) -> dict:
        print(f"[Core UseCase] Executing compliance loop for tracking: {request.industry}")

        should_speak = force_vocalization if force_vocalization is not None else self.synthesize_audio
        history = request.conversation_history or []

        audio_transcription = ""
        if self.audio_client is not None:
            if request.audio_base64:
                try:
                    audio_bytes = b64decode(request.audio_base64)
                except Exception as exc:
                    audio_transcription = f"Invalid audio_base64 payload: {exc}"
                else:
                    media_format = request.audio_media_format or "webm"
                    audio_transcription = self.audio_client.transcribe_audio_bytes(
                        audio_bytes,
                        media_format=media_format,
                    )
            elif request.audio_url:
                audio_transcription = self.audio_client.transcribe_audio(request.audio_url)

        prompt_query = (request.query or "").strip()
        if audio_transcription and not _is_transcription_error(audio_transcription):
            if prompt_query:
                prompt_query = f"{prompt_query}\n\nAudio transcription:\n{audio_transcription}"
            else:
                prompt_query = audio_transcription
        elif not prompt_query and audio_transcription:
            prompt_query = audio_transcription

        if not prompt_query:
            return {
                "status": "ERROR",
                "evaluated_industry": request.industry,
                "original_query": request.query or "",
                "subsystem_extracted_logs": "",
                "audio_transcription": audio_transcription,
                "speech_audio_base64": "",
                "spoken_summary": "",
                "speech_error": "",
                "bedrock_evaluation": {
                    "verdict": "ERROR",
                    "confidence_score": 0.0,
                    "summary": "No query text or usable audio transcription was provided.",
                },
            }

        mcp_query = format_conversation_for_mcp(prompt_query, history)
        llm_query = format_conversation_for_llm(prompt_query, history)

        raw_mcp_data = self.mcp_client.execute_compliance_audit(
            industry=request.industry,
            query=mcp_query,
        )

        ai_analysis = self.llm_client.generate_agent_reasoning(
            user_query=llm_query,
            available_mcp_data=raw_mcp_data,
        )

        spoken_summary = self._build_spoken_summary(ai_analysis)
        speech_audio_base64 = ""
        speech_error = ""
        if should_speak and self.audio_client is not None:
            print("[Voice Pipeline] Voice response requested. Invoking AWS Polly...")
            try:
                speech_bytes = self.audio_client.synthesize_speech(
                    spoken_summary,
                    voice_id=getattr(self.audio_client, "polly_voice_id", "Joanna"),
                    output_format=getattr(self.audio_client, "polly_output_format", "mp3"),
                    force=True,
                )
                if speech_bytes:
                    speech_audio_base64 = b64encode(speech_bytes).decode("utf-8")
                elif not getattr(self.audio_client, "polly_enabled", False):
                    speech_error = "POLLY_ENABLED is false. Set POLLY_ENABLED=true in .env to use Amazon Polly."
            except Exception as exc:
                speech_error = str(exc)
                print(f"[Voice Pipeline] Polly synthesis unavailable: {speech_error}")
        else:
            print("[Voice Pipeline] Text chat detected. Skipping AWS Polly for faster response.")

        display_query = request.query or audio_transcription or prompt_query

        return {
            "status": "COMPLETED",
            "evaluated_industry": request.industry,
            "original_query": display_query,
            "subsystem_extracted_logs": raw_mcp_data,
            "audio_transcription": audio_transcription,
            "speech_audio_base64": speech_audio_base64,
            "spoken_summary": spoken_summary,
            "speech_error": speech_error,
            "bedrock_evaluation": ai_analysis,
        }

    def _build_spoken_summary(self, ai_analysis: dict) -> str:
        verdict = ai_analysis.get("verdict", "UNKNOWN")
        summary = ai_analysis.get("summary", "No analysis summary was generated.")
        return f"Verdict: {verdict}. {summary}"
