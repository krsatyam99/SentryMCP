from abc import ABC, abstractmethod

class IMcpClientPort(ABC):
    @abstractmethod
    def execute_compliance_audit(self, industry: str, query: str) -> str:
        """
        Contract method to fetch compliance data from an industry MCP server.
        """
        pass