# MCP Compliance Agent MVP

A multi-domain compliance auditing platform that accepts natural-language audit requests (text or voice), routes them to industry-specific **MCP (Model Context Protocol)** servers, and returns a structured compliance verdict through an LLM reasoning layer.

**Package name:** `cross-industry-voice-dataguard` (v0.1.0)

---

## Quick Start

Get the demo running in under two minutes — no AWS credentials required.

```bash
# 1. Install
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
pip install -e .

# 2. Run (local mode — no cloud APIs)
$env:PYTHONPATH = "src"         # Windows PowerShell
$env:LLM_PROVIDER = "local"
python -m uvicorn agentai.adapters.inbound.api.app:app --host 0.0.0.0 --port 8000

# On macOS / Linux, use: export PYTHONPATH=src && export LLM_PROVIDER=local && ./scripts/run_local.sh
```

**Open in browser:**

| URL | What you get |
|-----|--------------|
| http://localhost:8000/ | Built-in web UI (chat + voice) |
| http://localhost:8000/docs | Swagger API explorer |

**Try a sample audit:**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d "{\"industry\": \"fintech\", \"query\": \"Check account ACC-991A for possible fraud\"}"
```

For full setup, Bedrock mode, and environment variables, see [Local Setup](#local-setup) and [Running the Application](#running-the-application).

**More documentation:**

| Document | Purpose |
|----------|---------|
| [`docs/project-guide.md`](docs/project-guide.md) | Business context, HLD/LLD, MCP plug-in guide, assignment framing |
| [`docs/architecture.md`](docs/architecture.md) | Layer diagram and design rationale |
| [`docs/linkedin-demo-script.md`](docs/linkedin-demo-script.md) | 90-second LinkedIn demo script |

---

## Table of Contents

0. [Quick Start](#quick-start)
1. [What This Project Does](#what-this-project-does)
2. [How It Works (End-to-End)](#how-it-works-end-to-end)
3. [Architecture & Low-Level Design (LLD)](#architecture--low-level-design-lld)
4. [Design Patterns & Why We Use Them](#design-patterns--why-we-use-them)
5. [Project Structure](#project-structure)
6. [Folder & File Reference](#folder--file-reference)
7. [Domain Plugins (FinTech, Healthcare, HR)](#domain-plugins-fintech-healthcare-hr)
8. [API Endpoints & Response Shape](#api-endpoints--response-shape)
9. [Local Setup](#local-setup)
10. [Running the Application](#running-the-application)
11. [Environment Variables](#environment-variables)
12. [Dependencies](#dependencies)
13. [Testing](#testing)

---

## What This Project Does

This project is a **proof of concept** for a pluggable, cross-industry compliance agent. An operator submits a question such as *"Check account ACC-991A for possible fraud"* or *"Summarize leave policy for an employee."* The system:

1. **Accepts** the request via HTTP (REST API or built-in web UI at `GET /`).
2. **Optionally transcribes** audio input from an S3 URL using Amazon Transcribe.
3. **Routes** the request to the correct domain MCP server based on the selected industry.
4. **Fetches** mock subsystem data (ledger records, patient records, HR policies) through MCP tools.
5. **Reasons** over that data using an LLM (AWS Bedrock, OpenRouter free-model fallback, or local heuristics).
6. **Returns** a structured JSON verdict with confidence score, summary, and optional synthesized speech (Amazon Polly).

The project is designed to be **demo-friendly**: it works fully offline with `LLM_PROVIDER=local`, uses mock data (no real customer or patient records), and can scale toward production patterns (clean architecture, swappable adapters, isolated MCP servers).

### What It Demonstrates

- Python backend with **FastAPI**
- **Clean / hexagonal architecture** — core logic isolated from frameworks and cloud SDKs
- **MCP server/client** integration via stdio subprocesses
- **Multi-domain tool routing** for FinTech, Healthcare, and HR
- **Resilient LLM pipeline** — Bedrock → OpenRouter model pool → local keyword heuristics
- **Multimodal I/O** — text chat, browser voice, S3 audio transcription, Polly TTS
- **Structured JSON** audit responses suitable for demos, portfolios, and API consumers

---

## How It Works (End-to-End)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER                                                             │
│  • Built-in web UI     →  GET /  (src/agentai/static/index.html)         │
│  • Text chat           →  POST /analyze                                   │
│  • Voice interaction   →  POST /voice-analyze                             │
│  • API consumers       →  curl, Postman, FastAPI /docs                    │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  INBOUND ADAPTER — FastAPI (app.py)                                     │
│  Parses JSON body → AuditRequest(industry, query, audio_url?)            │
│  Wires AnalyzeVoiceUseCase with MCP, LLM, and Audio adapters             │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  USE CASE — AnalyzeVoiceUseCase (analyze.py)                            │
│  1. [Optional] Transcribe audio_url via IAudioPort                        │
│  2. Fetch domain data via IMcpClientPort.execute_compliance_audit()       │
│  3. Generate verdict via ILlmPort.generate_agent_reasoning()              │
│  4. [Voice path] Synthesize spoken summary via IAudioPort (Polly)         │
│  5. Return unified JSON response                                          │
└───────────────┬────────────────────────────────────┬─────────────────────┘
                │                                    │
                ▼                                    ▼
┌───────────────────────────────┐    ┌─────────────────────────────────────┐
│  OUTBOUND MCP ADAPTER          │    │  OUTBOUND LLM ADAPTER                │
│  RealMcpClientAdapter          │    │  BedrockAdapter                      │
│  • Industry → server registry  │    │  • local → keyword heuristics        │
│  • Spawn MCP server subprocess │    │  • bedrock → AWS converse API        │
│  • call_tool(name, args)       │    │  • fallback → OpenRouter free pool   │
│  • Return formatted log text   │    │  • final fallback → local heuristics │
└───────────────┬───────────────┘    └─────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  MCP SERVER SUBPROCESS (stdio) — backend/mcp_servers/                    │
│  fintech_server.py    → audit_financial_account(account_id)              │
│  healthcare_server.py → audit_patient_record(patient_id)                 │
│  hr_server.py         → summarize_hr_policy(policy_topic)                  │
│  Each server returns mock domain data as tool output text                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### Text vs Voice Paths

| Endpoint | `force_vocalization` | Polly TTS | Typical Use |
|----------|---------------------|-----------|-------------|
| `POST /analyze` | `false` | Skipped | Fast text chat |
| `POST /voice-analyze` | `true` | Amazon Polly (when `POLLY_ENABLED=true`) | Mic / voice-to-voice |

### Voice-to-Voice Pipeline (Recognition + Polly)

Default voice-to-voice mode — **no S3 bucket required**:

```text
You speak
    → Browser Speech Recognition (Chrome/Edge)
    → POST /voice-analyze { query: "transcribed text" }
    → MCP + Bedrock analysis
    → Amazon Polly synthesizes verdict (POLLY_ENABLED=true)
    → Browser plays Polly MP3 audio
