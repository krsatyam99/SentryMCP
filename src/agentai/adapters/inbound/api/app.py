import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from agentai.core.entities.audit_request import AuditRequest
from agentai.core.use_cases.analyze import AnalyzeVoiceUseCase
from agentai.adapters.outbound.mcp.mcp_client import RealMcpClientAdapter
from agentai.adapters.outbound.aws.audio_adapter import AwsAudioAdapter
from agentai.adapters.outbound.aws.bedrock_adapter import BedrockAdapter

BASE_DIR = Path(__file__).resolve().parents[3]
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="MCP Compliance Agent MVP",
    description="Multi-domain compliance demo using FastAPI, MCP tools, and an LLM reasoning adapter.",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Boot up our real infrastructure dependencies
mcp_driver = RealMcpClientAdapter()
aws_driver = BedrockAdapter()
audio_driver = AwsAudioAdapter()
polly_enabled = os.getenv("POLLY_ENABLED", "false").lower() == "true"

def _build_use_case():
    return AnalyzeVoiceUseCase(
        mcp_client=mcp_driver,
        llm_client=aws_driver,
        audio_client=audio_driver,
        synthesize_audio=polly_enabled,
    )

@app.post("/analyze")
def analyze_voice_compliance(payload: AuditRequest):
    """Analyze text-based queries. Super fast, completely skips Polly voice generation."""
    # 🎯 FIX: Force vocalization to False for standard text box submissions
    result = _build_use_case().analyze(payload, force_vocalization=False)
    return result

@app.post("/voice-analyze")
def analyze_voice_to_voice(payload: AuditRequest):
    """Analyze microphone queries. Generates and returns synthesized speech output."""
    # 🎯 FIX: Force vocalization to True so it reads out loud when the mic is clicked
    result = _build_use_case().analyze(payload, force_vocalization=True)
    return result

@app.get("/")
def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "status": "online",
        "llm_provider": os.getenv("LLM_PROVIDER", "bedrock"),
        "supported_industries": ["fintech", "healthcare", "hr"],
    }