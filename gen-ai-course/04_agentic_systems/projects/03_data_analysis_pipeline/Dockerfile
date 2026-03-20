# Dockerfile - Multi-stage build for the AI Data Analysis Pipeline API
#
# Stage 1 (builder): installs Python dependencies into a venv.
# Stage 2 (runtime): copies only the venv + source code, without build tools.
#
# WHY multi-stage: separating build and runtime layers removes gcc, pip cache,
# and other build artefacts from the final image, reducing its size by ~300 MB.
#
# WHY non-root user: running as root inside a container grants the process the
# same privileges as root on the host if the container runtime is compromised.
# A non-root user (appuser) limits the blast radius of such an exploit.

# ─── Stage 1: Builder ───────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system packages needed by numpy, scipy, matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer cache means this step is skipped
# on rebuilds when only source code changes (not requirements).
COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ─── Stage 2: Runtime ───────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install only runtime system libraries (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory and copy application source
WORKDIR /app
COPY --chown=appuser:appgroup . .

# Create the output directory and ensure the app user owns it
RUN mkdir -p /app/output && chown -R appuser:appgroup /app/output

# Switch to non-root user
USER appuser

# Add venv to PATH so 'python' and 'uvicorn' resolve correctly
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/app/output

# Expose the FastAPI port
EXPOSE 8000

# Health check — polls the /health endpoint every 30 s
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Default command: launch the FastAPI server
CMD ["uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