```

Enable Polly in `.env`:

```env
POLLY_ENABLED=true
POLLY_VOICE_ID=Joanna
```

Verify at `GET /audio-config` — expect `"voice_mode": "recognition_polly"`.

---

## Architecture & Low-Level Design (LLD)

This project follows **Clean Architecture** (also called **Hexagonal Architecture** or **Ports & Adapters**). The idea is to keep business rules in the center and push all infrastructure concerns (HTTP, AWS, MCP subprocesses) to the edges.

### Layer Diagram

```text
                    ┌─────────────────────────────────┐
                    │         INBOUND ADAPTERS         │
                    │   FastAPI routes (app.py)        │
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

### Why This Architecture?

| Principle | How We Apply It | Benefit |
|-----------|-----------------|---------|
| **Dependency Inversion** | Use case depends on `IMcpClientPort`, not `RealMcpClientAdapter` | Swap MCP implementation without touching business logic |
| **Separation of Concerns** | FastAPI only parses HTTP; `AnalyzeVoiceUseCase` orchestrates the workflow | Each layer has one job |
| **Testability** | Tests inject `FakeMcpClient` and `FakeLlmClient` | Unit tests run without AWS or MCP subprocesses |
| **Extensibility** | New industry = new MCP server + registry entry | Add domains without rewriting the use case |
| **Framework Independence** | Core has no FastAPI, boto3, or MCP imports | Business rules survive framework upgrades |
| **Demo Resilience** | `LLM_PROVIDER=local` bypasses all cloud APIs | Portfolio demos never fail on quota |

### Dependency Rule

**Dependencies always point inward.** The core layer never imports from adapters. Adapters import from core ports and entities. MCP servers are standalone processes with no dependency on the main package.

---

