"""In-process metrics collection with Prometheus exposition."""
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
)

registry = CollectorRegistry()

# ── Request metrics ──────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["status", "guardrail_blocked", "cached"],
    registry=registry,
)

REQUEST_LATENCY = Histogram(
    "llm_request_latency_ms",
    "End-to-end request latency in milliseconds",
    buckets=[50, 100, 250, 500, 1000, 2000, 5000, 10000],
    registry=registry,
)

LLM_LATENCY = Histogram(
    "llm_inference_latency_ms",
    "Azure OpenAI inference latency in milliseconds",
    buckets=[100, 250, 500, 1000, 2000, 5000, 10000, 30000],
    registry=registry,
)

# ── Token & cost metrics ─────────────────────────────────────────────────────
PROMPT_TOKENS = Counter(
    "llm_prompt_tokens_total",
    "Total prompt tokens consumed",
    registry=registry,
)

COMPLETION_TOKENS = Counter(
    "llm_completion_tokens_total",
    "Total completion tokens generated",
    registry=registry,
)

ESTIMATED_COST_USD = Counter(
    "llm_estimated_cost_usd_total",
    "Total estimated cost in USD",
    registry=registry,
)

# ── Guardrail metrics ────────────────────────────────────────────────────────
GUARDRAIL_BLOCKS = Counter(
    "llm_guardrail_blocks_total",
    "Requests blocked by guardrails",
    ["stage", "violation_type"],
    registry=registry,
)

# ── Cache metrics ────────────────────────────────────────────────────────────
CACHE_HITS = Counter(
    "llm_cache_hits_total",
    "Cache hits (requests served from cache)",
    registry=registry,
)

CACHE_MISSES = Counter(
    "llm_cache_misses_total",
    "Cache misses",
    registry=registry,
)

# ── Evaluation metrics ───────────────────────────────────────────────────────
EVAL_SCORE = Summary(
    "llm_eval_score",
    "LLM response quality evaluation scores",
    ["metric"],
    registry=registry,
)

# ── Active connections ────────────────────────────────────────────────────────
ACTIVE_REQUESTS = Gauge(
    "llm_active_requests",
    "Currently active LLM requests",
    registry=registry,
)


def record_request(
    *,
    status: str,
    latency_ms: float,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    guardrail_blocked: bool,
    cached: bool,
):
    REQUEST_COUNT.labels(
        status=status,
        guardrail_blocked=str(guardrail_blocked).lower(),
        cached=str(cached).lower(),
    ).inc()
    REQUEST_LATENCY.observe(latency_ms)
    PROMPT_TOKENS.inc(prompt_tokens)
    COMPLETION_TOKENS.inc(completion_tokens)
    ESTIMATED_COST_USD.inc(cost_usd)


def record_guardrail_block(stage: str, violation_type: str):
    GUARDRAIL_BLOCKS.labels(stage=stage, violation_type=violation_type).inc()


def record_eval_scores(coherence: float, relevance: float, fluency: float):
    EVAL_SCORE.labels(metric="coherence").observe(coherence)
    EVAL_SCORE.labels(metric="relevance").observe(relevance)
    EVAL_SCORE.labels(metric="fluency").observe(fluency)


def get_metrics_output() -> tuple[bytes, str]:
    return generate_latest(registry), CONTENT_TYPE_LATEST
