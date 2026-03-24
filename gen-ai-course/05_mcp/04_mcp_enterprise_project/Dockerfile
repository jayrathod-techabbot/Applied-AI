FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY .env.example ./
COPY .env.dev ./
COPY .env.qa ./
COPY .env.prod ./
COPY src ./src

RUN pip install --no-cache-dir uv && \
    uv pip install --system .

EXPOSE 8080

CMD ["python", "-m", "enterprise_mcp.http_app"]
