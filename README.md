# MCP Compliance Agent MVP

A beginner-friendly but professional proof of concept for a multi-domain compliance agent.

The app accepts a natural-language audit request, routes it to a domain-specific MCP server, and returns a structured compliance verdict through an LLM adapter. It supports a local demo mode so the project works even when cloud LLM free-tier quota is exhausted.

## What It Demonstrates

- Python backend development with FastAPI
- Clean architecture with core ports and outbound adapters
- MCP server/client integration
- Multi-domain tool routing for FinTech, Healthcare, and HR
- Bedrock-compatible LLM adapter with a local demo fallback
- Structured JSON audit responses suitable for demos and portfolio videos

## Demo Domains

| Industry | Example Query | MCP Tool |
| --- | --- | --- |
| `fintech` | `Check account ACC-991A for possible fraud` | `audit_financial_account` |
| `healthcare` | `Check patient PAT-204B for compliance risk` | `audit_patient_record` |
| `hr` | `Summarize leave policy for an employee` | `summarize_hr_policy` |

## Architecture

```text
FastAPI Request
    -> AnalyzeVoiceUseCase
    -> MCP Client
    -> Domain MCP Server
    -> LLM Adapter
    -> JSON Compliance Verdict
```

The core use case depends only on abstract ports. MCP and LLM implementations live in adapters, so the business flow stays simple and testable.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

Create a local `.env` file in the project root to configure AWS and Bedrock settings:

```bash
cp .env .env.local
# then edit .env.local with your credentials and model settings
```

The project loads `.env` automatically via `python-dotenv`.

## Run The Demo

Local mode avoids AWS Bedrock quota issues:

```bash
export LLM_PROVIDER=local
./scripts/run_local.sh
```

Open:

```text
http://localhost:8000/docs
```

Sample request:

```json
{
  "industry": "fintech",
  "query": "Check account ACC-991A for possible fraud"
}
```

Expected response shape:

```json
{
  "status": "COMPLETED",
  "evaluated_industry": "fintech",
  "original_query": "Check account ACC-991A for possible fraud",
  "subsystem_extracted_logs": "Account Holder: Global Logistics Corp...",
  "bedrock_evaluation": {
    "verdict": "FLAGGED",
    "confidence_score": 0.92,
    "summary": "Local demo analysis: retrieved domain data contains compliance-sensitive risk signals requiring review."
  }
}
```

## Bedrock Mode

When AWS quota is available, switch back to Bedrock:

```bash
export LLM_PROVIDER=bedrock
export BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
export BEDROCK_MAX_TOKENS=120
```

The adapter defaults to Amazon Nova Micro because it is suitable for a low-cost POC. If Bedrock throttles, the app now falls back to GROQ using the provided API key. If GROQ is unavailable, it will still use the local reasoning fallback.

## Streamlit Chat + Voice UI

A Streamlit interface is included for both chat and voice-to-voice interactions. The UI uses browser audio recording and plays back synthesized voice when `POLLY_ENABLED=true`.

Run the UI with:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_ui.py
```

Then open the browser page and:

- type chat queries in the text box
- record voice input using the recorder widget
- get an audio response from Polly when enabled

## AWS Audio (Transcribe + Polly)

This demo supports limited AWS audio integration for free-tier usage:

- `audio_url` can point to an S3 URI such as `s3://my-bucket/input.wav`.
- `TRANSCRIBE_ROLE_ARN` is required for Amazon Transcribe to access the S3 object.
- Set `POLLY_ENABLED=true` to return `speech_audio_base64` for the LLM summary.

Example `.env` settings:

```env
TRANSCRIBE_ROLE_ARN=arn:aws:iam::123456789012:role/TranscribeAccessRole
TRANSCRIBE_LANGUAGE_CODE=en-US
POLLY_ENABLED=false
POLLY_VOICE_ID=Joanna
POLLY_OUTPUT_FORMAT=mp3
```

When enabled, the `/analyze` response includes:

- `audio_transcription`: the transcription text
- `speech_audio_base64`: base64-encoded synthesized speech for the summary

For an explicit voice-to-voice flow, use `/voice-analyze` with an `audio_url` field in the request body. The API will transcribe the audio, enrich the Bedrock/MCP prompt with the transcript, and return the spoken summary as base64 audio.

Example voice-to-voice request:

```json
{
  "industry": "fintech",
  "query": "Check account ACC-991A for possible fraud",
  "audio_url": "s3://your-bucket/path/to/audio.wav"
}
```

Example response fields:

- `audio_transcription`: transcribed audio text
- `speech_audio_base64`: synthesized output speech encoded as base64
- `bedrock_evaluation`: structured compliance analysis result

## Project Structure

```text
backend/mcp_servers/        Domain MCP servers
src/agentai/core/           Entities, ports, and use cases
src/agentai/adapters/       FastAPI, MCP, and LLM adapters
tests/                      Focused unit tests
docs/                       Architecture notes
scripts/                    Local run helpers
```
