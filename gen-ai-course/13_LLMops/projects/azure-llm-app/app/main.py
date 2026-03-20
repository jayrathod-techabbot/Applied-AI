"""FastAPI application — the main entrypoint."""
import time
import uuid
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.models import (
    ChatRequest, ChatResponse, HealthResponse, Message, MessageRole, MetricsSummary
)
from app.guardrails.input_guard import InputGuardrail
from app.guardrails.output_guard import OutputGuardrail
from app.llm.client import LLMClient
from app.llm.prompts import get_system_prompt, get_prompt_metadata, ACTIVE_PROMPT
from app.monitoring.logger import setup_logging, set_request_context
from app.monitoring import metrics as m
from app.cache.redis_cache import llm_cache
from app.evaluation.evaluator import LLMEvaluator

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# ── Singletons ───────────────────────────────────────────────────────────────
input_guard = InputGuardrail()
output_guard = OutputGuardrail()
llm_client = LLMClient()
evaluator = LLMEvaluator()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup", extra={"version": settings.app_version})
    yield
    logger.info("Application shutdown")
    await llm_cache.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production LLM API with LLMOps best practices on Azure",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Middleware: request tracing ───────────────────────────────────────────────
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    set_request_context(
        request_id=request_id,
        user_id=request.headers.get("X-User-ID", ""),
    )
    start = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Latency-Ms"] = str(round(latency_ms, 2))
    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
        },
    )
    return response


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["observability"])
async def health_check():
    deps = {"azure_openai": "ok", "redis": "unknown"}
    try:
        client = await llm_cache._get_client()
        await client.ping()
        deps["redis"] = "ok"
    except Exception:
        deps["redis"] = "unavailable"
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        dependencies=deps,
    )


@app.get("/metrics", tags=["observability"])
async def prometheus_metrics():
    data, content_type = m.get_metrics_output()
    return Response(content=data, media_type=content_type)


@app.post("/v1/chat", response_model=ChatResponse, tags=["chat"])
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def chat(request: Request, body: ChatRequest):
    request_id = request.state.request_id
    start_time = time.time()
    m.ACTIVE_REQUESTS.inc()

    try:
        set_request_context(
            request_id=request_id,
            session_id=body.session_id or "",
            user_id=body.user_id or "",
        )

        # ── 1. Input Guardrails ───────────────────────────────────────────────
        last_user_message = next(
            (msg.content for msg in reversed(body.messages) if msg.role == MessageRole.user),
            "",
        )
        input_result = input_guard.check(last_user_message)

        if not input_result.passed:
            logger.warning(
                "Input guardrail blocked request",
                extra={"violations": input_result.violations, "request_id": request_id},
            )
            for v in input_result.violations:
                m.record_guardrail_block("input", v.split(":")[0])
            raise HTTPException(
                status_code=400,
                detail={"error": "Request blocked by content policy", "violations": input_result.violations},
            )

        # Apply redaction if PII was found
        messages = list(body.messages)
        if input_result.redacted_content:
            messages[-1] = Message(role=MessageRole.user, content=input_result.redacted_content)

        # ── 2. Build full message list with system prompt ─────────────────────
        system_msg = Message(role=MessageRole.system, content=get_system_prompt(ACTIVE_PROMPT))
        full_messages = [system_msg] + messages

        # ── 3. Cache lookup ───────────────────────────────────────────────────
        max_tokens = body.max_tokens or settings.max_tokens
        temperature = body.temperature if body.temperature is not None else settings.temperature
        openai_messages = [{"role": msg.role.value, "content": msg.content} for msg in full_messages]

        cached_response = await llm_cache.get(openai_messages, max_tokens, temperature)
        cached = False

        if cached_response:
            m.CACHE_HITS.inc()
            cached = True
            response_text = cached_response["text"]
            from app.models import TokenUsage
            token_usage = TokenUsage(**cached_response["token_usage"])
        else:
            m.CACHE_MISSES.inc()

            # ── 4. LLM Call ───────────────────────────────────────────────────
            llm_start = time.time()
            response_text, token_usage = llm_client.chat(
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                request_id=request_id,
            )
            llm_latency = (time.time() - llm_start) * 1000
            m.LLM_LATENCY.observe(llm_latency)

            await llm_cache.set(
                openai_messages, max_tokens, temperature,
                {"text": response_text, "token_usage": token_usage.dict()},
            )

        # ── 5. Output Guardrails ──────────────────────────────────────────────
        output_result = output_guard.check(response_text, original_query=last_user_message)
        final_text = output_result.redacted_content or response_text

        if not output_result.passed:
            logger.warning(
                "Output guardrail violations",
                extra={"violations": output_result.violations, "request_id": request_id},
            )
            for v in output_result.violations:
                m.record_guardrail_block("output", v.split(":")[0])

        # ── 6. Record metrics ─────────────────────────────────────────────────
        total_latency = (time.time() - start_time) * 1000
        m.record_request(
            status="success",
            latency_ms=total_latency,
            prompt_tokens=token_usage.prompt_tokens,
            completion_tokens=token_usage.completion_tokens,
            cost_usd=token_usage.estimated_cost_usd,
            guardrail_blocked=False,
            cached=cached,
        )

        # ── 7. Async evaluation (sampled) ─────────────────────────────────────
        if evaluator.should_evaluate():
            asyncio.create_task(
                asyncio.to_thread(
                    evaluator.evaluate,
                    request_id, last_user_message, final_text,
                )
            )

        prompt_meta = get_prompt_metadata(ACTIVE_PROMPT)
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "total_latency_ms": round(total_latency, 2),
                "cached": cached,
                **prompt_meta,
            },
        )

        return ChatResponse(
            id=request_id,
            session_id=body.session_id,
            message=Message(role=MessageRole.assistant, content=final_text),
            token_usage=token_usage,
            latency_ms=round(total_latency, 2),
            model=settings.azure_openai_deployment,
            guardrail_input=input_result,
            guardrail_output=output_result,
            cached=cached,
        )

    except HTTPException:
        raise
    except Exception as e:
        total_latency = (time.time() - start_time) * 1000
        m.record_request(
            status="error",
            latency_ms=total_latency,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            guardrail_blocked=False,
            cached=False,
        )
        logger.error("Unhandled error", extra={"error": str(e), "request_id": request_id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        m.ACTIVE_REQUESTS.dec()
