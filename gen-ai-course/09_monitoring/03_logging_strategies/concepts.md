# AI Logging Strategies - Concepts

## Why AI Logging is Different

AI systems require specialized logging because:
- **Probabilistic outputs**: Need to capture model confidence and reasoning
- **Multi-stage pipelines**: RAG has retrieval + generation stages
- **Cost tracking**: Token usage affects billing
- **PII concerns**: User data in prompts requires careful handling
- **Agent workflows**: Complex multi-step executions need tracing

## Logging Components

### 1. Request Logging

**Essential Fields:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123",
  "user_id": "user_xyz789",
  "model": "gpt-4",
  "prompt": "User query text",
  "prompt_tokens": 150,
  "completion_tokens": 200,
  "latency_ms": 1500,
  "metadata": {
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### 2. Retrieval Logging (RAG)

```json
{
  "request_id": "req_abc123",
  "query_embedding": [0.1, -0.2, ...],
  "retrieved_documents": [
    {
      "doc_id": "doc_001",
      "chunk_text": "...",
      "similarity_score": 0.92,
      "rank": 1
    }
  ],
  "retrieval_time_ms": 45,
  "num_retrieved": 5
}
```

### 3. Response Logging

```json
{
  "request_id": "req_abc123",
  "response_text": "Generated response...",
  "total_tokens": 350,
  "finish_reason": "stop",
  "model_version": "gpt-4-0613",
  "response_quality_score": 0.85
}
```

### 4. Error Logging

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123",
  "error_type": "RateLimitError",
  "error_message": "Rate limit exceeded",
  "retry_count": 3,
  "stack_trace": "...",
  "recovered": true
}
```

## Structured Logging Best Practices

### Use JSON Format

```python
import logging
import json

def log_request(request_data):
    logging.info(json.dumps(request_data))
```

### Include Correlation IDs

Track requests across services:
- `request_id`: Unique per request
- `trace_id`: Across distributed systems
- `session_id`: For conversation tracking

### Log Levels Strategy

| Level | Use Case |
|-------|----------|
| DEBUG | Detailed request/response for debugging |
| INFO | Normal operation events |
| WARNING | Recoverable issues, retries |
| ERROR | Failures requiring attention |
| CRITICAL | System-wide failures |

## PII Handling

### Techniques

1. **Masking**: Replace sensitive data
   ```python
   import re
   
   def mask_pii(text):
       # Mask email
       text = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[EMAIL]', text)
       # Mask phone
       text = re.sub(r'\d{3}-\d{3}-\d{4}', '[PHONE]', text)
       return text
   ```

2. **Hashing**: One-way transformation for identification
   ```python
   import hashlib
   
   def hash_user_id(user_id):
       return hashlib.sha256(user_id.encode()).hexdigest()[:8]
   ```

3. **Tokenization**: Replace with reference tokens

4. **Exclusion**: Don't log sensitive fields at all

### Compliance Considerations

- **GDPR**: Right to erasure, data minimization
- **HIPAA**: Healthcare data protection
- **CCPA**: Consumer privacy rights

## Cost Tracking

### Metrics to Log

| Metric | Description |
|--------|-------------|
| Input tokens | Tokens in prompts |
| Output tokens | Tokens in completions |
| API calls | Number of model calls |
| Cache hits | Cached requests |
| Embedding costs | Vectorization costs |

### Cost Calculation

```python
def calculate_cost(input_tokens, output_tokens):
    # Example pricing (GPT-4)
    input_cost = input_tokens / 1000 * 0.03
    output_cost = output_tokens / 1000 * 0.06
    return input_cost + output_cost
```

## Agent Execution Tracing

### What to Log

1. **Tool Calls**: Which tools were invoked
2. **Tool Inputs/Outputs**: Arguments and results
3. **Decision Points**: Why certain actions were taken
4. **Execution Time**: Per-step timing
5. **Success/Failure**: Outcome of each step

### Example Trace

```json
{
  "trace_id": "trace_abc123",
  "steps": [
    {
      "step": 1,
      "tool": "search",
      "input": {"query": "weather in NYC"},
      "output": "Sunny, 72F",
      "duration_ms": 120
    },
    {
      "step": 2,
      "tool": "respond",
      "input": {"text": "Today's weather..."},
      "output": "Generated response",
      "duration_ms": 450
    }
  ]
}
```

## Log Aggregation Tools

### Popular Solutions

| Tool | Use Case |
|------|----------|
| ELK Stack | Full-text search, analytics |
| Splunk | Enterprise logging, compliance |
| Datadog | APM + logging integration |
| CloudWatch | AWS-native logging |
| Loki | Grafana-integrated logging |

### Implementation

```python
# Example: Sending logs to ELK
import logging
from elasticsearch import Elasticsearch

class ElasticHandler(logging.Handler):
    def __init__(self, es_host, index):
        super().__init__()
        self.es = Elasticsearch([es_host])
        self.index = index
    
    def emit(self, record):
        doc = self.format(record)
        self.es.index(index=self.index, document=doc)
```

## Advanced Techniques

### 1. Sampling

Not every request needs full logging:
```python
import random

def should_log():
    return random.random() < 0.1  # Log 10% of requests
```

### 2. Async Logging

Don't block requests with logging:
```python
import asyncio
import logging

async def log_async(message):
    await asyncio.to_thread(logging.info, message)
```

### 3. Log-Based Metrics

Derive metrics from logs:
- Error rate: Count errors / total requests
- Latency percentiles: Parse latency values
- Cost aggregation: Sum token costs

### 4. Retention Policies

| Data Type | Retention |
|-----------|-----------|
| Full logs | 30 days |
| Aggregated metrics | 1 year |
| Audit logs | 7 years |
| Error logs | 90 days |

## Summary

Key logging components:
1. **Structured JSON** for parseable logs
2. **Correlation IDs** for tracing
3. **PII handling** for compliance
4. **Cost tracking** for budgeting
5. **Agent traces** for debugging workflows
6. **Appropriate retention** for storage efficiency
