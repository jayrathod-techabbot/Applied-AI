# =============================================================================
# Multi-Agent Customer Support System — Dockerfile
# Multi-stage build for Python 3.12 slim
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — install Python dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies needed for some Python packages
# (faiss-cpu and scikit-learn need these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching.
# If requirements.txt doesn't change, this layer is cached.
COPY requirements.txt .

# Install all dependencies into a virtual environment inside /build/venv
RUN python -m venv /build/venv && \
    /build/venv/bin/pip install --upgrade pip && \
    /build/venv/bin/pip install -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2: Runtime — lean production image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Put the venv on PATH so python/pip resolve to it
    PATH="/app/venv/bin:$PATH" \
    # Application defaults (overridden by docker-compose / env file)
    KB_DIR=/app/data/knowledge_base \
    CONFIDENCE_THRESHOLD=0.6 \
    MAX_HISTORY_MESSAGES=20

# Install only runtime system libraries (libgomp1 needed by faiss-cpu)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /build/venv /app/venv

# Copy the application source
COPY --chown=appuser:appgroup . .

# Create necessary directories with correct permissions
RUN mkdir -p /app/data/knowledge_base && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check — polls the /health endpoint every 30 seconds
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run the FastAPI server
# The --host 0.0.0.0 ensures the container listens on all interfaces.
# Use docker-compose to override CMD for the Streamlit service.
CMD ["uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
