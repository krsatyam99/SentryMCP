from abc import ABC, abstractmethod
from typing import Dict, Any

class ILlmPort(ABC):
    @abstractmethod
    def generate_agent_reasoning(self, user_query: str, available_mcp_data: str) -> Dict[str, Any]:
        """
        Passes data parameters to Amazon Bedrock to synthesize a compliance verdict.
        """
        pass