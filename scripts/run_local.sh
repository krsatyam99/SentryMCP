#!/usr/bin/env bash

# Local startup helper for the MCP Compliance Agent MVP.

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"
export LLM_PROVIDER="${LLM_PROVIDER:-local}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

"${PYTHON_BIN}" -m uvicorn agentai.adapters.inbound.api.app:app --host 0.0.0.0 --port 8000
