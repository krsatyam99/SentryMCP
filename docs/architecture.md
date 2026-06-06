# Architecture Overview

This document describes the **low-level design (LLD)** of the MCP Compliance Agent MVP. For the full business and extension guide, see [project-guide.md](./project-guide.md). For setup and API reference, see the [README](../README.md).

---

## Architectural Style

The project follows **Clean Architecture** (also called **Hexagonal Architecture** or **Ports & Adapters**).

**Core idea:** business rules live in the center; all infrastructure (HTTP, AWS, MCP subprocesses) sits at the edges and depends inward through abstract ports.

```text
                    ┌─────────────────────────────────┐
                    │         INBOUND ADAPTERS         │
                    │   FastAPI (app.py)               │
                    │   static/index.html              │
                    └───────────────┬─────────────────┘
                                    │ calls
                    ┌───────────────▼─────────────────┐
                    │           CORE / DOMAIN          │
                    │  Entities: AuditRequest          │
                    │  Use Cases: AnalyzeVoiceUseCase  │
                    │  Ports: IMcpClientPort,          │
                    │         ILlmPort, IAudioPort     │
                    └───────────────┬─────────────────┘
                                    │ implemented by
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
┌─────────▼─────────┐   ┌───────────▼──────────┐   ┌─────────▼─────────┐
│  OUTBOUND MCP      │   │  OUTBOUND LLM         │   │  OUTBOUND AUDIO    │
│  mcp_client.py     │   │  bedrock_adapter.py   │   │  audio_adapter.py  │
└─────────┬─────────┘   └──────────────────────┘   └───────────────────┘
          │ spawns
┌─────────▼─────────┐
│  MCP SERVERS       │
│  backend/mcp_      │
│  servers/*.py      │
└───────────────────┘
```

### Dependency Rule

Dependencies always point **inward**. The `core` package never imports FastAPI, boto3, or MCP libraries. Adapters import core ports and entities.

---

## Runtime Flow

### Text Audit (`POST /analyze`)

```text
Client (web UI / curl / API)
    → FastAPI app.py
    → AuditRequest(industry, query, audio_url?)
    → AnalyzeVoiceUseCase.analyze(force_vocalization=False)
        → [optional] IAudioPort.transcribe_audio(audio_url)
        → IMcpClientPort.execute_compliance_audit(industry, query)
            → spawn MCP server subprocess (stdio)
            → ClientSession.call_tool(tool_name, args)
            → return formatted domain log text
        → ILlmPort.generate_agent_reasoning(query, mcp_data)
            → local heuristics | Bedrock | OpenRouter fallback
            → return { verdict, confidence_score, summary }
        → skip Polly TTS (text path)
    → unified JSON response
```

### Voice Audit (`POST /voice-analyze`)

Same flow as above, but `force_vocalization=True` triggers `IAudioPort.synthesize_speech()` via Amazon Polly when `POLLY_ENABLED=true`.

---

## Layers

| Layer | Path | Responsibility |
|-------|------|----------------|
| **Domain / Core** | `src/agentai/core/` | Entities, use cases, abstract ports — no framework or cloud SDK imports |
| **Inbound Adapter** | `src/agentai/adapters/inbound/api/` | HTTP entrypoint — parses requests, wires dependencies, returns JSON |
| **Outbound MCP** | `src/agentai/adapters/outbound/mcp/` | Spawns domain MCP servers, routes industry → tool, extracts IDs from natural language |
| **Outbound LLM** | `src/agentai/adapters/outbound/aws/bedrock_adapter.py` | Bedrock → OpenRouter free pool → local heuristics provider chain |
| **Outbound Audio** | `src/agentai/adapters/outbound/aws/audio_adapter.py` | Amazon Transcribe (S3 input) and Polly (TTS output) |
| **MCP Servers** | `backend/mcp_servers/` | Standalone domain tools run as child processes over stdio |
| **Config** | `src/agentai/config/` | `.env` loading via `python-dotenv` |
| **Static UI** | `src/agentai/static/` | Built-in Tailwind web workspace served at `GET /` |

---

## Design Patterns

