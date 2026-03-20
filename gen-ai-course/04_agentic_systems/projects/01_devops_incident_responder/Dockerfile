# ============================================================================
# Stage 1: Builder
# Install dependencies into a virtual environment so we can copy just the
# venv into the final image (reduces final image size by ~40%).
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools needed for some Python packages (faiss-cpu, numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer cache:
# If requirements.txt hasn't changed, this layer is cached and pip install
# is skipped on subsequent builds.
COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ============================================================================
# Stage 2: Final runtime image
# ============================================================================
FROM python:3.12-slim AS runtime

# Security: Run as non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY --chown=appuser:appgroup agent/    ./agent/
COPY --chown=appuser:appgroup api/      ./api/
COPY --chown=appuser:appgroup ui/       ./ui/
COPY --chown=appuser:appgroup data/     ./data/
COPY --chown=appuser:appgroup core_logic.py ./
COPY --chown=appuser:appgroup .env.example ./

# Create directories for runtime-generated data
RUN mkdir -p ./data/incident_history && \
    chown -R appuser:appgroup ./data/

# Create __init__.py files so subdirectories are treated as packages
RUN touch agent/__init__.py api/__init__.py ui/__init__.py

USER appuser

# Default: run the FastAPI server
# Override CMD in docker-compose.yml to run Streamlit or the demo script
EXPOSE 8000
EXPOSE 8501

CMD ["uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ============================================================================
# Build and run:
#   docker build -t devops-incident-responder .
#   docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 devops-incident-responder
#
# Run the Streamlit UI:
#   docker run -e OPENAI_API_KEY=sk-... -p 8501:8501 devops-incident-responder \
#     streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
#
# Run the demo script:
#   docker run -e OPENAI_API_KEY=sk-... devops-incident-responder python core_logic.py
# ============================================================================
