# SentryMCP

**Multi-domain compliance agent** — ask audit questions in plain English or by voice, route to the right subsystem via **MCP**, get a structured verdict from **AWS Bedrock**, hear it aloud with **Amazon Polly**.

| | |
|---|---|
| **Stack** | Python · FastAPI · MCP · Bedrock · Polly |
| **Domains** | FinTech · Healthcare · HR |
| **Pattern** | Clean / Hexagonal architecture (ports & adapters) |

---

## Why

Compliance teams jump between **siloed systems** (ledgers, patient records, HR policies). Checks are slow, inconsistent, and hard to audit. SentryMCP gives **one interface** for natural-language compliance triage with **explainable JSON verdicts** (`CLEARED` · `FLAGGED` · `ACTION_REQUIRED`).

## What

- **Text or voice** audits through a built-in web UI (`GET /`)
- **MCP routing** to domain-specific tools (mock data in this POC)
- **LLM reasoning** with Bedrock + fallback chain
- **Multi-turn chat** — follow-ups like *"What about their flagged transactions?"* keep context
- **Voice-to-voice** — browser speech recognition in, Polly out

## How (30-second view)

```text
Operator → Web UI / API → FastAPI → AnalyzeVoiceUseCase
    → MCP server (FinTech | Healthcare | HR)
    → Bedrock LLM → structured verdict → (optional) Polly TTS
```

---

## Architecture

**Approach:** Core business logic in the center; HTTP, MCP, and AWS at the edges. New industries = new MCP server, not a core rewrite.

### HLD — system overview

![High-Level Design](docs/images/hld-system-overview.png)

### LLD — sequence flows

| Flow | Diagram |
|------|---------|
| Text chat | ![LLD text analyze](docs/images/lld-text-analyze.png) |
| Voice + Polly | ![LLD voice analyze](docs/images/lld-voice-analyze.png) |
| Conversation memory | ![LLD conversation](docs/images/lld-conversation.png) |

---

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

$env:PYTHONPATH = "src"
$env:LLM_PROVIDER = "local"    # or bedrock + AWS keys in .env
python -m uvicorn agentai.adapters.inbound.api.app:app --host 0.0.0.0 --port 8000
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/ | Web UI (chat + voice) |
| http://localhost:8000/docs | API explorer |

**Sample query:** *Check account ACC-991A for possible fraud*

---

## Project layout

```text
backend/mcp_servers/     Domain MCP plugins (stdio)
src/agentai/core/        Entities, ports, use cases
src/agentai/adapters/    FastAPI, MCP client, Bedrock, Polly
src/agentai/static/      Web UI (index.html)
docs/                    Technical guide (DOCX) + diagrams
tests/
```

---

## Detailed documentation

**For deep dive** (architecture, MCP plug-in guide, API, AWS, demo script, assignment notes):

📄 **[docs/SentryMCP-Technical-Guide.docx](docs/SentryMCP-Technical-Guide.docx)**

Open in Microsoft Word or Google Docs. This is the single detailed reference — the README stays short for recruiters and quick scans.

---

## Key env vars

```env
LLM_PROVIDER=bedrock          # or local
POLLY_ENABLED=true
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
```

---

## Tests

```bash
pytest
```

---

**Package:** `cross-industry-voice-dataguard` v0.1.0
