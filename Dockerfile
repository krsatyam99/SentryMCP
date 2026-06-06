# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (layer caching)
COPY requirements.txt setup.py ./
COPY src/ ./src/

# Install dependencies into a prefix for easy copying
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt && \
    pip install --prefix=/install -e .


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN addgroup --system sentrygroup && \
    adduser --system --ingroup sentrygroup sentryuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=sentryuser:sentrygroup src/ ./src/
COPY --chown=sentryuser:sentrygroup backend/ ./backend/

# Switch to non-root user
USER sentryuser

# Expose port
EXPOSE 8000

# Environment defaults (override at runtime)
ENV PYTHONPATH=src \
    LLM_PROVIDER=local \
    POLLY_ENABLED=false \
    AWS_DEFAULT_REGION=us-east-1 \
    BEDROCK_MODEL_ID=amazon.nova-micro-v1:0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start server
CMD ["python", "-m", "uvicorn", "agentai.adapters.inbound.api.app:app", \
     "--host", "0.0.0.0", "--port", "8000"]
