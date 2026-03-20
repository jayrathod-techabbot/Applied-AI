"""FastAPI application — AWS LLM App."""
import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.models import ChatRequest, ChatResponse, HealthResponse, Message, TokenUsage
from app.guardrails import check_input, check_output
from app.llm_client import BedrockClient
from app.monitoring import setup_logging, record_request
from app.cache import cache

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

llm = BedrockClient()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup", extra={"version": settings.app_version, "env": settings.environment})
    yield
    await cache.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production LLM API on AWS with LLMOps best practices",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


@app.middleware("http")
async def tracing(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health():
    return HealthResponse(status="ok", version=settings.app_version, environment=settings.environment)


@app.post("/v1/chat", response_model=ChatResponse, tags=["chat"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat(request: Request, body: ChatRequest):
    request_id = request.state.request_id
    start = time.time()

    # ── 1. Input guardrail ────────────────────────────────────────────────────
    last_user_msg = next(m.content for m in reversed(body.messages) if m.role == "user")
    in_result = check_input(last_user_msg)

    if not in_result.passed:
        record_request(0, 0, 0, 0.0, False, True)
        logger.warning("Input blocked", extra={"violations": in_result.violations, "request_id": request_id})
        raise HTTPException(status_code=400, detail={"error": "Blocked by content policy", "violations": in_result.violations})

    # Build message list (apply PII-sanitized content if needed)
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    if in_result.sanitized != last_user_msg:
        messages[-1]["content"] = in_result.sanitized

    # ── 2. Cache lookup ───────────────────────────────────────────────────────
    max_tokens = body.max_tokens or settings.max_tokens
    cached_val = await cache.get(messages, max_tokens)
    cached = False

    if cached_val:
        cached = True
        response_text = cached_val["text"]
        token_usage = TokenUsage(**cached_val["usage"])
    else:
        # ── 3. LLM call ───────────────────────────────────────────────────────
        response_text, token_usage = llm.chat(messages, max_tokens)
        await cache.set(messages, max_tokens, {"text": response_text, "usage": token_usage.dict()})

    # ── 4. Output guardrail ───────────────────────────────────────────────────
    out_result = check_output(response_text)
    final_text = out_result.sanitized or response_text

    # ── 5. Metrics ────────────────────────────────────────────────────────────
    latency_ms = (time.time() - start) * 1000
    record_request(latency_ms, token_usage.input_tokens, token_usage.output_tokens,
                   token_usage.estimated_cost_usd, cached, blocked=False)

    logger.info("Request OK", extra={
        "request_id": request_id,
        "latency_ms": round(latency_ms, 2),
        "cached": cached,
        "input_tokens": token_usage.input_tokens,
        "output_tokens": token_usage.output_tokens,
    })

    return ChatResponse(
        id=request_id,
        message=Message(role="assistant", content=final_text),
        token_usage=token_usage,
        latency_ms=round(latency_ms, 2),
        model=settings.bedrock_model_id,
        guardrail_passed=out_result.passed,
        cached=cached,
    )