## Design Patterns & Why We Use Them

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Ports & Adapters** | `core/ports/*` + `adapters/*` | Abstract interfaces at the boundary; concrete implementations swappable |
| **Use Case / Application Service** | `AnalyzeVoiceUseCase` | Single orchestration point for the compliance audit workflow |
| **Dependency Injection** | `app.py` wires adapters into the use case | Production uses real adapters; tests use fakes |
| **Strategy / Provider Chain** | `BedrockAdapter` | Try Bedrock → OpenRouter models → local heuristics in order |
| **Registry / Router** | `RealMcpClientAdapter.server_registry` | Map `industry` string → MCP server script + tool + argument extractor |
| **Facade** | FastAPI `app.py` | Thin HTTP layer hiding adapter wiring complexity |
| **Subprocess Isolation** | MCP stdio client | Each domain server runs as its own process — mirrors real MCP deployments |

---

## Project Structure

```text
mcp/
├── backend/                    # Standalone MCP server processes (outside main package)
│   └── mcp_servers/            # One server per compliance domain
├── docs/                       # Supplementary architecture documentation
├── results/                    # Sample output artifacts for demos
├── scripts/                    # Local development run helpers
├── src/                        # Main Python package root (setuptools package_dir)
│   └── agentai/                # Installed package name
│       ├── config/             # Environment and settings
│       ├── core/               # Domain layer (entities, ports, use cases)
│       ├── adapters/           # Infrastructure (inbound API + outbound integrations)
│       └── static/             # Built-in web UI assets
├── tests/                      # Unit tests
├── setup.py                    # Package metadata and install config
├── requirements.txt            # Pip dependencies
├── pytest.ini                  # Test runner configuration
└── .env                        # Local secrets (not committed; see .gitignore)
```

---

## Folder & File Reference

### Root-Level Files

| File | Purpose |
|------|---------|
| `README.md` | Project documentation (this file) |
| `setup.py` | Setuptools config — package name, version, `find_packages(where="src")`, `install_requires` |
| `requirements.txt` | Pinned runtime and dev dependencies for `pip install` |
| `pytest.ini` | Sets `pythonpath = src` so tests can import `agentai` without installing |
| `.env` | Local environment variables (AWS keys, LLM provider, Polly settings). Loaded automatically via `python-dotenv` |
| `.gitignore` | Excludes `.venv`, `.env`, caches, build artifacts |

---

### `backend/` — MCP Server Processes

MCP servers live **outside** the `agentai` package so they can be spawned as independent child processes. Each server uses `FastMCP` from the `mcp` library and communicates over **stdio**.

| Path | Purpose |
|------|---------|
| `backend/mcp_servers/fintech_server.py` | FinTech MCP server. Exposes `audit_financial_account(account_id)`. Returns mock ledger data (risk scores, transactions, compliance status) from `MOCK_LEDGER` |
| `backend/mcp_servers/healthcare_server.py` | Healthcare MCP server. Exposes `audit_patient_record(patient_id)`. Returns mock patient records (consent, PHI exposure, alerts) from `MOCK_PATIENT_RECORDS` |
| `backend/mcp_servers/hr_server.py` | HR MCP server. Exposes `summarize_hr_policy(policy_topic)`. Returns mock HR policy summaries from `MOCK_POLICIES` (leave, remote work, whistleblower, etc.) |

Each server runs via `python backend/mcp_servers/<server>.py` when invoked by the MCP client adapter.

---

### `src/agentai/` — Main Application Package

#### `src/agentai/config/` — Configuration

| File | Purpose |
|------|---------|
| `settings.py` | Loads `.env` from project root; provides `get_setting(name, default)` helper |
| `__init__.py` | Package marker |

#### `src/agentai/core/` — Domain Layer (Framework-Agnostic)

This is the **heart of the application**. It contains no FastAPI, boto3, or MCP imports.

| Path | Purpose |
|------|---------|
| `core/entities/audit_request.py` | **Domain entity** — `AuditRequest` dataclass with `industry`, `query`, optional `audio_url` |
| `core/ports/mcp_port.py` | **Port** — `IMcpClientPort` abstract interface: `execute_compliance_audit(industry, query) -> str` |
| `core/ports/llm_port.py` | **Port** — `ILlmPort` abstract interface: `generate_agent_reasoning(query, mcp_data) -> dict` |
| `core/ports/audio_port.py` | **Port** — `IAudioPort` abstract interface: `transcribe_audio(uri)` and `synthesize_speech(text)` |
| `core/use_cases/analyze.py` | **Use case** — `AnalyzeVoiceUseCase` orchestrates transcribe → MCP fetch → LLM reasoning → optional Polly TTS → unified JSON response |

