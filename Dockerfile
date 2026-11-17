# =====================================================================
# NOUS PERSONAL AI ASSISTANT - PRODUCTION DOCKERFILE
# Multi-Architecture Cloud Container (Linux x86_64, ARM64 / Apple Silicon)
# Continuous 24/7 Minute-to-Minute Autonomous Execution
# =====================================================================

FROM python:3.12-slim-bookworm AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000 \
    OLLAMA_BASE_URL=http://ollama:11434 \
    OLLAMA_MODEL=qwen2.5:3b

# Install system dependencies & curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend /app/backend
COPY frontend /app/frontend
COPY desktop /app/desktop

# Create persistent storage directories with proper permissions
RUN mkdir -p /app/data/database /app/data/credentials /app/workspace /app/docs

# Expose default HTTP port
EXPOSE 8000

# Persistent storage volumes for SQLite WAL databases & sandboxed workspace
VOLUME ["/app/data", "/app/workspace"]

# Healthcheck probing live system health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production startup command
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
