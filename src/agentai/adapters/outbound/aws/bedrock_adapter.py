import json
import os
import re
import httpx
import boto3
from botocore.config import Config
from agentai.core.ports.llm_port import ILlmPort

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

class BedrockAdapter(ILlmPort):
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION", "us-east-1")
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region_name,
            config=Config(retries={"total_max_attempts": 1, "mode": "standard"}),
        )
        
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
        self.max_tokens = int(os.getenv("BEDROCK_MAX_TOKENS", "1000"))
        self.use_local_fallback = os.getenv("BEDROCK_LOCAL_FALLBACK", "false").lower() == "true"
        self.local_only = os.getenv("LLM_PROVIDER", "bedrock").lower() == "local"

        # OpenRouter Configuration
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        # Array of highly capable free fallback models from diverse upstream providers
        self.fallback_models = [
            "openrouter/free",                        # 1. Dynamic routing catch-all
            "openai/gpt-oss-120b:free",               # 2. OpenAI Hosted Back-up
            "nvidia/nemotron-3-super-120b-a12b:free", # 3. NVIDIA Hosted Back-up
            "qwen/qwen3-coder:free"                   # 4. Alibaba Qwen Hosted Back-up
        ]
        
        print(f"[BedrockAdapter] Target: {self.model_id} | Multi-Model Free Fallback Pool Enabled")

    def _build_reasoning_contract(self) -> str:
        return (
            "You are an MCP-native analysis assistant for a company assignment MVP. "
            "Your job is to interpret data returned by whichever MCP tool was selected and answer the operator's query.\n\n"
            "The MCP server may represent any business space: finance, healthcare, HR, education, legal operations, retail, "
            "support tickets, security logs, IoT telemetry, supply chain, or a custom company plugin. Do not lock your reasoning "
            "to one industry. Infer the domain only from the operator query and retrieved MCP data.\n\n"
            "Rules:\n"
            "1. Use only the retrieved MCP data and the operator query. Do not invent records, policies, identifiers, risk scores, "
            "timestamps, names, amounts, diagnoses, transactions, or tool results.\n"
            "2. Preserve important concrete details from the MCP data: IDs, names, statuses, scores, amounts, timestamps, alerts, "
            "counts, categories, locations, and explicit policy or compliance findings.\n"
            "3. If the MCP data is missing, ambiguous, or from an unregistered plugin, explain what is missing and set the verdict "
            "to ACTION_REQUIRED.\n"
            "4. Treat audio transcription as another form of the operator query. Do not mention voice or chat unless it affects the analysis.\n"
            "5. Keep the summary professional, concise, and readable for a reviewer evaluating a reusable MVP.\n"
            "6. If the operator asks for a table, put a compact Markdown table inside the summary field.\n\n"
            "Return ONLY a valid JSON object with this exact schema:\n"
            "{\n"
            "  \"verdict\": \"CLEARED\" | \"FLAGGED\" | \"ACTION_REQUIRED\" | \"ERROR\",\n"
            "  \"confidence_score\": 0.0,\n"
            "  \"summary\": \"A domain-aware answer grounded in the MCP data, including the key evidence and next action when needed.\"\n"
            "}\n\n"
            "Verdict guidance:\n"
            "- CLEARED: the data directly supports a normal, resolved, or compliant state.\n"
            "- FLAGGED: the data shows explicit risk, violation, anomaly, failed check, suspension, high severity, or unresolved concern.\n"
            "- ACTION_REQUIRED: more information, human review, missing tool coverage, or follow-up is needed.\n"
            "- ERROR: the retrieved MCP data is an execution/protocol error rather than business data."
        )

    def generate_agent_reasoning(self, user_query: str, available_mcp_data: str) -> dict:
        if self.local_only:
            return self._generate_local_reasoning(user_query, available_mcp_data, "Local mode.")

        system_rules = [{"text": self._build_reasoning_contract()}]

        user_payload = f"Operator Query: {user_query}\n\nRetrieved Subsystem Data:\n{available_mcp_data}"
        messages = [{
            "role": "user",
            "content": [{"text": user_payload}]
        }]

        # 1. Primary Call via AWS Bedrock
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                system=system_rules,
                inferenceConfig={"temperature": 0.1, "maxTokens": self.max_tokens}
            )
            raw_text = response["output"]["message"]["content"]["text"].strip()
            return self._with_provider_metadata(json.loads(raw_text), "bedrock", "")
            
        except Exception as bedrock_err:
            bedrock_reason = self._summarize_provider_error(bedrock_err)
            print(f"[BedrockAdapter] Bedrock failed: {bedrock_reason}. Initializing OpenRouter backup pool...")
            
            # 2. Bedrock Failed! Cycle through our explicit OpenRouter free model list
            if self.openrouter_api_key:
                errors_logged = []
                for model in self.fallback_models:
                    try:
                        print(f"[BedrockAdapter] Attempting fallback endpoint via: {model}")
                        result = self._execute_openrouter_call(model, user_query, available_mcp_data)
                        return self._with_provider_metadata(
                            result,
                            f"openrouter:{model}",
                            f"Bedrock unavailable: {bedrock_reason}. Free fallback used: {model}."
                        )
                    except Exception as model_err:
                        err_msg = f"{model}: {self._summarize_provider_error(model_err)}"
                        print(f"[BedrockAdapter] {err_msg}")
                        errors_logged.append(err_msg)
                        continue # Step down to the next provider in line
                
                combined_errors = self._summarize_openrouter_errors(errors_logged)
            else:
                combined_errors = "OpenRouter API key missing."

            if self.use_local_fallback:
                return self._generate_local_reasoning(
                    user_query, 
                    available_mcp_data, 
                    f"AI provider fallback unavailable. Bedrock: {bedrock_reason}. Free models: {combined_errors}."
                )

            return {
                "verdict": "ERROR",
                "confidence_score": 0.0,
                "summary": (
                    f"AI provider unavailable. Bedrock failed: {bedrock_reason}. "
                    f"Free fallback failed: {combined_errors}. MCP server data is available in the extracted logs."
                ),
                "provider": "none",
                "provider_note": f"Bedrock failed: {bedrock_reason}. Free fallback failed: {combined_errors}."
            }

    def _execute_openrouter_call(self, model_id: str, user_query: str, available_mcp_data: str) -> dict:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        system_prompt = self._build_reasoning_contract()

        user_content = f"Operator Query: {user_query}\n\nData Logs:\n{available_mcp_data}"

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"}
        }

        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        
        response_data = response.json()
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError(f"Empty choice metadata structure returned from OpenRouter payload: {response_data}")
            
        raw_content = choices[0].get("message", {}).get("content")
        raw_text = raw_content.strip() if isinstance(raw_content, str) else ""
        if not raw_text:
            raise ValueError("Empty response text content field processed.")
            
        return json.loads(raw_text)

    def _with_provider_metadata(self, result: dict, provider: str, provider_note: str) -> dict:
        result.setdefault("verdict", "ACTION_REQUIRED")
        result.setdefault("confidence_score", 0.0)
        result.setdefault("summary", "")
        result["provider"] = provider
        result["provider_note"] = provider_note
        return result

    def _summarize_provider_error(self, error: Exception) -> str:
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            if status_code == 429:
                return "rate limit reached"
            if status_code in {401, 403}:
                return "authentication or permission issue"
            return f"HTTP {status_code}"

        message = str(error)
        lower_message = message.lower()
        if "throttl" in lower_message or "too many requests" in lower_message:
            return "rate limit reached"
        if "accessdenied" in lower_message or "not authorized" in lower_message or "forbidden" in lower_message:
            return "authentication or permission issue"
        if "could not connect" in lower_message or "timeout" in lower_message:
            return "network timeout"
        if "json" in lower_message or "unterminated string" in lower_message or "empty response" in lower_message:
            return "invalid model response"
        return re.sub(r"\s+", " ", message).strip()[:140] or "unknown error"

    def _summarize_openrouter_errors(self, errors_logged: list[str]) -> str:
        if not errors_logged:
            return "no free model returned a valid response"

        reasons = []
        for entry in errors_logged:
            reason = entry.split(": ", 1)[-1]
            if reason not in reasons:
                reasons.append(reason)

        if len(reasons) == 1:
            return reasons[0]
        return "; ".join(reasons[:3])

    def _generate_local_reasoning(self, user_query: str, available_mcp_data: str, reason: str) -> dict:
        query = user_query.lower()
        data = available_mcp_data.lower()
        error_signals = ["error:" in data, "network protocol error" in data, "not registered" in data]
        risk_signals = [
            "fraud" in query,
            "risk profile: high" in data,
            "compliance status: under_review" in data,
            "consent status: revoked" in data,
            "phi exposure level: high" in data,
            "open compliance alerts" in data,
            "suspended" in data,
            "flagged" in data,
            "violation" in data,
            "failed" in data,
        ]
        
        if any(error_signals):
            verdict = "ERROR"
        elif any(risk_signals):
            verdict = "FLAGGED"
        elif not available_mcp_data.strip():
            verdict = "ACTION_REQUIRED"
        else:
            verdict = "CLEARED"
        summary = f"{reason} MCP server data: {available_mcp_data}"
        return {
            "verdict": verdict,
            "confidence_score": 0.85,
            "summary": summary,
            "provider": "local",
            "provider_note": reason
        }