#### `src/agentai/adapters/` — Infrastructure Layer

| Path | Purpose |
|------|---------|
| `adapters/inbound/api/app.py` | **FastAPI application** — mounts static files, wires adapters, exposes `POST /analyze`, `POST /voice-analyze`, `GET /` |
| `adapters/outbound/mcp/mcp_client.py` | **MCP client adapter** — implements `IMcpClientPort`. Maintains `server_registry` (industry → script + tool + arg extractor). Spawns MCP subprocess, calls tools via `ClientSession`, extracts IDs from natural language via regex/keyword maps |
| `adapters/outbound/aws/bedrock_adapter.py` | **LLM adapter** — implements `ILlmPort`. Provider chain: local heuristics → AWS Bedrock `converse` → OpenRouter free model pool → local fallback. Returns structured verdict JSON |
| `adapters/outbound/aws/audio_adapter.py` | **Audio adapter** — implements `IAudioPort`. Amazon Transcribe for S3 audio URIs; Amazon Polly for text-to-speech when enabled |

#### `src/agentai/static/` — Built-In Web UI

| File | Purpose |
|------|---------|
| `static/index.html` | **Tailwind-based web workspace** — industry selector, text chat (`/analyze`), browser SpeechRecognition voice input (`/voice-analyze`), verdict display, optional Polly/browser TTS playback. Served at `GET /` |

---

### `docs/` — Documentation

| File | Purpose |
|------|---------|
| `project-guide.md` | Full project guide — business problem, HLD/LLD, MCP plug-in, assignment framing |
| `architecture.md` | Layer diagram and design rationale (LLD supplement) |
| `linkedin-demo-script.md` | 90-second LinkedIn video script and demo checklist |

---

### `scripts/` — Run Helpers

| File | Purpose |
|------|---------|
| `run_local.sh` | Bash startup script. Sets `PYTHONPATH=src`, `LLM_PROVIDER=local` (default), runs uvicorn on port 8000 |

---

### `tests/` — Unit Tests

| File | Purpose |
|------|---------|
| `test_use_case.py` | Tests `AnalyzeVoiceUseCase` with `FakeMcpClient` and `FakeLlmClient`. Asserts `COMPLETED` status and `FLAGGED` verdict without real infrastructure |

---

### `results/` — Demo Artifacts

| File | Purpose |
|------|---------|
| `analysis_result.json` | Sample fintech audit response — useful as a reference for expected output shape |

---

## Domain Plugins (FinTech, Healthcare, HR)

Each industry is a **self-contained MCP plugin**: its own server process, tool, mock dataset, and query-routing logic.

### FinTech (`fintech`)

| Aspect | Detail |
|--------|--------|
| **Server** | `backend/mcp_servers/fintech_server.py` |
| **MCP Tool** | `audit_financial_account(account_id: str)` |
| **Example Query** | `Check account ACC-991A for possible fraud` |
| **Default ID** | `ACC-991A` (Global Logistics Corp — HIGH risk, UNDER_REVIEW) |
| **Routing Logic** | Extracts `ACC-XXXX` pattern from query, or matches account holder name against `MOCK_LEDGER` |
| **Risk Signals** | HIGH risk score, UNDER_REVIEW / SUSPENDED status, flagged offshore transactions |

### Healthcare (`healthcare`, `healthtech`)

| Aspect | Detail |
|--------|--------|
| **Server** | `backend/mcp_servers/healthcare_server.py` |
| **MCP Tool** | `audit_patient_record(patient_id: str)` |
| **Example Query** | `Check patient PAT-204B for compliance risk` |
| **Default ID** | `PAT-204B` (Avery Johnson — EXPIRED consent, POSSIBLE PHI exposure) |
| **Routing Logic** | Extracts `PAT-XXXX` pattern, or matches patient name against `MOCK_PATIENT_RECORDS` |
| **Risk Signals** | REVOKED/EXPIRED consent, HIGH PHI exposure, open compliance alerts |
| **Note** | `healthtech` is an alias that routes to the same healthcare server |

### HR (`hr`)

| Aspect | Detail |
|--------|--------|
| **Server** | `backend/mcp_servers/hr_server.py` |
| **MCP Tool** | `summarize_hr_policy(policy_topic: str)` |
| **Example Query** | `Summarize leave policy for an employee` |
| **Policy Topics** | `leave`, `remote`, `whistleblower`, `insider_trading`, `data_privacy`, `it_security`, `anti_bribery`, `expense_reimbursement`, `social_media`, `satyam_consulting_sla` |
| **Routing Logic** | Keyword map in `mcp_client.py` matches query terms → one or more `policy_topic` arguments |
| **Output** | Policy title, eligibility rules, summary, compliance risk note |

