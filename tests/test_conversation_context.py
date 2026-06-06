from agentai.core.entities.audit_request import AuditRequest
from agentai.core.use_cases.analyze import AnalyzeVoiceUseCase
from agentai.core.use_cases.conversation_context import (
    format_conversation_for_llm,
    format_conversation_for_mcp,
)


class RecordingMcpClient:
    def __init__(self):
        self.last_query = ""

    def execute_compliance_audit(self, industry: str, query: str) -> str:
        self.last_query = query
        return "Account: ACC-991A\nRisk Profile: HIGH"


class RecordingLlmClient:
    def __init__(self):
        self.last_query = ""

    def generate_agent_reasoning(self, user_query: str, available_mcp_data: str) -> dict:
        self.last_query = user_query
        return {
            "verdict": "FLAGGED",
            "confidence_score": 0.9,
            "summary": "Follow-up understood.",
        }


def test_format_conversation_for_mcp_includes_prior_user_turns():
    history = [
        {"role": "user", "content": "Check account ACC-991A for fraud"},
        {"role": "assistant", "content": "Verdict: FLAGGED. High risk."},
    ]
    merged = format_conversation_for_mcp("What about their flagged transactions?", history)
    assert "ACC-991A" in merged
    assert "flagged transactions" in merged.lower()


def test_format_conversation_for_llm_includes_history():
    history = [{"role": "user", "content": "Check patient PAT-204B"}]
    prompt = format_conversation_for_llm("Is consent still valid?", history)
    assert "PAT-204B" in prompt
    assert "Latest operator message" in prompt


def test_use_case_passes_conversation_context_to_ports():
    mcp = RecordingMcpClient()
    llm = RecordingLlmClient()
    use_case = AnalyzeVoiceUseCase(mcp_client=mcp, llm_client=llm)

    request = AuditRequest(
        industry="fintech",
        query="What about their flagged transactions?",
        conversation_history=[
            {"role": "user", "content": "Check account ACC-991A for possible fraud"},
            {"role": "assistant", "content": "Verdict: FLAGGED. Account under review."},
        ],
    )

    result = use_case.analyze(request)

    assert result["status"] == "COMPLETED"
    assert "ACC-991A" in mcp.last_query
    assert "Previous conversation" in llm.last_query
    assert "flagged transactions" in llm.last_query.lower()
