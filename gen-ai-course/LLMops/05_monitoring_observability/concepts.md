# Monitoring & Observability - Concepts

## Table of Contents
1. [Introduction to LLM Observability](#introduction-to-llm-observability)
2. [Key Metrics](#key-metrics)
3. [Logging Strategy](#logging-strategy)
4. [Tracing](#tracing)
5. [Alerting](#alerting)
6. [Dashboards](#dashboards)
7. [Tools & Technologies](#tools--technologies)
8. [Implementation](#implementation)

---

## Introduction to LLM Observability

### The Three Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                   Observability Pillars                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Logs      │  │   Metrics   │  │   Traces    │             │
│  │             │  │             │  │             │             │
│  │ - Events    │  │ - Counters  │  │ - Spans     │             │
│  │ - Timestamps│  │ - Gauges    │  │ - Timing    │             │
│  │ - Context   │  │ - Histograms│  │ - Context   │             │
│  │             │  │             │  │             │             │
│  │  "What      │  │  "How       │  │  "How       │             │
│  │   happened" │  │   much?"     │  │   long?"    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### LLM-Specific Observability Challenges

1. **Token Tracking**: Need to track input/output tokens per request
2. **Cost Attribution**: Calculate cost per user/endpoint
3. **Quality Metrics**: Measure response quality, relevance
4. **Prompt Versioning**: Track which prompt version was used
5. **Latency**: End-to-end latency including API calls

---

## Key Metrics

### 1. System Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Request Rate | Requests per second | Varies by load |
| Error Rate | Percentage of failed requests | < 1% |
| Latency p50 | Median response time | < 500ms |
| Latency p95 | 95th percentile | < 2s |
| Latency p99 | 99th percentile | < 5s |
| Throughput | Tokens processed per second | Max |

### 2. LLM-Specific Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                  LLM-Specific Metrics                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Request-Level Metrics                                          │
│  ─────────────────────                                          │
│  • input_tokens: Number of input tokens                         │
│  • output_tokens: Number of output tokens                      │
│  • total_tokens: input + output                                │
│  • prompt_tokens: Tokens in the prompt (excluding user input)  │
│  • completion_tokens: Generated tokens                        │
│                                                                  │
│  Cost Metrics                                                  │
│  ────────────                                                  │
│  • cost_per_request: $ based on token usage                    │
│  • cost_per_user: Total cost per user per day                  │
│  • cost_per_endpoint: Cost per API endpoint                    │
│  • budget_utilization: % of budget used                        │
│                                                                  │
│  Quality Metrics                                               │
│  ─────────────                                                 │
│  • quality_score: LLM-as-judge score (0-1)                    │
│  • relevance_score: RAG retrieval relevance                   │
│  • hallucination_rate: Detected hallucinations per 1K requests │
│  • user_satisfaction: Feedback-based score                     │
│                                                                  │
│  Performance Metrics                                           │
│  ────────────────                                              │
│  • time_to_first_token: TTFT (for streaming)                  │
│  • tokens_per_second: Generation speed                        │
│  • context_utilization: % of context window used              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Business Metrics

| Metric | Description |
|--------|-------------|
| Tasks Completed | Successful task completion rate |
| Deflection Rate | % of issues resolved by LLM without human |
| User Retention | User return rate |
| Cost per Conversation | Total cost / number of conversations |
| Revenue per User | Business value generated |

---

## Logging Strategy

### Log Levels

```python
# log_levels.py
from enum import Enum
from typing import Any
import json
import logging

class LLMLogLevel(Enum):
    TRACE = 5      # Detailed trace information
    DEBUG = 10     # Debug information
    INFO = 20      # General information
    WARNING = 30   # Warning messages
    ERROR = 40     # Error messages
    CRITICAL = 50  # Critical issues

class LLMLogger:
    """
    Structured logger for LLM applications
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
    
    def log_request(
        self,
        request_id: str,
        user_id: str,
        prompt: str,
        model: str,
        metadata: dict = None
    ):
        """Log incoming LLM request"""
        log_data = {
            "request_id": request_id,
            "user_id": user_id,
            "timestamp": self._get_timestamp(),
            "event": "llm_request",
            "model": model,
            "prompt_length": len(prompt),
            "metadata": metadata or {}
        }
        self.logger.info(json.dumps(log_data))
    
    def log_response(
        self,
        request_id: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        error: str = None
    ):
        """Log LLM response"""
        log_data = {
            "request_id": request_id,
            "timestamp": self._get_timestamp(),
            "event": "llm_response",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "response_length": len(response),
            "error": error
        }
        
        if error:
            self.logger.error(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))
    
    def log_cost_breakdown(
        self,
        request_id: str,
        model: str,
        input_cost: float,
        output_cost: float,
        total_cost: float,
        currency: str = "USD"
    ):
        """Log cost breakdown"""
        log_data = {
            "request_id": request_id,
            "timestamp": self._get_timestamp(),
            "event": "llm_cost",
            "model": model,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "currency": currency
        }
        self.logger.info(json.dumps(log_data))
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
```

### PII Handling in Logs

```python
# pii_handler.py
import re
from typing import Optional

class PIIHandler:
    """
    Handle PII in logs to ensure compliance
    """
    
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }
    
    @classmethod
    def redact_pii(cls, text: str) -> str:
        """Redact PII from text"""
        redacted = text
        
        for pii_type, pattern in cls.PII_PATTERNS.items():
            redacted = re.sub(pattern, f"[{pii_type}_redacted]", redacted)
        
        return redacted
    
    @classmethod
    def hash_user_id(cls, user_id: str) -> str:
        """Hash user ID for privacy"""
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
```

---

## Tracing

### Distributed Tracing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Distributed Tracing Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Request: "Explain quantum computing"                          │
│        │                                                          │
│        ▼                                                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   API Gateway                             │   │
│   │  ┌─────────────────────────────────────────────────────┐│  │
│   │  │  Span: api_gateway                                  ││  │
│   │  │  Duration: 5ms                                     ││  │
│   │  └─────────────────────────────────────────────────────┘│  │
│   └────────────────────┬────────────────────────────────────┘   │
│                        │                                           │
│        ┌───────────────┼───────────────┐                         │
│        ▼               ▼               ▼                         │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                     │
│   │  Auth   │    │  Rate   │    │ Router  │                     │
│   │ Service │    │ Limiter │    │ Service │                     │
│   │  Span   │    │  Span   │    │  Span   │                    │
│   └────┬────┘    └────┬────┘    └────┬────┘                     │
│        │               │               │                          │
│        └───────────────┼───────────────┘                         │
│                        │                                           │
│                        ▼                                           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │               LLM Service Span                            │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│   │  │   Prompt    │  │   API Call  │  │   Response  │     │   │
│   │  │ Preparation │  │  (200ms)    │  │  Parsing    │     │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation with OpenTelemetry

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.trace import Status, StatusCode

# Initialize tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure exporter (e.g., to Jaeger, Zipkin, or OTEL collector)
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument OpenAI
OpenAIInstrumentor().instrument()

class LLMLogger:
    """
    Traced logger for LLM operations
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(service_name)
    
    async def traced_chat_completion(
        self,
        prompt: str,
        model: str,
        user_id: str
    ):
        """Trace LLM chat completion"""
        with self.tracer.start_as_current_span(
            "llm.chat_completion",
            attributes={
                "model": model,
                "user_id": user_id,
                "prompt_length": len(prompt)
            }
        ) as span:
            try:
                # Call LLM
                response = await self._call_llm(prompt, model)
                
                # Add response attributes
                span.set_attribute("response_length", len(response))
                span.set_attribute("status", "success")
                
                return response
                
            except Exception as e:
                # Record error
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def _call_llm(self, prompt: str, model: str):
        # Your LLM call logic here
        pass

# Usage with context
async def handle_request(request: dict):
    logger = LLMLogger("my-service")
    
    with logger.tracer.start_as_current_span("handle_request") as span:
        span.set_attribute("request_id", request["id"])
        
        response = await logger.traced_chat_completion(
            prompt=request["prompt"],
            model=request["model"],
            user_id=request["user_id"]
        )
        
        return response
```

---

## Alerting

### Alert Rules

```yaml
# alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: llm-alerts
  labels:
    prometheus: k8s
spec:
  groups:
    - name: llm-operational
      interval: 30s
      rules:
        # High Error Rate
        - alert: HighErrorRate
          expr: |
            (
              sum(rate(llm_requests_total{status=~"5.."}[5m])) 
              / 
              sum(rate(llm_requests_total[5m]))
            ) > 0.05
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "High error rate detected"
            description: "Error rate is {{ $value | humanizePercentage }}"
        
        # High Latency
        - alert: HighLatencyP95
          expr: |
            histogram_quantile(0.95, 
              sum(rate(llm_request_duration_seconds_bucket[5m])) 
              by (le, model)
            ) > 5
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High p95 latency"
            description: "p95 latency for {{ $labels.model }} is {{ $value }}s"
        
        # Budget Overspend
        - alert: BudgetOverspend
          expr: |
            (
              sum(rate(llm_cost_total[1h])) 
              / 
              (weekly_budget / 168)
            ) > 1.2
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Budget overspend detected"
            description: "Current spend rate is 120% of budget"
        
        # Cache Hit Rate Low
        - alert: LowCacheHitRate
          expr: llm_cache_hit_rate < 0.3
          for: 10m
          labels:
            severity: info
          annotations:
            summary: "Cache hit rate below 30%"
        
        # Token Limit Approaching
        - alert: TokenLimitApproaching
          expr: |
            (
              llm_tokens_used / llm_token_limit
            ) > 0.8
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Token limit approaching"
```

### Alert Notification Channels

```python
# alerting.py
from typing import List, Callable

class AlertManager:
    """
    Manage alert notifications
    """
    
    def __init__(self):
        self.handlers: List[Callable] = []
    
    def add_handler(self, handler: Callable):
        """Add notification handler"""
        self.handlers.append(handler)
    
    async def send_alert(
        self,
        alert_name: str,
        severity: str,
        message: str,
        metadata: dict = None
    ):
        """Send alert to all handlers"""
        alert = {
            "name": alert_name,
            "severity": severity,
            "message": message,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp()
        }
        
        for handler in self.handlers:
            try:
                await handler(alert)
            except Exception as e:
                print(f"Failed to send alert to handler: {e}")

# Example: Slack handler
async def slack_alert_handler(alert: dict):
    import aiohttp
    
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    
    severity_emoji = {
        "critical": "🔴",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    
    payload = {
        "text": f"{severity_emoji.get(alert['severity'], '')} {alert['name']}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": alert["name"]}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": alert["message"]}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"*Severity:* {alert['severity']}"},
                    {"type": "mrkdwn", "text": f"*Time:* {alert['timestamp']}"}
                ]
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)
```

---

## Dashboards

### Key Dashboard Panels

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Operations Dashboard                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Request Volume          │  Error Rate                     │ │
│  │  ████████████░░░░        │  ██░░░░░░░░░░░░░░               │ │
│  │  1.2K/min                │  0.8%                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Latency (p50/p95/p99)     │  Cost per Hour                 │ │
│  │  ███░░ / ██████░░ / █████  │  ██████████░░░               │ │
│  │  200ms/800ms/1.5s         │  $45.23                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Token Usage (Input/Output)    │  Model Distribution       │ │
│  │  ████████████░░░░             │  ████░░░░ (gpt-4)         │ │
│  │  2.1M / 890K                 │  █████████████████ (gpt-35)│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Top Endpoints by Cost                                     │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │ /api/chat         ████████████████████   $125.50     │ │ │
│  │  │ /api/summarize    ██████████████░░░░░    $89.30      │ │ │
│  │  │ /api/analyze      ████████░░░░░░░░░░░    $45.20      │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Quality Metrics                                           │ │
│  │  User Satisfaction: 4.2/5  │  Relevance Score: 0.87      │ │
│  │  Hallucination Rate: 0.02%  │  Task Completion: 94%       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Grafana Dashboard JSON

```json
{
  "dashboard": {
    "title": "LLM Operations Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(llm_requests_total[1m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate by Model",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(llm_requests_total{status=~\"5..\"}[5m])) by (model) / sum(rate(llm_requests_total[5m])) by (model)",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "title": "Latency Percentiles",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(llm_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(llm_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(llm_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Token Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(llm_tokens_input_total[5m]))",
            "legendFormat": "Input tokens/sec"
          },
          {
            "expr": "sum(rate(llm_tokens_output_total[5m]))",
            "legendFormat": "Output tokens/sec"
          }
        ]
      },
      {
        "title": "Cost by Hour",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(llm_cost_total[1h]))",
            "legendFormat": "Cost/hour ($)"
          }
        ]
      }
    ]
  }
}
```

---

## Tools & Technologies

### Observability Stack

| Category | Tools |
|----------|-------|
| **Metrics** | Prometheus, Datadog, New Relic, CloudWatch |
| **Logging** | ELK Stack, Loki, CloudWatch Logs |
| **Tracing** | Jaeger, Zipkin, Tempo, AWS X-Ray |
| **APM** | Datadog APM, New Relic APM, AWS X-Ray |
| **LLM-specific** | LangSmith, Helicone, Langtrace, PromptLayer |

### LangSmith Integration

```python
# langsmith_integration.py
from langsmith import Client
import os

# Set up LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.environ.get("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "production"

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import chain

# Initialize client
langsmith_client = Client()

# Track metrics
class LangSmithMetrics:
    @staticmethod
    def log_feedback(run_id: str, score: float, feedback_type: str = "user_score"):
        """Log user feedback to LangSmith"""
        langsmith_client.create_feedback(
            run_id=run_id,
            key=feedback_type,
            score=score
        )
    
    @staticmethod
    def get_run_stats(project_name: str = "production") -> dict:
        """Get statistics for a project"""
        runs = langsmith_client.list_runs(
            project_name=project_name,
            execution_order="asc"
        )
        
        total_runs = 0
        total_tokens = 0
        total_cost = 0
        
        for run in runs:
            total_runs += 1
            if hasattr(run, 'token_usage'):
                total_tokens += run.token_usage.get('total_tokens', 0)
                total_cost += run.token_usage.get('cost', 0)
        
        return {
            "total_runs": total_runs,
            "total_tokens": total_tokens,
            "total_cost": total_cost
        }
```

---

## Implementation

### Complete Monitoring Setup

```python
# monitoring_setup.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Define metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status', 'endpoint']
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model', 'endpoint']
)

llm_tokens_input_total = Counter(
    'llm_tokens_input_total',
    'Total input tokens',
    ['model']
)

llm_tokens_output_total = Counter(
    'llm_tokens_output_total',
    'Total output tokens',
    ['model']
)

llm_cost_total = Counter(
    'llm_cost_total',
    'Total cost in USD',
    ['model', 'endpoint']
)

llm_active_requests = Gauge(
    'llm_active_requests',
    'Number of active requests',
    ['model']
)

llm_cache_hits_total = Counter(
    'llm_cache_hits_total',
    'Total cache hits'
)

llm_cache_misses_total = Counter(
    'llm_cache_misses_total',
    'Total cache misses'
)

class LLMMonitor:
    """
    Complete LLM monitoring solution
    """
    
    # Pricing (example rates)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    }
    
    def __init__(self, model: str, endpoint: str):
        self.model = model
        self.endpoint = endpoint
    
    async def __aenter__(self):
        # Increment active requests
        llm_active_requests.labels(model=self.model).inc()
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Record duration
        llm_request_duration_seconds.labels(
            model=self.model,
            endpoint=self.endpoint
        ).observe(duration)
        
        # Record success/error
        status = "error" if exc_type else "success"
        llm_requests_total.labels(
            model=self.model,
            status=status,
            endpoint=self.endpoint
        ).inc()
        
        # Decrement active requests
        llm_active_requests.labels(model=self.model).dec()
        
        return False  # Don't suppress exceptions
    
    def record_tokens(self, input_tokens: int, output_tokens: int):
        """Record token usage"""
        llm_tokens_input_total.labels(model=self.model).inc(input_tokens)
        llm_tokens_output_total.labels(model=self.model).inc(output_tokens)
        
        # Calculate and record cost
        pricing = self.PRICING.get(self.model, {"input": 0, "output": 0})
        cost = (input_tokens / 1000) * pricing["input"]
        cost += (output_tokens / 1000) * pricing["output"]
        
        llm_cost_total.labels(
            model=self.model,
            endpoint=self.endpoint
        ).inc(cost)

# Usage
async def handle_llm_request(prompt: str, model: str):
    endpoint = "/api/chat"
    
    async with LLMMonitor(model, endpoint) as monitor:
        # Your LLM call
        response, tokens = await call_llm(prompt, model)
        
        # Record tokens
        monitor.record_tokens(tokens.input, tokens.output)
        
        return response
```

### Start Prometheus Metrics Server

```bash
# Start metrics server on port 8000
if __name__ == "__main__":
    start_http_server(8000)
    print("Metrics server started on port 8000")
```

---

## Best Practices

1. **Start Early**: Add observability from the beginning
2. **Use Standard Metrics**: Follow industry standards
3. **Set Meaningful Alerts**: Avoid alert fatigue
4. **Log Structured Data**: Use JSON for easier parsing
5. **Track Costs**: Essential for LLM applications
6. **Monitor Quality**: Don't just track technical metrics
7. **Correlate Data**: Link logs, metrics, and traces
8. **Retention Policy**: Balance cost and compliance
