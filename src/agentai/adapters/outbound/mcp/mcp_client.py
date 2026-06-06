import asyncio
import importlib.util
import os
import re
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agentai.core.ports.mcp_port import IMcpClientPort

class RealMcpClientAdapter(IMcpClientPort):
    def __init__(self):
        # Resolve repo root from: src/agentai/adapters/outbound/mcp/mcp_client.py
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(current_file_dir, "../../../../../"))

        self.server_registry = {
            "fintech": {
                "script": os.path.join(base_dir, "backend/mcp_servers/fintech_server.py"),
                "tool": "audit_financial_account",
                "args": self._fintech_args,
            },
            "healthcare": {
                "script": os.path.join(base_dir, "backend/mcp_servers/healthcare_server.py"),
                "tool": "audit_patient_record",
                "args": self._healthcare_args,
            },
            "healthtech": {
                "script": os.path.join(base_dir, "backend/mcp_servers/healthcare_server.py"),
                "tool": "audit_patient_record",
                "args": self._healthcare_args,
            },
            "hr": {
                "script": os.path.join(base_dir, "backend/mcp_servers/hr_server.py"),
                "tool": "summarize_hr_policy",
                "args": self._hr_args,
            },
        }

    def execute_compliance_audit(self, industry: str, query: str) -> str:
        """Synchronous portal executor bridging hex code to async mcp loops"""
        return asyncio.run(self._connect_and_call(industry, query))

    async def _connect_and_call(self, industry: str, query: str) -> str:
        route = self.server_registry.get(industry.lower())
        if not route:
            return f"Error: Compliance tracking track '{industry}' is not registered."

        server_script = route["script"]
        if not os.path.exists(server_script):
            return f"Error: MCP server for '{industry}' is not available."

        # Establish I/O process streaming constraints for the background child server
        server_params = StdioServerParameters(
            command="python3",
            args=[server_script],
            env=os.environ.copy()
        )

        try:
            # Initialize streaming lifecycle context managers
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    response = await session.call_tool(
                        route["tool"],
                        arguments=route["args"](query),
                    )
                    
                    return "".join([content.text for content in response.content if hasattr(content, 'text')])
        except Exception as e:
            return f"Network Protocol Error connecting to {industry} backend module: {str(e)}"

    def _fintech_args(self, query: str) -> dict:
        return {"account_id": self._extract_fintech_id(query)}

    def _healthcare_args(self, query: str) -> dict:
        return {"patient_id": self._extract_healthcare_id(query)}

    def _hr_args(self, query: str) -> dict:
        topic = "remote" if "remote" in query.lower() else "leave"
        return {"policy_topic": topic}

    def _extract_identifier(self, query: str, default: str, pattern: str) -> str:
        match = re.search(pattern, query.upper())
        return match.group(0) if match else default

    def _extract_fintech_id(self, query: str) -> str:
        """Extract fintech account ID from query, supporting both ID format (ACC-991A) and account holder names."""
        # First try to match ID pattern
        match = re.search(r"ACC-[A-Z0-9]+", query.upper())
        if match:
            return match.group(0)
        
        # If no ID found, try to match against account holder names from mock data
        fintech_server_path = Path(__file__).resolve().parents[4] / "backend" / "mcp_servers" / "fintech_server.py"
        if fintech_server_path.exists():
            try:
                spec = importlib.util.spec_from_file_location("fintech_server", fintech_server_path)
                fintech_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(fintech_module)
                
                # Search for matching account holder name
                query_lower = query.lower()
                for account_id, account_data in fintech_module.MOCK_LEDGER.items():
                    holder_name = account_data.get("account_holder", "").lower()
                    if holder_name in query_lower or query_lower in holder_name or holder_name.split()[0] in query_lower:
                        return account_id
            except Exception:
                pass
        
        # Return first account as fallback (better than None)
        return "ACC-991A"

    def _extract_healthcare_id(self, query: str) -> str:
        """Extract healthcare patient ID from query, supporting both ID format (PAT-512E) and patient names."""
        # First try to match ID pattern
        match = re.search(r"PAT-[A-Z0-9]+", query.upper())
        if match:
            return match.group(0)
        
        # If no ID found, try to match against patient names from mock data
        healthcare_server_path = Path(__file__).resolve().parents[4] / "backend" / "mcp_servers" / "healthcare_server.py"
        if healthcare_server_path.exists():
            try:
                spec = importlib.util.spec_from_file_location("healthcare_server", healthcare_server_path)
                healthcare_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(healthcare_module)
                
                # Search for matching patient name
                query_lower = query.lower()
                for patient_id, patient_data in healthcare_module.MOCK_PATIENT_RECORDS.items():
                    patient_name = patient_data.get("patient_name", "").lower()
                    if patient_name in query_lower or query_lower in patient_name or patient_name.split()[0] in query_lower:
                        return patient_id
            except Exception:
                pass
        
        # Return first patient as fallback (better than None)
        return "PAT-204B"
