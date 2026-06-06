# MCP Compliance Agent — Project Guide

A reader-facing guide for reviewers, interviewers, and engineers who want to understand **what this project does**, **why it exists**, **how it is built**, and **how to extend it**.

For setup and API reference, see the [README](../README.md). For layer-level LLD notes, see [architecture.md](./architecture.md).

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Problem & Solution](#business-problem--solution)
3. [What This Project Demonstrates (Assignment / Portfolio)](#what-this-project-demonstrates-assignment--portfolio)
4. [High-Level Design (HLD)](#high-level-design-hld)
5. [Low-Level Design (LLD)](#low-level-design-lld)
6. [End-to-End Request Flow](#end-to-end-request-flow)
7. [Multi-Turn Conversations](#multi-turn-conversations)
8. [Domain Plugins (FinTech, Healthcare, HR)](#domain-plugins-fintech-healthcare-hr)
9. [Voice-to-Voice (Recognition + Polly)](#voice-to-voice-recognition--polly)
10. [How to Connect Your Own MCP Server](#how-to-connect-your-own-mcp-server)
11. [AWS Integration](#aws-integration)
12. [Future Scope](#future-scope)

---

## Executive Summary

**SentryMCP** (package: `cross-industry-voice-dataguard`) is a **multi-domain compliance auditing MVP**.

An operator asks a natural-language question — by **text** or **voice** — such as:

- *"Check account ACC-991A for possible fraud"*
- *"Check patient PAT-204B for compliance risk"*
- *"Summarize leave policy for an employee"*

The system:

1. Routes the request to the correct **industry MCP server**
2. Fetches domain data through an **MCP tool**
3. Reasons over that data with an **LLM** (AWS Bedrock with fallbacks)
4. Returns a structured verdict: `CLEARED`, `FLAGGED`, `ACTION_REQUIRED`, or `ERROR`
5. Optionally **speaks** the verdict with **Amazon Polly** on the voice path

The frontend is a single-page web UI at `src/agentai/static/index.html`, served by FastAPI at `GET /`.

---

## Business Problem & Solution

### Problem

Compliance and risk teams operate across **siloed subsystems**:

| Domain | Typical subsystem | Manual pain |
|--------|-------------------|-------------|
| FinTech | Ledger / AML | Analysts jump between dashboards to check account risk |
| Healthcare | Patient / PHI records | Consent and exposure checks are fragmented |
| HR | Policy repositories | Policy answers require searching multiple documents |

Each check is **slow**, **inconsistent**, and **hard to audit** — especially under time pressure.

### Solution

This MVP provides **one compliance interface** that:

- Accepts **plain-language** audit questions (text or voice)
- Uses **MCP** to pull data from the correct domain backend (mocked in this POC)
- Uses an **LLM** to produce a **structured, explainable verdict**
- Supports **multi-turn conversation** so follow-up questions like *"What about their flagged transactions?"* keep context from earlier turns
- Returns JSON suitable for dashboards, workflows, or human review

### Business value (even as a POC)

- **Faster triage** — seconds instead of switching tools
- **Consistent output** — same JSON schema every time
- **Pluggable domains** — new industries add an MCP server, not a rewrite
- **Demo-ready** — voice + text for stakeholder presentations

---

## What This Project Demonstrates (Assignment / Portfolio)

This project is designed as a **professional proof of concept** suitable for:

- University / company **assignments** on AI agents and compliance automation
- **Portfolio** and **LinkedIn** demos
- Interviews discussing **system design**, not just API calls

### Technical competencies shown

| Competency | Evidence in repo |
|------------|------------------|
| **Clean / Hexagonal Architecture** | `core/` ports + `adapters/` |
| **MCP protocol** | `backend/mcp_servers/*.py` + `mcp_client.py` |
| **Multi-domain routing** | `server_registry` by `industry` |
| **LLM integration** | `bedrock_adapter.py` with fallback chain |
| **Multimodal UX** | Browser speech recognition + Polly TTS |
| **Structured AI output** | Fixed JSON verdict contract |
| **Testability** | Fake ports in `tests/` |
| **Conversation context** | `conversation_history` + `conversation_context.py` |

### Assignment framing (suggested)

> *Build a reusable compliance agent that connects to heterogeneous enterprise subsystems via MCP, produces auditable structured verdicts, and supports operator-friendly text and voice interaction — without hard-coding each domain into the orchestration layer.*

---

## High-Level Design (HLD)

### System context

```text
                    ┌─────────────────────────────────────┐
                    │           Operators / API clients    │
                    │   (Web UI, curl, integrations)       │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │     Compliance Agent Platform        │
                    │  FastAPI + Use Case Orchestrator     │
                    └───────┬──────────────────┬──────────┘
                            │                  │
              ┌─────────────▼────────┐   ┌─────▼──────────────┐
              │   MCP Client Layer      │   │   LLM Adapter       │
              │   (domain routing)      │   │   (Bedrock / etc.)  │
              └─────────────┬──────────┘   └────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
   ┌─────▼─────┐    ┌───────▼──────┐   ┌──────▼──────┐
   │ FinTech   │    │ Healthcare   │   │ HR Policy   │
   │ MCP Server│    │ MCP Server   │   │ MCP Server  │
   └───────────┘    └──────────────┘   └─────────────┘
```

### HLD principles

1. **One orchestrator** — `AnalyzeVoiceUseCase` owns the workflow
2. **Many domain plugins** — each industry is an MCP server process
3. **Swappable AI** — LLM and audio are ports, not hard dependencies in core logic
4. **Thin HTTP layer** — FastAPI parses requests and wires dependencies only

---

## Low-Level Design (LLD)

### Layer map

| Layer | Path | Responsibility |
|-------|------|----------------|
| **Entity** | `core/entities/audit_request.py` | Input model: industry, query, optional audio, `conversation_history` |
| **Ports** | `core/ports/*.py` | Abstract interfaces: MCP, LLM, Audio |
| **Use case** | `core/use_cases/analyze.py` | Orchestration: transcribe → MCP → LLM → Polly |
| **Context helper** | `core/use_cases/conversation_context.py` | Merge chat history for MCP ID extraction and LLM prompts |
| **Inbound adapter** | `adapters/inbound/api/app.py` | FastAPI routes, static UI |
| **Outbound MCP** | `adapters/outbound/mcp/mcp_client.py` | Spawn MCP subprocess, route tools, extract IDs |
| **Outbound LLM** | `adapters/outbound/aws/bedrock_adapter.py` | Bedrock → OpenRouter → local fallback |
| **Outbound audio** | `adapters/outbound/aws/audio_adapter.py` | Polly TTS; optional Transcribe + S3 |
| **MCP servers** | `backend/mcp_servers/` | Domain tools with mock data |

### Dependency rule

Dependencies point **inward**. `core/` never imports FastAPI, boto3, or MCP libraries.

### Key design patterns

| Pattern | Where | Why |
|---------|-------|-----|
| Ports & Adapters | `core/ports` + `adapters/` | Testability and swappable infrastructure |
| Registry / Router | `mcp_client.server_registry` | Map `industry` → server + tool |
| Strategy chain | `BedrockAdapter` | Resilient LLM when quota fails |
| Use case | `AnalyzeVoiceUseCase` | Single workflow entry point |

---

## End-to-End Request Flow

### Text chat (`POST /analyze`)

```text
index.html
  → { industry, query, conversation_history }
  → AnalyzeVoiceUseCase
  → MCP tool call (with merged history for ID extraction)
  → Bedrock reasoning (with conversation in prompt)
  → JSON response (no Polly)
```

### Voice (`POST /voice-analyze`)

```text
Browser SpeechRecognition
  → transcribed text
  → same pipeline as above
  → Amazon Polly speaks verdict (POLLY_ENABLED=true)
  → browser plays MP3
```

---

## Multi-Turn Conversations

### Problem (before)

Each request was **stateless**. Follow-up questions like *"What about their transactions?"* lost the account or patient from turn one.

### Solution (now)

The web UI sends `conversation_history` — prior `{role, content}` turns — with each request.

| Component | Behavior |
|-----------|----------|
| **Frontend** | Maintains last 12 turns; resets when industry changes |
| **MCP client** | Receives merged user text so `ACC-991A` / `PAT-204B` from earlier turns are still found |
| **LLM** | Receives formatted history so pronouns like *"their"* resolve correctly |

Example:

```text
Turn 1: "Check account ACC-991A for fraud"
Turn 2: "What about their flagged transactions?"   ← works without repeating ACC-991A
```

---

## Domain Plugins (FinTech, Healthcare, HR)

| Industry | MCP server | Tool | Example ID |
|----------|------------|------|------------|
| `fintech` | `fintech_server.py` | `audit_financial_account` | `ACC-991A` |
| `healthcare` | `healthcare_server.py` | `audit_patient_record` | `PAT-204B` |
| `hr` | `hr_server.py` | `summarize_hr_policy` | keyword → policy topic |

Each server uses **mock data** for safe demos. Production would replace mocks with real API/database connectors behind the same MCP tool interface.

---

## Voice-to-Voice (Recognition + Polly)

Default voice mode — **no S3 bucket required**:

| Step | Technology |
|------|------------|
| Speech in | Browser **Speech Recognition** (Chrome/Edge) |
| Analysis | MCP + **Bedrock** |
| Speech out | **Amazon Polly** (`POLLY_ENABLED=true`) |

Configure in `.env`:

```env
POLLY_ENABLED=true
POLLY_VOICE_ID=Joanna
```

Verify: `GET /audio-config` → `"voice_mode": "recognition_polly"`.

---

## How to Connect Your Own MCP Server

This is how an organization **plugs their subsystem** into the agent.

### Step 1 — Create an MCP server

Create `backend/mcp_servers/your_domain_server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Your Domain Compliance Server")

@mcp.tool()
def audit_your_resource(resource_id: str) -> str:
    # Call your real API / database here
    return f"Resource {resource_id}: status OK"

if __name__ == "__main__":
    mcp.run()
```

Test standalone:

```bash
python backend/mcp_servers/your_domain_server.py
```

### Step 2 — Register in the MCP client

Edit `src/agentai/adapters/outbound/mcp/mcp_client.py` — add to `server_registry`:

```python
"your_industry": {
    "script": os.path.join(base_dir, "backend/mcp_servers/your_domain_server.py"),
    "tool": "audit_your_resource",
    "args": self._your_domain_args,
},
```

Implement `_your_domain_args(self, query: str)` to extract `resource_id` from natural language (regex, keywords, or conversation-merged text).

### Step 3 — Add UI option

In `src/agentai/static/index.html`, add an `<option>` to the industry `<select>`.

### Step 4 — Restart API

```bash
python -m uvicorn agentai.adapters.inbound.api.app:app --host 0.0.0.0 --port 8000
```

### Step 5 — Test

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"industry": "your_industry", "query": "Audit resource RES-001"}'
```

### Production notes

- Replace mock data with authenticated calls to your internal API
- Run MCP servers as managed sidecars or remote MCP endpoints
- Add per-domain authorization at the tool level
- Keep the **tool output as text** the LLM can reason over

---

## AWS Integration

| Service | Role in MVP | Required? |
|---------|-------------|-----------|
| **Bedrock** | LLM verdict | Optional (`LLM_PROVIDER=local` for offline demo) |
| **Polly** | Voice responses | Optional (`POLLY_ENABLED=true`) |
| **Transcribe + S3** | AWS speech-to-text | Optional (browser recognition is default) |
| **OpenRouter** | LLM fallback | Optional |

---

## Future Scope

| Enhancement | Benefit |
|-------------|---------|
| Server-side session store | Persist conversations across page reloads |
| Real database connectors | Production-grade domain data |
| Authentication / RBAC | Enterprise deployment |
| Audit logging | Compliance trail for every verdict |
| CI/CD + cloud deploy | AgentCore, ECS, or Lambda |
| Additional MCP domains | Legal, retail, security logs, IoT |
| Transcribe streaming | AWS speech input without S3 batch jobs |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Setup, run, API, env vars |
| [architecture.md](./architecture.md) | LLD layer diagram and runtime flow |
| [linkedin-demo-script.md](./linkedin-demo-script.md) | 90-second demo script |