### Domain Summary Table

| Industry | Example Query | MCP Tool |
|----------|---------------|----------|
| `fintech` | `Check account ACC-991A for possible fraud` | `audit_financial_account` |
| `healthcare` | `Check patient PAT-204B for compliance risk` | `audit_patient_record` |
| `hr` | `Summarize leave policy for an employee` | `summarize_hr_policy` |

---

## API Endpoints & Response Shape

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves built-in web UI (`static/index.html`) |
| `GET` | `/docs` | FastAPI Swagger UI |
| `POST` | `/analyze` | Text-based compliance audit (no Polly TTS) |
| `POST` | `/voice-analyze` | Voice path — forces Polly synthesis when enabled |

### Request Body

```json
{
  "industry": "fintech",
  "query": "Check account ACC-991A for possible fraud",
  "audio_url": "s3://your-bucket/path/to/audio.wav"
}
```

Voice input with uploaded microphone audio:

```json
{
  "industry": "fintech",
  "query": "",
  "audio_base64": "<base64-encoded webm or wav>",
  "audio_media_format": "webm"
}
```

- `audio_url` — existing S3 file; Transcribe reads it directly.
- `audio_base64` — raw mic audio; server uploads to S3 then transcribes.
- Either field can supply the spoken query; `query` is optional when transcription succeeds.

### Response Body

```json
{
  "status": "COMPLETED",
  "evaluated_industry": "fintech",
  "original_query": "Check account ACC-991A for possible fraud",
  "subsystem_extracted_logs": "Account Holder: Global Logistics Corp...",
  "audio_transcription": "",
  "speech_audio_base64": "",
  "spoken_summary": "Verdict: FLAGGED. High-risk account requires review.",
  "speech_error": "",
  "bedrock_evaluation": {
    "verdict": "FLAGGED",
    "confidence_score": 0.92,
    "summary": "Account shows HIGH risk with flagged offshore transactions.",
    "provider": "local"
  }
}
```

### Verdict Values

| Verdict | Meaning |
|---------|---------|
| `CLEARED` | Data supports a normal, resolved, or compliant state |
| `FLAGGED` | Explicit risk, violation, anomaly, or unresolved concern |
| `ACTION_REQUIRED` | More information, human review, or follow-up needed |
| `ERROR` | MCP data is a protocol/execution error, not business data |

---

## Local Setup

### Prerequisites

- Python 3.11+
- pip

### Install

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Configure Environment

