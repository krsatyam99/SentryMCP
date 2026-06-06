from base64 import b64encode
from typing import Optional

from agentai.core.entities.audit_request import AuditRequest
from agentai.core.ports.audio_port import IAudioPort
from agentai.core.ports.mcp_port import IMcpClientPort
from agentai.core.ports.llm_port import ILlmPort

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

        # Determine whether to speak aloud: check explicit override first, then fallback to class initialization default
        should_speak = force_vocalization if force_vocalization is not None else self.synthesize_audio

        audio_transcription = ""
        if request.audio_url and self.audio_client is not None:
            audio_transcription = self.audio_client.transcribe_audio(request.audio_url)

        prompt_query = request.query
        if audio_transcription and "Transcription requires" not in audio_transcription and "disabled" not in audio_transcription:
            prompt_query = f"{request.query}\n\nAudio transcription:\n{audio_transcription}"

        # 1. Fetch live system information from our protocol client
        raw_mcp_data = self.mcp_client.execute_compliance_audit(
            industry=request.industry,
            query=prompt_query
        )
        
        # 2. Feed the results into the LLM Engine for intelligent analysis
        ai_analysis = self.llm_client.generate_agent_reasoning(
            user_query=prompt_query,
            available_mcp_data=raw_mcp_data
        )

        # 🎯 OPTIMIZATION FIX: Generate audio ONLY if should_speak is evaluated as True
        speech_audio_base64 = ""
        if should_speak and self.audio_client is not None:
            print("[Voice Pipeline] Mic input detected or vocalization forced. Invoking AWS Polly...")
            speech_bytes = self.audio_client.synthesize_speech(
                ai_analysis.get("summary", ""),
                voice_id=getattr(self.audio_client, "polly_voice_id", "Joanna"),
                output_format=getattr(self.audio_client, "polly_output_format", "mp3"),
            )
            if speech_bytes:
                speech_audio_base64 = b64encode(speech_bytes).decode("utf-8")
        else:
            print("[Voice Pipeline] Text chat detected. Skipping AWS Polly calculation for faster response.")

        # 3. Compile the structural unified response object
        return {
            "status": "COMPLETED",
            "evaluated_industry": request.industry,
            "original_query": request.query,
            "subsystem_extracted_logs": raw_mcp_data,
            "audio_transcription": audio_transcription,
            "speech_audio_base64": speech_audio_base64,
            "bedrock_evaluation": ai_analysis
        }