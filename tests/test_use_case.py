from agentai.core.entities.audit_request import AuditRequest
from agentai.core.use_cases.analyze import AnalyzeVoiceUseCase


class FakeMcpClient:
    def execute_compliance_audit(self, industry: str, query: str) -> str:
        return "Risk Profile: HIGH\nCompliance Status: UNDER_REVIEW\nFlagged Transactions found: 1"


class FakeLlmClient:
    def generate_agent_reasoning(self, user_query: str, available_mcp_data: str) -> dict:
        return {
            "verdict": "FLAGGED",
            "confidence_score": 0.9,
            "summary": "High-risk account requires review.",
        }


def test_analyze_returns_structured_compliance_result():
    request = AuditRequest(
        industry="fintech",
        query="Check account ACC-991A for possible fraud",
    )
    use_case = AnalyzeVoiceUseCase(
        mcp_client=FakeMcpClient(),
        llm_client=FakeLlmClient(),
    )

    result = use_case.analyze(request)

    assert result["status"] == "COMPLETED"
    assert result["evaluated_industry"] == "fintech"
    assert result["bedrock_evaluation"]["verdict"] == "FLAGGED"
