# Module 9: Monitoring & Observability — Interview Questions

## Table of Contents
- [Beginner Level](#beginner-level)
- [Intermediate Level](#intermediate-level)
- [Advanced Level](#advanced-level)

---

## Beginner Level

### Q1: What is observability and why is it important for LLM applications?

**Answer:** Observability is the ability to understand a system's internal state by examining its external outputs. For LLM applications, it is critical because:
- LLMs are non-deterministic, making behavior harder to predict
- Costs scale with usage and can escalate quickly
- Quality can degrade silently as data drifts
- Debugging requires visibility into prompts, retrieval, and generation stages

Without observability, you cannot detect quality degradation, cost overruns, or reliability issues in production.

### Q2: What are the three pillars of observability?

**Answer:**

| Pillar | Description | LLM Example |
|--------|-------------|-------------|
| **Logs** | Discrete event records | API request/response metadata |
| **Metrics** | Aggregated numerical measurements | P95 latency, tokens per minute |
| **Traces** | End-to-end request journey | User query → retrieval → LLM → response |

Together, they provide complementary views: logs explain *what* happened, metrics show *trends*, and traces reveal *how* a request flowed through the system.

### Q3: What is latency in the context of LLM systems and what are the two key measurements?

**Answer:** Latency measures how long an LLM takes to respond. The two key measurements are:
- **Time to First Token (TTFT):** The delay from request to the first streamed token. This is what the user perceives as "thinking time."
- **Total Latency:** The end-to-end time from request to complete response. This determines SLA compliance.

Both matter for user experience — TTFT for perceived responsiveness, total latency for task completion.

### Q4: What is the difference between data drift and concept drift?

**Answer:**
- **Data drift (covariate shift):** The input distribution changes while the relationship to outputs stays the same. Example: users start asking about a new product category.
- **Concept drift:** The relationship between inputs and correct outputs changes. Example: a product's pricing model is updated, so old answers are now wrong.

Data drift means the model sees unfamiliar inputs. Concept drift means the model's learned patterns are outdated.

### Q5: Why is cost monitoring important for LLM applications?

**Answer:** LLM API costs are usage-based (per token), so costs scale directly with traffic. Without monitoring:
- A sudden traffic spike can cause bill shock
- Inefficient prompts waste tokens and money
- Using expensive models for simple tasks inflates costs
- No visibility into cost-per-request makes ROI calculation impossible

Cost monitoring enables budget alerts, model selection optimization, and prompt efficiency improvements.

### Q6: What is structured logging and why is it preferred over unstructured logging?

**Answer:** Structured logging outputs logs as key-value pairs (typically JSON) rather than free-form text. It is preferred because:
- Machine-parseable for automated analysis
- Enables filtering, aggregation, and search by field
- Consistent format across services
- Integrates with log aggregation tools (Elasticsearch, Datadog)

```json
{"request_id": "req_abc123", "model": "gpt-4o", "latency_ms": 1850, "tokens": 384, "status": "success"}
```

### Q7: What is OpenTelemetry?

**Answer:** OpenTelemetry (OTel) is an open-source, vendor-neutral framework for instrumenting applications to generate, collect, and export telemetry data (traces, metrics, logs). It provides:
- Standard APIs for creating spans and traces
- SDKs in multiple languages (Python, Java, Go, etc.)
- Exporters to various backends (Jaeger, Zipkin, Datadog, Grafana)
- Automatic instrumentation for popular frameworks

It is the CNCF standard for observability instrumentation.

### Q8: What is the purpose of alerting thresholds and what are common alert levels?

**Answer:** Alerting thresholds define conditions that trigger notifications to the operations team. Common levels:
- **Critical:** Service down, error rate > 10% — pages on-call engineer
- **Warning:** P95 latency > 5s, budget 80% consumed — notifies team channel
- **Info:** Deployments, traffic changes — logged for awareness

Thresholds should be actionable (not too noisy) and based on SLOs to avoid alert fatigue.

---

## Intermediate Level

### Q9: How would you design a cost tracking system for an LLM application?

**Answer:**

```python
# Per-request cost calculation
COST_RATES = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},  # per 1K tokens
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}

def track_cost(request_id, model, prompt_tokens, completion_tokens):
    rates = COST_RATES[model]
    cost = (prompt_tokens / 1000 * rates["input"]) + (completion_tokens / 1000 * rates["output"])
    # Store in metrics DB
    metrics_client.record("llm_cost", cost, tags={"model": model, "request_id": request_id})
    return cost
```

The system should:
1. Calculate cost per request using model-specific pricing
2. Aggregate costs by model, user, feature, and time window
3. Set budget alerts at daily/monthly thresholds
4. Provide dashboards showing cost trends and breakdowns
5. Attribute costs to business units for chargeback

### Q10: How would you implement drift detection for an LLM application?

**Answer:** A comprehensive drift detection system monitors multiple signals:

1. **Input distribution drift:** Embed recent query embeddings, compare to reference distribution using KS test or PSI
2. **Output distribution drift:** Track response length, token usage, and vocabulary changes
3. **Quality drift:** Run automated evaluation (LLM-as-judge) on a sample, track scores over a sliding window
4. **Retrieval drift:** Monitor vector search relevance scores (cosine similarity) against thresholds

```python
class DriftDetector:
    def check_all(self, reference_data, current_data):
        results = {}
        results["input_psi"] = self.psi(reference_data["embeddings"], current_data["embeddings"])
        results["quality_trend"] = self.trend_analysis(current_data["quality_scores"])
        results["retrieval_drift"] = self.ks_test(reference_data["retrieval_scores"], current_data["retrieval_scores"])
        results["alert"] = any([
            results["input_psi"] > 0.2,
            results["quality_trend"]["degradation"] > 0.15,
            results["retrieval_drift"]["p_value"] < 0.05,
        ])
        return results
```

### Q11: How would you set up distributed tracing for a RAG pipeline?

**Answer:** Instrument each stage as a span within a single trace:

```python
from opentelemetry import trace

tracer = trace.get_tracer("rag-pipeline")

def rag_query(question: str) -> str:
    with tracer.start_as_current_span("rag_request") as root:
        root.set_attribute("user.question_length", len(question))

        with tracer.start_as_current_span("query_embedding"):
            embedding = embed_model.encode(question)
            current_span.set_attribute("embedding.dimensions", len(embedding))

        with tracer.start_as_current_span("vector_search") as search_span:
            results = vector_db.search(embedding, top_k=5)
            search_span.set_attribute("results.count", len(results))
            search_span.set_attribute("results.max_score", max(r.score for r in results))

        with tracer.start_as_current_span("reranking"):
            reranked = reranker.rerank(question, results)

        with tracer.start_as_current_span("llm_generation") as llm_span:
            llm_span.set_attribute("model", "gpt-4o")
            response = llm_client.generate(prompt=build_prompt(question, reranked))
            llm_span.set_attribute("tokens.input", response.usage.prompt_tokens)
            llm_span.set_attribute("tokens.output", response.usage.completion_tokens)

        return response.content
```

This provides a waterfall view showing exactly where time is spent and which stage might be causing issues.

### Q12: What is the difference between LangSmith and Langfuse for LLM observability?

**Answer:**

| Aspect | LangSmith | Langfuse |
|--------|-----------|----------|
| **Integration** | Deep LangChain integration, auto-tracing | Framework-agnostic, manual + auto instrumentation |
| **Tracing** | Native LangChain chains/agents | OpenTelemetry-based, any framework |
| **Self-hosting** | Cloud only | Self-hosted option available |
| **Evaluation** | Built-in LLM-as-judge evaluators | Custom scoring functions, human annotation |
| **Cost Tracking** | Automatic model pricing | Custom pricing rules |
| **Best For** | LangChain-heavy applications | Any LLM stack, full data control |

Choose LangSmith if you're deeply invested in LangChain. Choose Langfuse for framework flexibility or self-hosting requirements.

### Q13: How do you monitor LLM response quality in production without human evaluation at scale?

**Answer:** Combine multiple automated approaches:

1. **LLM-as-judge:** Sample 5-10% of responses, evaluate with a stronger LLM on relevance, faithfulness, coherence
2. **User feedback signals:** Thumbs up/down, chat rephrasing (user re-asks the same question), session abandonment
3. **Rule-based checks:** Response length anomalies, presence of refusal patterns, format validation
4. **Retrieval quality:** Track if retrieved context was relevant (cosine similarity > threshold)
5. **Regression testing:** Run a fixed test set through the pipeline daily, compare scores

Aggregate these signals into a composite quality score and track its trend over time.

### Q14: What should a production LLM monitoring dashboard include?

**Answer:** A production dashboard should cover five areas:

1. **Traffic:** Requests/min, concurrent users, geographic distribution
2. **Performance:** Latency percentiles (P50/P95/P99), TTFT, throughput
3. **Reliability:** Error rate, error types breakdown, timeout rate
4. **Cost:** Cost per request, cumulative daily spend, cost by model
5. **Quality:** Automated quality scores, user CSAT, hallucination rate, drift indicators

Each area should show current values, trends (hour-over-hour, day-over-day), and anomaly indicators.

### Q15: How would you handle a situation where drift detection triggers but quality scores haven't dropped yet?

**Answer:** This is a common scenario — drift is a *leading indicator* while quality degradation is a *lagging indicator*. The response should be:

1. **Investigate:** Analyze what changed — new topics? New user segments? Seasonal variation?
2. **Assess risk:** Is the drifted data in a critical domain? How much traffic does it represent?
3. **Monitor closely:** Increase evaluation sampling rate for the drifted segment
4. **Prepare:** Update the knowledge base or prepare a retraining pipeline
5. **Decide:** If the drift represents a permanent shift (>20% of traffic), schedule retraining. If temporary, add to watchlist.

Do not wait for quality to degrade before acting — proactive response prevents user-facing issues.

---

## Advanced Level

### Q16: Design an end-to-end observability platform for a multi-model LLM application.

**Answer:** The architecture should handle multiple models, services, and environments:

```
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Chat API │  │ RAG Svc  │  │ Agent Svc│  │ Batch    │     │
│  │ + OTel   │  │ + OTel   │  │ + OTel   │  │ + OTel   │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │              │              │              │           │
├───────┼──────────────┼──────────────┼──────────────┼──────────┤
│       ▼              ▼              ▼              ▼           │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              COLLECTOR TIER (OpenTelemetry)              │  │
│  │  Receives → Processes → Routes telemetry data           │  │
│  └──────┬──────────────┬──────────────┬────────────────────┘  │
│         │              │              │                        │
├─────────┼──────────────┼──────────────┼────────────────────────┤
│         ▼              ▼              ▼                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐      │
│  │  Traces    │  │  Metrics   │  │  Logs              │      │
│  │  (Jaeger/  │  │ (Prometheus│  │  (Elasticsearch/   │      │
│  │  Tempo)    │  │  /Datadog) │  │  Loki)             │      │
│  └─────┬──────┘  └─────┬──────┘  └──────┬─────────────┘      │
│        │               │                │                      │
├────────┼───────────────┼────────────────┼──────────────────────┤
│        ▼               ▼                ▼                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              UNIFIED DASHBOARD (Grafana)                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │  │
│  │  │ Traffic  │ │ Latency  │ │  Cost    │ │ Quality  │    │  │
│  │  │ & Errors │ │ & P95    │ │ Tracking │ │ & Drift  │    │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              ALERTING (PagerDuty / Slack)                │  │
│  │  Critical → Page  │  Warning → Channel  │  Info → Log   │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

Key design decisions:
- Use OTel Collector as the central routing point (vendor-neutral)
- Separate backends for traces, metrics, and logs (each optimized for its query pattern)
- Unified dashboard layer correlates signals across pillars
- Alerting rules combine multiple signals to reduce noise

### Q17: How would you implement canary analysis for LLM model deployments?

**Answer:** Canary analysis compares a new model version against the current production model on real traffic:

1. **Traffic splitting:** Route 5-10% of traffic to the canary model
2. **Shadow comparison:** For the same requests, call both models and compare outputs
3. **Metric comparison:** Track latency, cost, quality scores, and error rate for both
4. **Automated decision:** Promote canary if all metrics are within tolerance; rollback if degradation detected

```python
class CanaryAnalyzer:
    def __init__(self, tolerance: dict):
        self.tolerance = tolerance  # e.g., {"latency_p95_ms": 1.2, "quality_min": 0.95}

    def analyze(self, baseline_metrics: dict, canary_metrics: dict) -> str:
        checks = {
            "latency": canary_metrics["p95_latency"] <= baseline_metrics["p95_latency"] * self.tolerance["latency_p95_ms"],
            "quality": canary_metrics["avg_quality"] >= baseline_metrics["avg_quality"] * self.tolerance["quality_min"],
            "errors": canary_metrics["error_rate"] <= baseline_metrics["error_rate"] * 1.5,
            "cost": canary_metrics["avg_cost"] <= baseline_metrics["avg_cost"] * self.tolerance.get("cost_max", 1.3),
        }
        if all(checks.values()):
            return "promote"
        elif any(checks.get(k) is False for k in ["latency", "errors"]):
            return "rollback"
        else:
            return "extend_canary"  # Run longer to gather more data
```

### Q18: How would you detect and handle prompt injection attacks through monitoring?

**Answer:** Monitoring can detect prompt injection through several signals:

1. **Anomalous input patterns:** Unusually long inputs, embedded instructions, role-switching language
2. **Output deviation:** Responses that suddenly deviate from expected behavior or system prompt
3. **Token usage spikes:** Sudden increase in output tokens (model following injected instructions)
4. **Behavioral anomalies:** Model accessing tools it shouldn't, returning unexpected formats

```python
class PromptInjectionDetector:
    INJECTION_PATTERNS = [
        r"ignore (all |previous |above )?instructions",
        r"you are now",
        r"system prompt:",
        r"act as if",
        r"new role:",
    ]

    def detect(self, prompt: str, response: str, baseline_tokens: int) -> dict:
        import re

        # Pattern matching on input
        pattern_matches = [p for p in self.INJECTION_PATTERNS if re.search(p, prompt.lower())]

        # Token anomaly detection
        token_ratio = count_tokens(response) / max(baseline_tokens, 1)

        # System prompt leakage detection
        system_prompt_leak = any(phrase in response.lower() for phrase in ["my instructions are", "i was told to"])

        risk_score = (
            len(pattern_matches) * 0.4 +
            (1 if token_ratio > 2.0 else 0) * 0.3 +
            (1 if system_prompt_leak else 0) * 0.3
        )

        return {"risk_score": risk_score, "flagged": risk_score > 0.5, "patterns": pattern_matches}
```

Alert on high-risk scores and maintain a review queue for flagged requests.

### Q19: Explain how to build a feedback loop that connects monitoring data to model improvement.

**Answer:** The monitoring-to-improvement feedback loop has four stages:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   MONITOR    │───▶│   ANALYZE    │───▶│   IMPROVE    │───▶│   VALIDATE   │
│              │    │              │    │              │    │              │
│ • Collect    │    │ • Detect     │    │ • Update     │    │ • A/B test   │
│   traces     │    │   drift      │    │   knowledge  │    │ • Canary     │
│ • Track      │    │ • Find       │    │ • Fine-tune  │    │   analysis   │
│   quality    │    │   failure    │    │ • Improve    │    │ • Regression │
│ • Log user   │    │   patterns   │    │   prompts    │    │   testing    │
│   feedback   │    │ • Cluster    │    │ • Retrain    │    │ • Monitor    │
│              │    │   errors     │    │   retriever  │    │   impact     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
       ▲                                                           │
       └───────────────────────────────────────────────────────────┘
                            Continuous Loop
```

1. **Monitor:** Collect traces, quality scores, user feedback, and drift indicators
2. **Analyze:** Identify failure patterns (low-quality responses cluster around specific topics), detect drift, categorize errors
3. **Improve:** Based on analysis — update the knowledge base for stale information, refine prompts for systematic failures, fine-tune for domain adaptation, improve retrieval for relevance drops
4. **Validate:** Test improvements using A/B testing, canary deployment, and regression test suites before full rollout

The loop is continuous — each improvement generates new monitoring data that feeds the next cycle.

### Q20: How would you implement SLOs (Service Level Objectives) for an LLM application?

**Answer:** SLOs define measurable reliability targets. For LLM applications, define SLOs across multiple dimensions:

| SLO Dimension | Objective | Measurement |
|---------------|-----------|-------------|
| **Availability** | 99.9% of requests return a non-error response | Successful responses / total requests |
| **Latency** | 95% of requests complete within 3 seconds | P95 of total response time |
| **Quality** | 90% of responses score ≥ 4.0 on relevance | Automated quality evaluation |
| **Cost** | Average cost per request ≤ $0.01 | Mean cost across all requests |
| **Drift** | Embedding PSI < 0.1 (no significant drift) | Weekly PSI calculation |

```python
class SLOTracker:
    def __init__(self):
        self.slos = {
            "availability": {"target": 0.999, "window_days": 30},
            "latency_p95": {"target": 3000, "window_days": 7},
            "quality_avg": {"target": 4.0, "window_days": 7},
        }

    def calculate_error_budget(self, slo_name: str, current_value: float) -> dict:
        slo = self.slos[slo_name]
        if slo_name == "availability":
            budget_remaining = 1 - ((1 - current_value) / (1 - slo["target"]))
        else:
            budget_remaining = max(0, current_value / slo["target"])
        return {
            "slo": slo_name,
            "target": slo["target"],
            "current": current_value,
            "budget_remaining_pct": round(budget_remaining * 100, 2),
            "at_risk": budget_remaining < 0.25,
        }
```

Track error budgets — if 75% of the error budget is consumed, freeze non-critical deployments and prioritize reliability improvements.

---