Create a `.env` file in the project root (see [Environment Variables](#environment-variables) below). The project loads it automatically via `python-dotenv`.

---

## Running the Application

### Option 1: Local Mode (No AWS Required)

Best for demos and development. Uses keyword-based local heuristics instead of cloud LLMs.

```bash
# macOS / Linux
export LLM_PROVIDER=local
./scripts/run_local.sh

# Windows (PowerShell)
$env:PYTHONPATH = "src"
$env:LLM_PROVIDER = "local"
python -m uvicorn agentai.adapters.inbound.api.app:app --host 0.0.0.0 --port 8000
```

Open:

- **Web UI:** http://localhost:8000/
- **API docs:** http://localhost:8000/docs

### Option 2: Bedrock Mode (AWS)

When AWS quota is available:

```bash
export LLM_PROVIDER=bedrock
export BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
export BEDROCK_MAX_TOKENS=120
export BEDROCK_LOCAL_FALLBACK=true
```

The adapter tries Bedrock first. On failure, it falls back to **OpenRouter** free models, then local heuristics if `BEDROCK_LOCAL_FALLBACK=true`.

### Option 3: Built-In Web UI (Primary Frontend)

Start the API (Option 1 or 2), then open http://localhost:8000/. This serves `src/agentai/static/index.html` — the main UI for text chat and voice-to-voice (browser speech recognition + Amazon Polly).

- **Text:** type a query and submit
- **Voice:** click **Start Voice Loop**, speak your audit request, hear the Polly response

Use Chrome or Edge for voice input.

### Sample API Request

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"industry": "fintech", "query": "Check account ACC-991A for possible fraud"}'
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | `bedrock` | `local` (no cloud) or `bedrock` (AWS) |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock, Transcribe, Polly |
| `BEDROCK_MODEL_ID` | `amazon.nova-micro-v1:0` | Bedrock model identifier |
| `BEDROCK_MAX_TOKENS` | `1000` | Max tokens for Bedrock response |
| `BEDROCK_LOCAL_FALLBACK` | `false` | Use local heuristics after cloud failures |
| `OPENROUTER_API_KEY` | — | OpenRouter API key for free-model fallback |
| `AUDIO_S3_BUCKET` | — | S3 bucket for uploaded microphone audio (required for AWS voice input) |
| `AUDIO_S3_PREFIX` | `agentai/uploads` | S3 key prefix for uploaded audio files |
| `TRANSCRIBE_ROLE_ARN` | — | IAM role ARN Transcribe uses to read audio from S3 |
| `TRANSCRIBE_LANGUAGE_CODE` | `en-US` | Transcription language |
| `POLLY_ENABLED` | `false` | Enable Amazon Polly speech synthesis on `/voice-analyze` |
| `POLLY_VOICE_ID` | `Joanna` | Polly voice |
| `POLLY_OUTPUT_FORMAT` | `mp3` | Polly audio format |

### Example `.env`

```env
LLM_PROVIDER=local
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
BEDROCK_MAX_TOKENS=120
BEDROCK_LOCAL_FALLBACK=true
OPENROUTER_API_KEY=your-key-here
AUDIO_S3_BUCKET=your-audio-bucket-name
AUDIO_S3_PREFIX=agentai/uploads
TRANSCRIBE_ROLE_ARN=arn:aws:iam::123456789012:role/TranscribeDataAccessRole
TRANSCRIBE_LANGUAGE_CODE=en-US
POLLY_ENABLED=true
POLLY_VOICE_ID=Joanna
POLLY_OUTPUT_FORMAT=mp3
```

Copy `.env.example` to `.env` and fill in your values.

### AWS IAM for Voice (Transcribe + S3 + Polly)

1. **S3 bucket** — create a bucket and set `AUDIO_S3_BUCKET`.
2. **App IAM user/role** — needs `s3:PutObject` on `arn:aws:s3:::your-bucket/agentai/uploads/*`.
3. **Transcribe IAM role** — set `TRANSCRIBE_ROLE_ARN` to a role that:
   - Trusts `transcribe.amazonaws.com`
   - Has `s3:GetObject` on the same bucket/prefix
4. **Polly** — set `POLLY_ENABLED=true`; your app credentials need `polly:SynthesizeSpeech`.

After restart, verify: `GET http://localhost:8000/audio-config` should show `"transcribe_enabled": true` and `"polly_enabled": true`.

---

## Dependencies

| Package | Role |
|---------|------|
| **fastapi** | HTTP framework — route definitions, request parsing, OpenAPI docs |
| **uvicorn** | ASGI server — runs the FastAPI application |
| **starlette** | FastAPI foundation — static file serving, responses |
| **pydantic** | Data validation (used by FastAPI for request bodies) |
| **mcp** | MCP client (`ClientSession`, stdio) and server (`FastMCP`) |
| **boto3** | AWS SDK — Bedrock Runtime, Transcribe, Polly |
| **httpx** | HTTP client — OpenRouter API calls, Transcribe transcript fetch |
| **python-dotenv** | Loads `.env` configuration files |
| **pytest** | Unit test runner |
| **pytest-asyncio** | Async test support (MCP client uses asyncio) |

---

## Testing

```bash
pytest
```

The test suite uses **fake port implementations** to verify the use case orchestration without AWS credentials or MCP subprocesses:

- `FakeMcpClient` returns mock high-risk ledger text
- `FakeLlmClient` returns a `FLAGGED` verdict
- Asserts `status == "COMPLETED"` and correct industry routing

---

## MVP Scope & Future Extensions

**In scope (this MVP):**

- Multi-domain MCP routing with mock data
- Clean architecture with swappable adapters
- Local demo mode (no cloud dependency)
- Text and voice interaction paths
- Built-in web UI (`index.html`) for text and voice interaction

**Out of scope (intentionally):**

- Production authentication / authorization
- Real customer, patient, or financial data
- CI/CD pipelines and cloud deployment
- Persistent storage or audit logging

**Natural extensions:**

- Additional MCP domain servers (legal, retail, IoT)
- Real database connectors replacing mock data
- AgentCore / CloudFront deployment
- Authentication middleware on FastAPI routes
