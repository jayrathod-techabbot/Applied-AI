# Module 9: Monitoring & Observability — Core Concepts

## Table of Contents
- [9.1 Observability Fundamentals for LLM Systems](#91-observability-fundamentals-for-llm-systems)
- [9.2 Drift Detection and Model Performance Tracking](#92-drift-detection-and-model-performance-tracking)
- [9.3 Logging Strategies and Distributed Tracing](#93-logging-strategies-and-distributed-tracing)

---

## 9.1 Observability Fundamentals for LLM Systems

### The Three Pillars of Observability

Observability in LLM systems extends the classic three-pillar model to address unique challenges of generative AI.

| Pillar | Purpose | LLM-Specific Considerations |
|--------|---------|----------------------------|
| **Logs** | Detailed event records | Prompt/response pairs, token-level decisions, tool calls |
| **Metrics** | Quantitative measurements | Token usage, latency percentiles, quality scores, cost |
| **Traces** | Request lifecycle tracking | Multi-step chains, agent reasoning loops, RAG retrieval spans |

### Why LLM Observability Differs from Traditional ML

Traditional ML models produce deterministic, structured outputs. LLM systems generate free-form text, make autonomous tool calls, and chain multiple reasoning steps — making failures harder to detect and debug.

```
Traditional ML Pipeline:
  Input → Model → Prediction → Metric

LLM System:
  Input → Prompt Engineering → LLM Call → Tool Use → Retrieval → LLM Call → Output
           ↓                   ↓           ↓           ↓           ↓
         Metrics             Metrics     Traces      Metrics     Metrics
```

### LLM-Specific Metrics

#### Operational Metrics

| Metric | Description | Target Range | Alert Threshold |
|--------|-------------|-------------|-----------------|
| **Latency (p50)** | Median response time | < 1s | > 2s |
| **Latency (p99)** | Tail response time | < 5s | > 15s |
| **Token Usage (input)** | Tokens per request | Varies | Spike detection |
| **Token Usage (output)** | Tokens generated | Varies | Spike detection |
| **Cost per Request** | USD per inference | Model-dependent | > 2x baseline |
| **Throughput** | Requests per second | Capacity-dependent | < SLA minimum |
| **Error Rate** | Failed requests / total | < 0.1% | > 1% |
| **Timeout Rate** | Timed-out requests | < 0.5% | > 2% |

#### Quality Metrics

| Metric | Description | Measurement Method |
|--------|-------------|-------------------|
| **Hallucination Rate** | Factual inaccuracies | LLM-as-judge, human eval, RAG faithfulness |
| **Relevance Score** | Response relevance to query | Embedding similarity, LLM scoring |
| **Coherence Score** | Logical consistency | LLM-as-judge evaluation |
| **Toxicity Score** | Harmful content detection | Perspective API, custom classifiers |
| **User Satisfaction** | Thumbs up/down, CSAT | Explicit feedback collection |
| **Task Completion Rate** | Successful end-to-end flows | Outcome tracking |

### Setting Up a Basic Monitoring Stack

```python
import time
from dataclasses import dataclass, field
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider

# --- Metric instruments ---
meter = metrics.get_meter("llm.service")

latency_histogram = meter.create_histogram(
    name="llm.request.duration",
    unit="ms",
    description="LLM request latency in milliseconds",
)

token_counter = meter.create_counter(
    name="llm.tokens.total",
    unit="tokens",
    description="Total tokens consumed",
)

cost_counter = meter.create_counter(
    name="llm.cost.total",
    unit="USD",
    description="Cumulative cost in USD",
)

request_counter = meter.create_counter(
    name="llm.requests.total",
    unit="requests",
    description="Total LLM requests",
)

error_counter = meter.create_counter(
    name="llm.errors.total",
    unit="errors",
    description="Total LLM errors",
)


@dataclass
class LLMCallRecord:
    model: str
    start_time: float = 0.0
    end_time: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    status: str = "success"
    error_type: Optional[str] = None
    prompt_hash: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def latency_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000


class LLMMonitor:
    """Central monitoring class for LLM operations."""

    # Cost per 1K tokens (input, output) — update with actual pricing
    PRICING = {
        "gpt-4o": (0.0025, 0.01),
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-4-turbo": (0.01, 0.03),
        "claude-3-opus": (0.015, 0.075),
        "claude-3-sonnet": (0.003, 0.015),
    }

    def __init__(self, service_name: str = "llm-service"):
        self.service_name = service_name
        self.tracer = trace.get_tracer(service_name)
        self._records: list[LLMCallRecord] = []

    def estimate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost based on token counts and model pricing."""
        input_price, output_price = self.PRICING.get(model, (0.01, 0.03))
        return (input_tokens * input_price + output_tokens * output_price) / 1000

    def record_call(self, record: LLMCallRecord) -> None:
        """Record an LLM call and emit metrics."""
        record.cost_usd = self.estimate_cost(
            record.model, record.input_tokens, record.output_tokens
        )

        labels = {
            "model": record.model,
            "status": record.status,
            "service": self.service_name,
        }

        latency_histogram.record(record.latency_ms, labels)
        token_counter.add(record.input_tokens, {**labels, "token_type": "input"})
        token_counter.add(record.output_tokens, {**labels, "token_type": "output"})
        cost_counter.add(record.cost_usd, labels)
        request_counter.add(1, labels)

        if record.status == "error":
            error_counter.add(1, {**labels, "error_type": record.error_type or "unknown"})

        self._records.append(record)

    def get_summary(self, window_seconds: int = 3600) -> dict:
        """Get a summary of recent calls within the time window."""
        cutoff = time.time() - window_seconds
        recent = [r for r in self._records if r.start_time >= cutoff]

        if not recent:
            return {"total_requests": 0}

        latencies = sorted(r.latency_ms for r in recent)
        errors = [r for r in recent if r.status == "error"]

        return {
            "total_requests": len(recent),
            "error_count": len(errors),
            "error_rate": len(errors) / len(recent),
            "latency_p50": latencies[len(latencies) // 2],
            "latency_p99": latencies[int(len(latencies) * 0.99)],
            "total_tokens": sum(r.total_tokens for r in recent),
            "total_cost_usd": sum(r.cost_usd for r in recent),
            "avg_tokens_per_request": sum(r.total_tokens for r in recent) / len(recent),
        }
```

### Alerting Rules

Alerting catches anomalies before they become incidents. Define alerts based on SLOs.

```yaml
# prometheus/alert-rules.yml
groups:
  - name: llm_service_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          rate(llm_errors_total[5m]) / rate(llm_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "LLM error rate exceeds 1%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighLatencyP99
        expr: |
          histogram_quantile(0.99, rate(llm_request_duration_bucket[5m])) > 15000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p99 latency exceeds 15 seconds"

      - alert: CostSpike
        expr: |
          rate(llm_cost_total[1h]) > 2 * rate(llm_cost_total[1h] offset 24h)
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Hourly cost is 2x higher than yesterday"

      - alert: TokenUsageAnomaly
        expr: |
          rate(llm_tokens_total[5m]) > 3 * avg_over_time(rate(llm_tokens_total[5m])[1h:5m])
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Token usage spike detected — possible prompt injection or loop"
```

### Dashboard Design (Grafana)

A well-designed LLM monitoring dashboard includes these panels:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Service Overview                         │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  Request Rate│  Error Rate  │  Avg Latency │  Hourly Cost (USD) │
│  ▓▓▓▓▓▓▓▓▓▓  │   0.12%      │   1.2s       │  $12.45            │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│  Latency Distribution (Histogram)                               │
│  p50: 0.8s  p90: 2.1s  p95: 3.5s  p99: 8.2s                   │
├─────────────────────────────────────────────────────────────────┤
│  Token Usage by Model                                           │
│  gpt-4o: ████████████ 1.2M  │  claude-3: ████████ 0.8M         │
├─────────────────────────────────────────────────────────────────┤
│  Cost Breakdown (Last 24h)         │  Quality Scores            │
│  Input tokens:  $4.20              │  Relevance:  0.92          │
│  Output tokens: $8.25              │  Coherence:  0.95          │
│  Total:         $12.45             │  Hallucination: 0.03       │
├────────────────────────────────────┴────────────────────────────┤
│  Error Breakdown by Type                                        │
│  Timeout: 45% │ Rate Limit: 30% │ Invalid Input: 15% │ Other: 10% │
└─────────────────────────────────────────────────────────────────┘
```

### LangSmith Integration

LangSmith provides built-in tracing and evaluation for LangChain applications.

```python
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer

# Enable tracing via environment variables
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your-key
# LANGCHAIN_PROJECT=my-llm-project

# Programmatic access to traces
client = Client()

# Fetch recent runs
runs = client.list_runs(
    project_name="my-llm-project",
    filter='eq(is_root, true)',
    limit=50,
)

# Run evaluation on logged traces
from langsmith.evaluators import LangChainStringEvaluator

evaluator = LangChainStringEvaluator(
    "criteria",
    config={
        "criteria": {
            "helpfulness": "Is the response helpful to the user?",
            "accuracy": "Is the response factually accurate?",
        }
    },
)

# Batch evaluation
results = client.evaluate(
    "my-llm-project",
    evaluators=[evaluator],
    max_concurrency=4,
)
```

### Langfuse Integration

Langfuse is an open-source alternative with strong cost tracking and prompt management.

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="https://cloud.langfuse.com",  # or self-hosted
)

# Trace a full request
trace = langfuse.trace(
    name="rag-query",
    user_id="user-123",
    metadata={"version": "v2.1"},
)

# Add spans for sub-operations
retrieval_span = trace.span(
    name="retrieval",
    input={"query": "What is RAG?"},
)

# ... perform retrieval ...

retrieval_span.end(
    output={"documents": ["doc1", "doc2"], "scores": [0.95, 0.87]},
)

# LLM generation span
generation = trace.generation(
    name="answer-generation",
    model="gpt-4o",
    model_parameters={"temperature": 0.7},
    input=[{"role": "user", "content": "..."}],
    output="RAG stands for...",
    usage={"input": 250, "output": 120, "total": 370},
)

langfuse.flush()
```

---

## 9.2 Drift Detection and Model Performance Tracking

### Types of Drift in LLM Systems

Drift in LLM systems manifests in several forms, each requiring different detection strategies.

| Drift Type | Description | Example | Detection Method |
|------------|-------------|---------|-----------------|
| **Data Drift** | Input distribution changes | New topics, languages, or formatting | Statistical tests on embeddings |
| **Concept Drift** | Relationship between input and output changes | User expectations evolve | Metric trend analysis |
| **Embedding Drift** | Semantic distribution of inputs shifts | New domain vocabulary | Cosine distance on embedding centroids |
| **Prompt Drift** | Effective prompt strategies degrade | Template stops working | A/B testing, quality score trends |
| **Model Drift** | Underlying model behavior changes | Provider silently updates model | Output distribution comparison |

### Data Drift Detection

```python
import numpy as np
from scipy import stats
from sklearn.metrics.pairwise import cosine_distances


class EmbeddingDriftDetector:
    """Detect drift in LLM input embeddings using statistical tests."""

    def __init__(self, reference_embeddings: np.ndarray, window_size: int = 100):
        """
        Args:
            reference_embeddings: Embeddings from training/calibration period
            window_size: Sliding window for current distribution
        """
        self.reference_embeddings = reference_embeddings
        self.window_size = window_size
        self.current_window: list[np.ndarray] = []
        self.drift_scores: list[float] = []

    def add_embedding(self, embedding: np.ndarray) -> dict:
        """Add a new embedding and check for drift."""
        self.current_window.append(embedding)

        if len(self.current_window) < self.window_size:
            return {"drift_detected": False, "window_fill": len(self.current_window) / self.window_size}

        current_batch = np.array(self.current_window[-self.window_size:])

        # 1. Maximum Mean Discrepancy (MMD)
        mmd_score = self._compute_mmd(self.reference_embeddings, current_batch)

        # 2. Population Stability Index (PSI) on first principal component
        psi_score = self._compute_psi(self.reference_embeddings, current_batch)

        # 3. Cosine distance between centroids
        ref_centroid = self.reference_embeddings.mean(axis=0)
        curr_centroid = current_batch.mean(axis=0)
        centroid_distance = cosine_distances(
            ref_centroid.reshape(1, -1), curr_centroid.reshape(1, -1)
        )[0, 0]

        result = {
            "drift_detected": mmd_score > 0.1 or psi_score > 0.25,
            "mmd_score": round(mmd_score, 4),
            "psi_score": round(psi_score, 4),
            "centroid_distance": round(centroid_distance, 4),
            "window_size": self.window_size,
        }

        self.drift_scores.append(mmd_score)
        return result

    def _compute_mmd(self, X: np.ndarray, Y: np.ndarray, kernel: str = "rbf") -> float:
        """Maximum Mean Discrepancy between two distributions."""
        gamma = 1.0 / X.shape[1]  # feature-based gamma
        XX = self._rbf_kernel(X, X, gamma)
        YY = self._rbf_kernel(Y, Y, gamma)
        XY = self._rbf_kernel(X, Y, gamma)
        return float(np.mean(XX) + np.mean(YY) - 2 * np.mean(XY))

    def _rbf_kernel(self, X: np.ndarray, Y: np.ndarray, gamma: float) -> np.ndarray:
        sq_dist = np.sum(X ** 2, axis=1).reshape(-1, 1) + \
                  np.sum(Y ** 2, axis=1) - 2 * X @ Y.T
        return np.exp(-gamma * sq_dist)

    def _compute_psi(self, reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Population Stability Index."""
        # Use first principal component for PSI
        ref_pc = reference[:, 0]
        curr_pc = current[:, 0]

        quantiles = np.linspace(0, 100, bins + 1)
        bin_edges = np.percentile(ref_pc, quantiles)
        bin_edges[0], bin_edges[-1] = -np.inf, np.inf

        ref_counts = np.histogram(ref_pc, bins=bin_edges)[0] / len(ref_pc) + 1e-6
        curr_counts = np.histogram(curr_pc, bins=bin_edges)[0] / len(curr_pc) + 1e-6

        return float(np.sum((curr_counts - ref_counts) * np.log(curr_counts / ref_counts)))
```

### Concept Drift Detection

```python
import collections
from datetime import datetime


class ConceptDriftDetector:
    """Track quality metrics over time to detect concept drift."""

    def __init__(
        self,
        metric_name: str = "relevance_score",
        window_size: int = 200,
        alert_threshold: float = 0.05,  # 5% drop triggers alert
        min_samples: int = 50,
    ):
        self.metric_name = metric_name
        self.window_size = window_size
        self.alert_threshold = alert_threshold
        self.min_samples = min_samples
        self.history: list[dict] = []  # {timestamp, value, metadata}
        self.baseline_mean: Optional[float] = None
        self.baseline_std: Optional[float] = None

    def set_baseline(self, scores: list[float]) -> None:
        """Establish baseline from calibration data."""
        self.baseline_mean = np.mean(scores)
        self.baseline_std = np.std(scores)

    def record(self, score: float, metadata: dict | None = None) -> dict:
        """Record a new metric value and check for drift."""
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "value": score,
            "metadata": metadata or {},
        })

        if len(self.history) < self.min_samples:
            return {"drift_detected": False, "samples": len(self.history)}

        recent = [h["value"] for h in self.history[-self.window_size:]]
        recent_mean = np.mean(recent)
        recent_std = np.std(recent)

        # Welch's t-test for distribution shift
        if self.baseline_mean is not None and len(recent) >= 2:
            baseline_samples = [self.baseline_mean] * self.min_samples  # approximate
            t_stat, p_value = stats.ttest_ind(
                baseline_samples, recent, equal_var=False
            )
        else:
            t_stat, p_value = 0, 1.0

        # Page-Hinkley test for change point detection
        ph_detected = self._page_hinkley_test(recent)

        # Cohen's d effect size
        if self.baseline_std and self.baseline_std > 0:
            cohens_d = (self.baseline_mean - recent_mean) / self.baseline_std
        else:
            cohens_d = 0

        drift_detected = (
            (self.baseline_mean is not None and
             recent_mean < self.baseline_mean - self.alert_threshold)
            or p_value < 0.01
            or ph_detected
        )

        return {
            "drift_detected": drift_detected,
            "recent_mean": round(recent_mean, 4),
            "baseline_mean": round(self.baseline_mean, 4) if self.baseline_mean else None,
            "drop": round(self.baseline_mean - recent_mean, 4) if self.baseline_mean else None,
            "p_value": round(p_value, 6),
            "cohens_d": round(cohens_d, 4),
            "page_hinkley_detected": ph_detected,
            "samples_analyzed": len(recent),
        }

    def _page_hinkley_test(self, values: list[float], delta: float = 0.005, lam: float = 50) -> bool:
        """Page-Hinkley test for detecting mean changes."""
        n = len(values)
        mean = np.mean(values)
        cumsum = 0
        min_cumsum = float("inf")

        for i, v in enumerate(values):
            cumsum += v - mean - delta
            min_cumsum = min(min_cumsum, cumsum)
            if cumsum - min_cumsum > lam:
                return True
        return False
```

### Performance Tracking Dashboard Data

```python
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class PerformanceWindow:
    start_time: datetime
    end_time: datetime
    request_count: int
    error_count: int
    avg_latency_ms: float
    p99_latency_ms: float
    total_tokens: int
    total_cost: float
    avg_quality_score: float
    hallucination_rate: float


class PerformanceTracker:
    """Aggregate and track LLM performance over time windows."""

    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes
        self.windows: list[PerformanceWindow] = []

    def compute_window(self, records: list[LLMCallRecord]) -> PerformanceWindow:
        """Compute performance metrics for a batch of records."""
        if not records:
            raise ValueError("No records to compute window from")

        latencies = sorted(r.latency_ms for r in records)
        errors = [r for r in records if r.status == "error"]
        quality_scores = [
            r.metadata.get("quality_score", 0)
            for r in records
            if "quality_score" in r.metadata
        ]

        return PerformanceWindow(
            start_time=datetime.fromtimestamp(min(r.start_time for r in records)),
            end_time=datetime.fromtimestamp(max(r.end_time for r in records)),
            request_count=len(records),
            error_count=len(errors),
            avg_latency_ms=np.mean(latencies),
            p99_latency_ms=latencies[int(len(latencies) * 0.99)],
            total_tokens=sum(r.total_tokens for r in records),
            total_cost=sum(r.cost_usd for r in records),
            avg_quality_score=np.mean(quality_scores) if quality_scores else 0.0,
            hallucination_rate=len([
                r for r in records if r.metadata.get("hallucination", False)
            ]) / len(records),
        )

    def detect_anomalies(self, current: PerformanceWindow) -> list[str]:
        """Compare current window against historical trends."""
        alerts = []

        if len(self.windows) < 3:
            return alerts

        historical = self.windows[-10:]  # last 10 windows

        # Check error rate anomaly
        avg_error_rate = np.mean([w.error_count / w.request_count for w in historical])
        current_error_rate = current.error_count / current.request_count
        if current_error_rate > avg_error_rate * 3 and current_error_rate > 0.01:
            alerts.append(f"Error rate spike: {current_error_rate:.2%} vs avg {avg_error_rate:.2%}")

        # Check latency anomaly
        avg_latency = np.mean([w.avg_latency_ms for w in historical])
        if current.avg_latency_ms > avg_latency * 2:
            alerts.append(f"Latency spike: {current.avg_latency_ms:.0f}ms vs avg {avg_latency:.0f}ms")

        # Check quality drop
        avg_quality = np.mean([w.avg_quality_score for w in historical if w.avg_quality_score > 0])
        if avg_quality > 0 and current.avg_quality_score < avg_quality * 0.85:
            alerts.append(f"Quality drop: {current.avg_quality_score:.3f} vs avg {avg_quality:.3f}")

        # Check cost spike
        avg_cost = np.mean([w.total_cost for w in historical])
        if current.total_cost > avg_cost * 3:
            alerts.append(f"Cost spike: ${current.total_cost:.2f} vs avg ${avg_cost:.2f}")

        self.windows.append(current)
        return alerts
```

---

## 9.3 Logging Strategies and Distributed Tracing

### Structured Logging

Structured logging produces machine-parseable log entries that enable efficient querying, aggregation, and alerting.

```python
import json
import logging
import hashlib
from datetime import datetime, timezone
from typing import Any


class PIIFilter(logging.Filter):
    """Redact PII from log records before they leave the application."""

    PII_PATTERNS = {
        "email": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL_REDACTED]"),
        "phone": (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "[PHONE_REDACTED]"),
        "ssn": (r'\b\d{3}-\d{2}-\d{4}\b', "[SSN_REDACTED]"),
        "credit_card": (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "[CC_REDACTED]"),
        "ip_address": (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "[IP_REDACTED]"),
    }

    def filter(self, record: logging.LogRecord) -> bool:
        import re
        if isinstance(record.msg, str):
            for name, (pattern, replacement) in self.PII_PATTERNS.items():
                record.msg = re.sub(pattern, replacement, record.msg)
        return True


class StructuredLLMLogger:
    """Structured JSON logger for LLM operations."""

    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"llm.{service_name}")
        self.logger.setLevel(getattr(logging, log_level))

        # Console handler with JSON formatting
        handler = logging.StreamHandler()
        handler.setFormatter(self._json_formatter)
        self.logger.addHandler(handler)

        # Add PII filter
        self.logger.addFilter(PIIFilter())

    @staticmethod
    def _json_formatter(record: logging.LogRecord) -> str:
        return json.dumps(record.msg) + "\n"

    def log_request(
        self,
        request_id: str,
        model: str,
        prompt_hash: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        status: str,
        trace_id: str | None = None,
        span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a structured LLM request entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "service": self.service_name,
            "event_type": "llm_request",
            "request_id": request_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "model": model,
            "prompt_hash": prompt_hash,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": round(latency_ms, 2),
            "status": status,
            "metadata": metadata or {},
        }
        self.logger.info(entry)

    def log_error(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        model: str,
        trace_id: str | None = None,
        stack_trace: str | None = None,
    ) -> None:
        """Log a structured error entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR",
            "service": self.service_name,
            "event_type": "llm_error",
            "request_id": request_id,
            "trace_id": trace_id,
            "model": model,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
        }
        self.logger.error(entry)

    def log_evaluation(
        self,
        request_id: str,
        evaluation_type: str,
        scores: dict[str, float],
        trace_id: str | None = None,
    ) -> None:
        """Log quality evaluation results."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "service": self.service_name,
            "event_type": "llm_evaluation",
            "request_id": request_id,
            "trace_id": trace_id,
            "evaluation_type": evaluation_type,
            "scores": scores,
        }
        self.logger.info(entry)
```

### PII Handling Strategies

| Strategy | When to Use | Trade-offs |
|----------|-------------|------------|
| **Redaction** | Production logs, third-party services | Lose debugging context |
| **Tokenization** | Internal systems, compliance-heavy | Reversible with token store |
| **Hashing** | Analytics without exposure | One-way, no retrieval |
| **Encryption at rest** | All log storage | Performance overhead |
| **Exclusion** | Highly sensitive fields | No visibility |

```python
class PIIRedactor:
    """Configurable PII redaction for log entries."""

    def __init__(self, strategy: str = "redact"):
        self.strategy = strategy
        self._token_map: dict[str, str] = {}

    def redact_dict(self, data: dict, fields_to_redact: list[str]) -> dict:
        """Redact specified fields from a dictionary."""
        result = {}
        for key, value in data.items():
            if key in fields_to_redact:
                if self.strategy == "redact":
                    result[key] = "[REDACTED]"
                elif self.strategy == "hash":
                    result[key] = hashlib.sha256(str(value).encode()).hexdigest()[:12]
                elif self.strategy == "tokenize":
                    token = f"TOKEN_{len(self._token_map)}"
                    self._token_map[token] = str(value)
                    result[key] = token
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value, fields_to_redact)
            else:
                result[key] = value
        return result

    def redact_prompt(self, prompt: str, max_length: int = 200) -> str:
        """Redact PII from prompt text and truncate for logging."""
        import re
        redacted = re.sub(r'\b\S+@\S+\.\S+\b', '[EMAIL]', prompt)
        redacted = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', redacted)
        redacted = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', redacted)
        if len(redacted) > max_length:
            return redacted[:max_length] + "...[TRUNCATED]"
        return redacted
```

### Distributed Tracing with OpenTelemetry

OpenTelemetry provides vendor-neutral instrumentation for tracing LLM pipelines end-to-end.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import StatusCode
import uuid


class LLMTracer:
    """Distributed tracing for LLM pipelines using OpenTelemetry."""

    def __init__(self, service_name: str = "llm-rag-pipeline", otlp_endpoint: str = "localhost:4317"):
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(service_name)

    def trace_rag_query(self, query: str, top_k: int = 5):
        """Context manager for tracing a full RAG query."""
        return self._RAGSpan(self.tracer, query, top_k)

    class _RAGSpan:
        def __init__(self, tracer, query: str, top_k: int):
            self.tracer = tracer
            self.query = query
            self.top_k = top_k
            self.root_span = None

        def __enter__(self):
            self.root_span = self.tracer.start_span("rag.query")
            self.root_span.set_attribute("rag.query_length", len(self.query))
            self.root_span.set_attribute("rag.top_k", self.top_k)
            self.root_span.set_attribute("request.id", str(uuid.uuid4()))
            return self

        def __exit__(self, *args):
            if self.root_span:
                self.root_span.end()

        def trace_retrieval(self, docs_retrieved: int, avg_score: float):
            """Add retrieval span."""
            with self.tracer.start_span("rag.retrieval", parent=self.root_span) as span:
                span.set_attribute("retrieval.docs_count", docs_retrieved)
                span.set_attribute("retrieval.avg_score", avg_score)
                span.set_status(StatusCode.OK)

        def trace_reranking(self, input_count: int, output_count: int, model: str):
            """Add reranking span."""
            with self.tracer.start_span("rag.reranking", parent=self.root_span) as span:
                span.set_attribute("rerank.input_count", input_count)
                span.set_attribute("rerank.output_count", output_count)
                span.set_attribute("rerank.model", model)

        def trace_generation(
            self,
            model: str,
            input_tokens: int,
            output_tokens: int,
            latency_ms: float,
            cost: float,
        ):
            """Add LLM generation span."""
            with self.tracer.start_span("llm.generation", parent=self.root_span) as span:
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.input_tokens", input_tokens)
                span.set_attribute("llm.output_tokens", output_tokens)
                span.set_attribute("llm.latency_ms", latency_ms)
                span.set_attribute("llm.cost_usd", cost)
                span.set_attribute("llm.total_tokens", input_tokens + output_tokens)
                span.set_status(StatusCode.OK)

        def trace_error(self, error: Exception):
            """Record error on root span."""
            if self.root_span:
                self.root_span.set_status(StatusCode.ERROR, str(error))
                self.root_span.record_exception(error)
```

### Log Aggregation Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  App Server  │    │  App Server  │    │  App Server  │
│  (Structured │    │  (Structured │    │  (Structured │
│   JSON logs) │    │   JSON logs) │    │   JSON logs) │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────┐
│              Log Shipper (Fluentd/Filebeat)          │
│  - Parse JSON                                       │
│  - Add metadata (host, region, version)             │
│  - Route to appropriate index                       │
└───────────────────────┬─────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   ┌────────────┐ ┌──────────┐ ┌───────────┐
   │ Elasticsearch│ │  S3/GCS  │ │  Loki     │
   │ (Hot store) │ │(Archive) │ │(Optional) │
   └─────┬──────┘ └──────────┘ └───────────┘
         │
         ▼
   ┌────────────┐
   │  Grafana   │──── Dashboards, Alerts
   │  Kibana    │──── Search, Analytics
   └────────────┘
```

### Log Retention Policies

| Log Type | Hot Storage | Warm Storage | Cold Archive | Total Retention |
|----------|-------------|-------------|-------------|-----------------|
| **Request/Response** | 7 days | 30 days | 1 year | 1 year |
| **Error Logs** | 30 days | 90 days | 2 years | 2 years |
| **Evaluation Scores** | 30 days | 1 year | 3 years | 3 years |
| **Audit Logs** | 90 days | 1 year | 7 years | 7 years |
| **Debug/Trace** | 3 days | - | - | 3 days |

### Production Monitoring Patterns

#### Pattern 1: Canary Monitoring

Deploy new prompts/models to a small percentage of traffic and compare metrics.

```python
class CanaryMonitor:
    """Compare canary vs baseline performance."""

    def __init__(self, significance_level: float = 0.05):
        self.canary_metrics: list[float] = []
        self.baseline_metrics: list[float] = []
        self.significance_level = significance_level

    def add_canary_sample(self, metric: float):
        self.canary_metrics.append(metric)

    def add_baseline_sample(self, metric: float):
        self.baseline_metrics.append(metric)

    def should_promote(self, min_samples: int = 100) -> dict:
        """Determine if canary should be promoted."""
        if len(self.canary_metrics) < min_samples or len(self.baseline_metrics) < min_samples:
            return {"decision": "insufficient_data", "canary_n": len(self.canary_metrics)}

        t_stat, p_value = stats.ttest_ind(self.canary_metrics, self.baseline_metrics)
        canary_mean = np.mean(self.canary_metrics)
        baseline_mean = np.mean(self.baseline_metrics)

        return {
            "decision": "promote" if p_value > self.significance_level and canary_mean >= baseline_mean * 0.95
            else "reject",
            "canary_mean": canary_mean,
            "baseline_mean": baseline_mean,
            "p_value": p_value,
            "relative_change": (canary_mean - baseline_mean) / baseline_mean,
        }
```

#### Pattern 2: Shadow Mode Evaluation

Run production traffic through a new system alongside the old one without affecting users.

```python
import asyncio
from dataclasses import dataclass


@dataclass
class ShadowResult:
    request_id: str
    production_output: str
    shadow_output: str
    production_latency_ms: float
    shadow_latency_ms: float
    agreement_score: float


class ShadowEvaluator:
    """Run shadow evaluations comparing new vs production models."""

    def __init__(self, production_fn, shadow_fn):
        self.production_fn = production_fn
        self.shadow_fn = shadow_fn
        self.results: list[ShadowResult] = []

    async def evaluate(self, request_id: str, prompt: str) -> str:
        """Run both models, return production output, log comparison."""
        # Run production path (blocking)
        prod_start = time.time()
        prod_output = await self.production_fn(prompt)
        prod_latency = (time.time() - prod_start) * 1000

        # Run shadow path (non-blocking, fire-and-forget)
        asyncio.create_task(
            self._run_shadow(request_id, prompt, prod_output, prod_latency)
        )

        return prod_output

    async def _run_shadow(self, request_id, prompt, prod_output, prod_latency):
        try:
            shadow_start = time.time()
            shadow_output = await self.shadow_fn(prompt)
            shadow_latency = (time.time() - shadow_start) * 1000

            # Compute agreement
            from sklearn.feature_extraction.text import TfidfVectorizer
            vec = TfidfVectorizer()
            tfidf = vec.fit_transform([prod_output, shadow_output])
            agreement = (tfidf[0] @ tfidf[1].T).toarray()[0, 0]

            self.results.append(ShadowResult(
                request_id=request_id,
                production_output=prod_output,
                shadow_output=shadow_output,
                production_latency_ms=prod_latency,
                shadow_latency_ms=shadow_latency,
                agreement_score=float(agreement),
            ))
        except Exception as e:
            logging.error(f"Shadow evaluation failed: {e}")
```

#### Pattern 3: Real-Time Quality Sampling

Evaluate a random subset of requests in real-time using LLM-as-judge.

```python
import random


class QualitySampler:
    """Sample and evaluate LLM outputs in real-time."""

    def __init__(self, sample_rate: float = 0.05, judge_model: str = "gpt-4o-mini"):
        self.sample_rate = sample_rate
        self.judge_model = judge_model
        self.scores: list[dict] = []

    def should_sample(self) -> bool:
        return random.random() < self.sample_rate

    async def evaluate(
        self,
        request_id: str,
        query: str,
        response: str,
        context: str | None = None,
    ) -> dict:
        """Evaluate a single response using LLM-as-judge."""
        judge_prompt = f"""Rate the following LLM response on a scale of 1-5 for each criterion.

Query: {query}
{"Context: " + context if context else ""}
Response: {response}

Rate each criterion (1-5):
1. Relevance: Is the response relevant to the query?
2. Accuracy: Is the response factually accurate?
3. Completeness: Does the response fully address the query?
4. Conciseness: Is the response appropriately concise?

Return JSON: {{"relevance": <int>, "accuracy": <int>, "completeness": <int>, "conciseness": <int>}}"""

        # Call judge model (implementation depends on your LLM client)
        # result = await llm_client.complete(self.judge_model, judge_prompt)
        # scores = json.loads(result)

        scores = {"relevance": 4, "accuracy": 4, "completeness": 3, "conciseness": 4}  # placeholder

        self.scores.append({
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scores": scores,
            "avg_score": sum(scores.values()) / len(scores),
        })

        return scores
```

---

## Key Takeaways

1. **Three pillars extend to LLM**: Logs capture prompt/response pairs, metrics track tokens/cost/quality, traces follow multi-step chains.

2. **LLM-specific metrics are essential**: Beyond latency and error rates, track hallucination rate, token efficiency, cost per request, and quality scores.

3. **Drift detection requires multiple signals**: Monitor embedding distributions, quality metric trends, and input characteristic shifts simultaneously.

4. **Structured logging is non-negotiable**: JSON-formatted logs with request IDs, trace IDs, and model metadata enable efficient debugging and aggregation.

5. **PII handling must be built-in**: Redact, tokenize, or hash sensitive data before logs leave the application boundary.

6. **OpenTelemetry provides vendor-neutral tracing**: Instrument once, export to any backend (Jaeger, Tempo, Datadog, etc.).

7. **Alert on SLOs, not just symptoms**: Define error budgets and alert when burn rates indicate SLO violations are imminent.

8. **Canary and shadow deployments de-risk changes**: Compare new prompts/models against production baselines before full rollout.

9. **Real-time quality sampling catches silent failures**: LLM-as-judge evaluation on a random sample provides continuous quality visibility.

10. **Cost monitoring prevents bill shock**: Track per-model, per-feature, per-customer costs with spike detection and budget alerts.