| Pattern | Where | Why |
|---------|-------|-----|
| **Ports & Adapters** | `core/ports/*` + `adapters/*` | Core logic testable and swappable without AWS/MCP/FastAPI |
| **Use Case** | `AnalyzeVoiceUseCase` | Single orchestration point for the compliance workflow |
| **Dependency Injection** | `app.py` wires real adapters | Tests inject fakes; production uses real infrastructure |
| **Strategy / Provider Chain** | `BedrockAdapter` | Resilient LLM path: local → Bedrock → OpenRouter → local fallback |
| **Registry / Router** | `RealMcpClientAdapter.server_registry` | Maps industry string to MCP server script, tool name, and argument extractor |
| **Facade** | FastAPI `app.py` | Thin HTTP layer over one use case |
| **Subprocess Isolation** | MCP stdio client | Each domain server is an independent process — mirrors real MCP deployments |

---

## MCP Domain Routing

The MCP client adapter maintains a registry that maps each industry to a server script, tool, and argument parser:

| Industry | Server | Tool | Argument Extraction |
|----------|--------|------|---------------------|
| `fintech` | `fintech_server.py` | `audit_financial_account` | `ACC-XXXX` regex or account holder name match |
| `healthcare` / `healthtech` | `healthcare_server.py` | `audit_patient_record` | `PAT-XXXX` regex or patient name match |
| `hr` | `hr_server.py` | `summarize_hr_policy` | Keyword map → policy topic keys |

Each server uses `FastMCP`, exposes one `@mcp.tool()`, and returns mock domain data. No server imports the main `agentai` package.

---

## LLM Provider Chain

`BedrockAdapter` implements `ILlmPort` with a fallback chain:

```text
LLM_PROVIDER=local  →  keyword heuristics only (no cloud)

LLM_PROVIDER=bedrock:
    1. AWS Bedrock converse API (default: amazon.nova-micro-v1:0)
    2. On failure → OpenRouter free model pool
    3. On failure → local heuristics (if BEDROCK_LOCAL_FALLBACK=true)
```

The LLM is instructed to return a fixed JSON schema:

```json
{
  "verdict": "CLEARED | FLAGGED | ACTION_REQUIRED | ERROR",
  "confidence_score": 0.0,
  "summary": "..."
}
```

---

## Design Choices

| Decision | Rationale |
|----------|-----------|
| Use case has no FastAPI/boto3/MCP imports | Business logic survives framework and cloud SDK changes |
| One MCP server per industry | Routing is visible in demos; new domains are additive |
| MCP servers outside `src/agentai/` | Spawned as subprocesses; no circular package dependency |
| `LLM_PROVIDER=local` default for demos | Works without AWS quota or API keys |
| Mock data in MCP servers | No real PII or financial data; safe for portfolio demos |
| Separate `/analyze` and `/voice-analyze` | Text path skips Polly for faster responses |
| Ports as ABCs (not protocols) | Simple, explicit contracts easy to fake in tests |

---

## Client Interfaces

The system exposes three ways to interact with the same use case:

| Interface | Location | Transport |
|-----------|----------|-----------|
| **Built-in Web UI** | `src/agentai/static/index.html` | Browser → FastAPI (`/analyze`, `/voice-analyze`) |
| **REST API** | `src/agentai/adapters/inbound/api/app.py` | HTTP JSON |

Both converge on `AnalyzeVoiceUseCase` — the core workflow is identical regardless of client.

---

## Testing Strategy

Unit tests live in `tests/test_use_case.py` and inject fake port implementations:

- `FakeMcpClient` — returns mock high-risk ledger text
- `FakeLlmClient` — returns a structured `FLAGGED` verdict

This validates orchestration logic without AWS credentials, network calls, or MCP subprocesses.

---

## MVP Scope

**In scope:**

- Multi-domain MCP routing (FinTech, Healthcare, HR)
- Clean architecture with swappable adapters
- Local demo mode (no cloud dependency)
- Built-in web UI (`index.html`) and REST API
- Text and voice interaction paths
- Optional AWS Transcribe + Polly integration

**Out of scope (intentionally):**

- Production authentication / authorization
- Real customer, patient, or financial data
- Persistent storage or audit logging
- CI/CD and cloud deployment

**Natural extensions:**

- Additional MCP domain servers (legal, retail, IoT)
- Real database connectors replacing mock data
- AgentCore / CloudFront deployment
- Authentication middleware on FastAPI routes
