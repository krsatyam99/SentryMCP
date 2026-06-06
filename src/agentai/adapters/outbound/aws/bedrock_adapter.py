import json
import os
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
        self.use_local_fallback = os.getenv("BEDROCK_LOCAL_FALLBACK", "true").lower() == "true"
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

    def generate_agent_reasoning(self, user_query: str, available_mcp_data: str) -> dict:
        if self.local_only:
            return self._generate_local_reasoning(user_query, available_mcp_data, "Local mode.")

        system_rules = [{
            "text": (
                "You are a versatile, dynamic Data Analytics Assistant. Your core objective is to analyze the retrieved "
                "subsystem data, logs, or database rows and comprehensively answer the operator's query in clear, natural language.\n\n"
                
                "CRITICAL OPERATIONAL RULES:\n"
                "1. ADAPTABILITY: Do not assume a specific industry. Whether the data is fintech, healthcare, education, or generic server logs, "
                "adapt your vocabulary, domain understanding, and perspective entirely to the context of the retrieved data.\n"
                "2. DATA INTEGRITY: You must include ALL key metrics, transaction amounts, timestamps, identifiers, statuses, and critical "
                "data points present in the logs that directly answer or add vital context to the user's question. Do NOT generalize, omit, or truncate specific values.\n"
                "3. FORMAT: Respond using clean, professional, and scannable natural text. Use Markdown headers, bullet points, and tables if they make "
                "the raw data vastly easier for the operator to read and interpret. Avoid wrapping your final response in structural JSON configurations."
            )
        }]

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
            return json.loads(raw_text)
            
        except Exception as bedrock_err:
            print(f"[BedrockAdapter] Bedrock failed: {bedrock_err}. Initializing OpenRouter backup pool...")
            
            # 2. Bedrock Failed! Cycle through our explicit OpenRouter free model list
            if self.openrouter_api_key:
                errors_logged = []
                for model in self.fallback_models:
                    try:
                        print(f"[BedrockAdapter] Attempting fallback endpoint via: {model}")
                        return self._execute_openrouter_call(model, user_query, available_mcp_data)
                    except Exception as model_err:
                        err_msg = f"Model {model} failed: {str(model_err)}"
                        print(f"[BedrockAdapter] {err_msg}")
                        errors_logged.append(err_msg)
                        continue # Step down to the next provider in line
                
                # If we exhausted all free fallback models, format the collective trace string
                combined_errors = "; ".join(errors_logged)
            else:
                combined_errors = "OpenRouter API Key missing."

            # 3. Last resort programmatic fallback
            if self.use_local_fallback:
                return self._generate_local_reasoning(
                    user_query, 
                    available_mcp_data, 
                    f"All cloud providers throttled ({combined_errors}). Local fallback executed."
                )

            return {
                "verdict": "ERROR",
                "confidence_score": 0.0,
                "summary": f"Bedrock failed: {str(bedrock_err)}; OpenRouter pool exhausted: {combined_errors}"
            }

    def _execute_openrouter_call(self, model_id: str, user_query: str, available_mcp_data: str) -> dict:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        system_prompt = (
            "You are a compliance auditing assistant. Analyze the retrieved subsystem data and answer the operator's query comprehensively.\n\n"
            "Return ONLY a valid JSON object with this exact structure:\n"
            "{\n"
            "  \"verdict\": \"CLEARED\" or \"FLAGGED\" or \"ACTION_REQUIRED\",\n"
            "  \"confidence_score\": (0.0 to 1.0),\n"
            "  \"summary\": \"Detailed answer including ALL relevant data from the subsystem logs. Include transaction amounts, account details, compliance status, alerts, and any other information requested or relevant to the query.\"\n"
            "}\n\n"
            "CRITICAL: Include ALL transaction amounts, account details, patient information, and specific data points when present in the retrieved logs. Do NOT omit details."
        )

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
            
        raw_text = choices.get("message", {}).get("content", "").strip()
        if not raw_text:
            raise ValueError("Empty response text content field processed.")
            
        return json.loads(raw_text)

    def _generate_local_reasoning(self, user_query: str, available_mcp_data: str, reason: str) -> dict:
        query = user_query.lower()
        data = available_mcp_data.lower()
        risk_signals = ["fraud" in query, "risk profile: high" in data, "compliance status: under_review" in data, "flagged" in data]
        
        verdict = "DummFLAGGED" if any(risk_signals) else "CLEARED"
        summary = f"{reason} Analysis Result: {available_mcp_data}"
        return {
            "verdict": verdict,
            "confidence_score": 0.85,
            "summary": summary
        }