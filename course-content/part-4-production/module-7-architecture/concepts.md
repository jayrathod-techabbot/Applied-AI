# Module 7: Architecture Design — Core Concepts

## Table of Contents
- [7.1 AI System Architecture Patterns](#71-ai-system-architecture-patterns)
  - [Microservices vs Monolith for AI](#microservices-vs-monolith-for-ai)
  - [API Gateway Patterns](#api-gateway-patterns)
  - [Async Processing: Message Queues & Event-Driven](#async-processing-message-queues--event-driven)
  - [Load Balancing](#load-balancing)
  - [Caching Strategies](#caching-strategies)
  - [Model Serving Architectures](#model-serving-architectures)
- [7.2 Scaling, Reliability, and Cost Trade-offs](#72-scaling-reliability-and-cost-trade-offs)
  - [Cost Optimization](#cost-optimization)
  - [Reliability Patterns](#reliability-patterns)
  - [Scaling Strategies](#scaling-strategies)
  - [Multi-Region Deployment](#multi-region-deployment)
  - [Observability Integration](#observability-integration)

---

## 7.1 AI System Architecture Patterns

### Microservices vs Monolith for AI

Choosing between microservices and monolithic architecture for AI systems depends on team size, scale, iteration speed, and operational maturity.

| Dimension | Monolith | Microservices |
|---|---|---|
| **Deployment** | Single artifact | Independent services |
| **Scaling** | Scale everything together | Scale individual components |
| **Latency** | In-process calls (sub-ms) | Network calls (1–10 ms) |
| **Complexity** | Low initially | High (service mesh, discovery) |
| **Fault Isolation** | One crash = total failure | Blast radius contained |
| **ML Lifecycle** | Tight coupling between model & app | Independent model versioning |
| **Best For** | Small teams, prototypes, <5 models | Large teams, 10+ models, regulated |

**Hybrid Pattern — Modular Monolith:**
Most AI teams start here. The application is a single deployable unit but internally organized into well-defined modules (inference, preprocessing, postprocessing, caching).

```
┌─────────────────────────────────────────────────┐
│              Modular Monolith                   │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Inference │  │  Cache   │  │  Auth &   │    │
│  │  Module   │◄─┤  Module  │  │  Routing  │    │
│  └────┬─────┘  └──────────┘  └──────────┘     │
│       │                                         │
│  ┌────▼─────┐  ┌──────────┐  ┌──────────┐     │
│  │ Pre/Post │  │ Observ-  │  │  Config   │    │
│  │ Process  │  │ ability  │  │  Module   │    │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
```

**When to migrate to microservices:**
- Different components have wildly different scaling needs (inference GPU vs metadata CPU)
- Teams need independent deployment cycles
- Regulatory requirements demand isolation (PHI processing separate from general logic)
- You need to serve the same model behind multiple APIs with different SLAs

### API Gateway Patterns

The API Gateway is the single entry point for all client requests. For AI systems, it handles authentication, rate limiting, model routing, and request transformation.

```
                    ┌──────────────┐
   Clients ────────►│  API Gateway │
                    │              │
                    │  • Auth      │
                    │  • Rate Limit│
                    │  • Route     │
                    │  • Transform │
                    │  • Cache     │
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────┘   │   └────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ Model A │ │ Model B │ │ Model C │
         │ (GPT-4) │ │(Claude) │ │(Llama)  │
         └─────────┘ └─────────┘ └─────────┘
```

**Key Gateway Functions for AI:**

| Function | Description | Example |
|---|---|---|
| **Model Routing** | Route to different models based on task/complexity | Simple queries → GPT-3.5, complex → GPT-4 |
| **Token Metering** | Track and enforce token budgets per user/org | 1M tokens/day per org |
| **Request Queuing** | Buffer requests during spikes | Queue depth = 1000, then reject |
| **A/B Testing** | Split traffic between model versions | 90% v1, 10% v2 |
| **Guard Rails** | Input/output validation at the edge | PII detection, content filters |

**Popular Gateway Solutions:**

| Gateway | Best For | AI-Specific Features |
|---|---|---|
| **Kong** | Enterprise, plugin ecosystem | Rate limiting, logging, custom plugins |
| **AWS API Gateway** | Serverless, AWS-native | Lambda integration, usage plans |
| **Envoy** | Service mesh, gRPC | L7 load balancing, observability |
| **LiteLLM** | AI-native gateway | Multi-LLM routing, cost tracking |
| **Portkey** | AI gateway as service | Caching, fallbacks, analytics |

**Python example — FastAPI as a lightweight gateway:**

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
import httpx
import time

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AI Gateway")
app.state.limiter = limiter

MODEL_ENDPOINTS = {
    "gpt-4": "http://model-server:8001/v1/completions",
    "llama-70b": "http://model-server:8002/v1/completions",
    "embeddings": "http://model-server:8003/v1/embeddings",
}

@app.post("/v1/chat/completions")
@limiter.limit("100/minute")
async def route_request(request: Request, body: dict):
    model = body.get("model", "gpt-4")
    if model not in MODEL_ENDPOINTS:
        raise HTTPException(400, f"Unknown model: {model}")

    start = time.time()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(MODEL_ENDPOINTS[model], json=body)

    latency = time.time() - start
    # Log for observability
    log_request(model, latency, resp.status_code)
    return resp.json()
```

### Async Processing: Message Queues & Event-Driven

Synchronous request-response breaks down for AI workloads that are compute-heavy (long inference, batch embedding, document parsing). Async processing decouples the request from the result.

**Pattern Comparison:**

| Pattern | Latency Tolerance | Throughput | Complexity | Use Case |
|---|---|---|---|---|
| **Sync** | < 5s | Low | Low | Chat, real-time Q&A |
| **Queue-based** | Seconds–hours | High | Medium | Batch inference, doc processing |
| **Event-driven** | Variable | Very High | High | Multi-step pipelines, agentic workflows |

**Queue-Based Architecture:**

```
┌──────────┐    ┌───────────────┐    ┌──────────────┐    ┌──────────┐
│  Client   │───►│  API Server   │───►│ Message Queue│───►│  Worker  │
│           │    │  (returns     │    │              │    │  Pool    │
│           │◄───│  job_id)      │    │ • SQS        │    │          │
│           │    └───────────────┘    │ • RabbitMQ   │    │ • GPU    │
│           │                        │ • Redis      │    │ • CPU    │
│           │    ┌───────────────┐    │ • Kafka      │    │          │
│           │◄───│  Callback /   │◄───│              │    │          │
│           │    │  Poll Endpoint│    └──────────────┘    └──────────┘
└──────────┘    └───────────────┘
```

**Implementation with Redis + Celery:**

```python
# tasks.py
from celery import Celery
from openai import OpenAI

app = Celery('ai_tasks', broker='redis://localhost:6379/0')
client = OpenAI()

@app.task(bind=True, max_retries=3, rate_limit='10/m')
def generate_report(self, prompt: str, model: str = "gpt-4"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        return {
            "status": "completed",
            "result": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

# api.py
from fastapi import FastAPI
from tasks import generate_report

app = FastAPI()

@app.post("/jobs")
async def create_job(prompt: str):
    task = generate_report.delay(prompt)
    return {"job_id": task.id, "status": "queued"}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    result = generate_report.AsyncResult(job_id)
    return {"job_id": job_id, "status": result.status, "result": result.result}
```

**Event-Driven with Kafka for Multi-Step Pipelines:**

```python
# Producer: Document ingestion
from confluent_kafka import Producer
import json

producer = Producer({'bootstrap.servers': 'kafka:9092'})

def ingest_document(doc_id: str, content: str):
    event = {
        "event_type": "document.ingested",
        "doc_id": doc_id,
        "content_length": len(content),
        "timestamp": datetime.utcnow().isoformat(),
    }
    producer.produce('doc-events', key=doc_id, value=json.dumps(event))
    producer.flush()

# Consumer: Chunking service
from confluent_kafka import Consumer

consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'chunking-service',
    'auto.offset.reset': 'earliest',
})
consumer.subscribe(['doc-events'])

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    event = json.loads(msg.value())
    if event['event_type'] == 'document.ingested':
        chunks = chunk_document(event['doc_id'])
        # Emit next event: document.chunked
        emit_event('doc-events', 'document.chunked', {
            'doc_id': event['doc_id'],
            'chunk_count': len(chunks),
        })
```

### Load Balancing

Load balancing distributes inference requests across multiple model replicas to maximize throughput and minimize latency.

**Strategies for AI Workloads:**

| Strategy | How It Works | Best For |
|---|---|---|
| **Round Robin** | Cycle through replicas sequentially | Uniform request sizes |
| **Least Connections** | Route to replica with fewest active requests | Variable inference times |
| **Weighted** | Assign weights based on GPU capacity | Heterogeneous hardware |
| **Latency-Based** | Track p99 latency, route to fastest | Latency-sensitive apps |
| **Token-Aware** | Estimate token count, route to least-loaded | LLM serving (vLLM) |

**GPU-Aware Load Balancing:**

```python
import asyncio
import httpx
from dataclasses import dataclass, field
import time

@dataclass
class ModelReplica:
    url: str
    gpu_memory_total: int  # GB
    gpu_memory_used: int = 0
    active_requests: int = 0
    avg_latency_ms: float = 0
    health_score: float = 1.0

class TokenAwareBalancer:
    def __init__(self, replicas: list[ModelReplica]):
        self.replicas = replicas

    def select_replica(self, estimated_tokens: int) -> ModelReplica:
        """Select replica based on estimated load."""
        healthy = [r for r in self.replicas if r.health_score > 0.5]
        if not healthy:
            raise RuntimeError("No healthy replicas available")

        # Score: lower is better
        def score(r: ModelReplica) -> float:
            load = (r.gpu_memory_used + estimated_tokens * 0.001) / r.gpu_memory_total
            return load + (r.active_requests * 0.1) + (r.avg_latency_ms * 0.001)

        return min(healthy, key=score)

    async def forward(self, request: dict) -> dict:
        tokens = estimate_tokens(request["prompt"])
        replica = self.select_replica(tokens)
        replica.active_requests += 1
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{replica.url}/generate", json=request)
            latency = (time.time() - start) * 1000
            replica.avg_latency_ms = 0.9 * replica.avg_latency_ms + 0.1 * latency
            return resp.json()
        finally:
            replica.active_requests -= 1
```

### Caching Strategies

Caching is the highest-ROI optimization for AI systems. LLM calls are expensive (latency + cost), and many requests are repetitive or semantically similar.

**Cache Types for AI:**

| Cache Type | What's Cached | Hit Rate Potential | Savings |
|---|---|---|---|
| **Exact Match** | Full response for identical prompts | 15–30% | Cost + Latency |
| **Semantic Cache** | Response for semantically similar prompts | 30–60% | Cost + Latency |
| **Embedding Cache** | Pre-computed embeddings | 50–80% | Latency only |
| **Partial/Prefix** | KV-cache for shared prompt prefixes | 20–40% | Latency only |

**Semantic Cache Implementation:**

```python
import numpy as np
from openai import OpenAI
import redis
import json
import hashlib

client = OpenAI()
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

SIMILARITY_THRESHOLD = 0.92

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def semantic_cache_get(query: str) -> dict | None:
    query_embedding = get_embedding(query)

    # Scan recent cache entries (in production, use vector DB like Redis Stack)
    for key in redis_client.scan_iter("semantic_cache:*"):
        cached = json.loads(redis_client.get(key))
        sim = cosine_similarity(query_embedding, cached["embedding"])
        if sim >= SIMILARITY_THRESHOLD:
            return {
                "response": cached["response"],
                "similarity": sim,
                "cache_hit": True,
            }
    return None

def semantic_cache_set(query: str, response: str, ttl: int = 3600):
    key = f"semantic_cache:{hashlib.sha256(query.encode()).hexdigest()}"
    value = json.dumps({
        "query": query,
        "embedding": get_embedding(query),
        "response": response,
    })
    redis_client.setex(key, ttl, value)
```

**Response Cache (Exact Match):**

```python
import hashlib
import json
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_llm_response(ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"llm_cache:{hashlib.sha256(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_llm_response(ttl=1800)
def call_llm(prompt: str, model: str = "gpt-4", **params):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **params,
    )
    return {
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens,
    }
```

### Model Serving Architectures

The serving layer is where trained models meet production traffic. Architecture choices here directly affect latency, throughput, and cost.

**Serving Framework Comparison:**

| Framework | Throughput | Latency | Quantization | Continuous Batching | Best For |
|---|---|---|---|---|---|
| **vLLM** | Very High | Low | AWQ, GPTQ, FP8 | Yes (PagedAttention) | Production LLM serving |
| **TGI** (HuggingFace) | High | Medium | GPTQ, AWQ, EETQ | Yes | HuggingFace ecosystem |
| **TensorRT-LLM** | Highest | Lowest | INT8, INT4, FP8 | Yes | NVIDIA GPUs, max perf |
| **Ollama** | Medium | Medium | GGUF (Q4–Q8) | No | Local dev, single user |
| **LiteLLM** | Proxy layer | Low overhead | N/A | N/A | Multi-provider routing |

**vLLM Architecture (PagedAttention):**

```
┌──────────────────────────────────────────────────┐
│                   vLLM Server                    │
│                                                  │
│  ┌────────────┐   ┌──────────────────────────┐  │
│  │   API      │   │    Scheduler              │  │
│  │  Layer     │──►│  • Continuous batching    │  │
│  │ (FastAPI)  │   │  • Preemption             │  │
│  └────────────┘   │  • Priority queues        │  │
│                    └───────────┬──────────────┘  │
│                                │                  │
│  ┌─────────────────────────────▼──────────────┐  │
│  │          PagedAttention Engine              │  │
│  │  • KV cache in non-contiguous pages        │  │
│  │  • Memory efficiency: near-zero waste      │  │
│  │  • Enables larger batch sizes              │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌────────────┐   ┌────────────┐   ┌─────────┐ │
│  │  GPU 0     │   │  GPU 1     │   │  GPU N  │ │
│  │  KV Pages  │   │  KV Pages  │   │  KV     │ │
│  └────────────┘   └────────────┘   └─────────┘ │
└──────────────────────────────────────────────────┘
```

**Deploying with vLLM:**

```bash
# Single GPU
python -m vllm.entrypoint.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --tensor-parallel-size 1 \
    --quantization awq \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.90 \
    --port 8000

# Multi-GPU tensor parallel
python -m vllm.entrypoint.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --tensor-parallel-size 4 \
    --quantization awq \
    --max-model-len 8192 \
    --port 8000
```

**Docker Compose for multi-model serving:**

```yaml
version: "3.8"
services:
  vllm-llama:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=0,1
    command: >
      --model meta-llama/Llama-3-70B-Instruct
      --tensor-parallel-size 2
      --quantization awq
      --max-model-len 8192
      --gpu-memory-utilization 0.90
    ports:
      - "8001:8000"
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  vllm-embeddings:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=2
    command: >
      --model BAAI/bge-large-en-v1.5
      --task embedding
    ports:
      - "8002:8000"

  api-gateway:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

**Model Serving with TGI (HuggingFace):**

```bash
# Text Generation Inference
docker run --gpus all \
    -p 8000:80 \
    -v /data/models:/data \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id meta-llama/Llama-3-70B-Instruct \
    --quantize awq \
    --max-input-tokens 4096 \
    --max-total-tokens 8192 \
    --max-batch-prefill-tokens 4096 \
    --max-batch-total-tokens 32768 \
    --num-shard 4
```

#### Key Takeaways — AI System Architecture Patterns

- Start with a **modular monolith**; migrate to microservices only when scaling or team size demands it.
- The **API gateway** is the control plane — use it for routing, metering, guardrails, and A/B testing.
- **Async processing** (queues, events) is essential for any inference workload exceeding 5 seconds.
- **Semantic caching** can cut LLM costs by 30–60% for applications with repetitive query patterns.
- **vLLM with PagedAttention** is the current best-in-class for self-hosted LLM serving throughput.

---

## 7.2 Scaling, Reliability, and Cost Trade-offs

### Cost Optimization

LLM API costs scale linearly with usage unless actively managed. Cost optimization requires strategies at the model, prompt, and architecture levels.

**Token Economics:**

| Model | Input $/1M tokens | Output $/1M tokens | Context Window | Relative Cost |
|---|---|---|---|---|
| GPT-4o | $2.50 | $10.00 | 128K | 1x (baseline) |
| GPT-4o-mini | $0.15 | $0.60 | 128K | ~6% of GPT-4o |
| Claude 3.5 Sonnet | $3.00 | $15.00 | 200K | ~1.3x |
| Claude 3 Haiku | $0.25 | $1.25 | 200K | ~9% |
| Llama 3 70B (self-hosted) | $0.50* | $0.50* | 8K | ~4% (*infra cost) |
| Llama 3 8B (self-hosted) | $0.07* | $0.07* | 8K | ~0.5% |

**Strategy 1 — Model Routing (Cascade):**

Route requests to the cheapest model that can handle the task. Only escalate to expensive models when needed.

```python
from openai import OpenAI
import json

client = OpenAI()

def classify_complexity(prompt: str) -> str:
    """Use a cheap model to classify task complexity."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "Classify the complexity of this task as 'simple', 'medium', or 'complex'. "
                       "Respond with ONLY the classification word."
        }, {
            "role": "user",
            "content": prompt
        }],
        max_tokens=10,
        temperature=0,
    )
    return response.choices[0].message.content.strip().lower()

MODEL_MAP = {
    "simple": "gpt-4o-mini",      # $0.15/$0.60
    "medium": "gpt-4o",            # $2.50/$10.00
    "complex": "gpt-4o",           # $2.50/$10.00
}

def smart_route(prompt: str, **kwargs) -> dict:
    complexity = classify_complexity(prompt)
    model = MODEL_MAP.get(complexity, "gpt-4o")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )

    return {
        "model_used": model,
        "complexity": complexity,
        "response": response.choices[0].message.content,
        "tokens": response.usage.total_tokens,
    }
```

**Strategy 2 — Prompt Optimization:**

| Technique | Savings | Implementation |
|---|---|---|
| **Shorter system prompts** | 20–40% input tokens | Remove verbose instructions |
| **Few-shot → zero-shot** | 50–80% input tokens | Use fine-tuned model instead |
| **Structured output** | 10–30% output tokens | JSON mode instead of free text |
| **Max tokens limit** | Variable | Cap output to what's needed |
| **Prompt caching** | 50% on cached prefix | OpenAI prompt caching (prefix matching) |

```python
# BAD: Verbose few-shot prompt (500+ tokens)
BAD_SYSTEM = """You are a helpful assistant. When the user asks about weather,
respond like this:
Example 1: User: "What's the weather?" → "The weather is sunny, 72°F"
Example 2: User: "Is it raining?" → "No, it's not raining."
... (many more examples) ..."""

# GOOD: Concise with structured output (50 tokens)
GOOD_SYSTEM = "You are a weather assistant. Respond in JSON: {city, temp_f, condition}"

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": GOOD_SYSTEM},
        {"role": "user", "content": "What's the weather in NYC?"},
    ],
    response_format={"type": "json_object"},
    max_tokens=100,  # Cap output
)
```

**Strategy 3 — Self-Hosted Fallback:**

For high-volume, non-critical workloads, deploy open-source models on your own infrastructure.

```python
import httpx
from openai import OpenAI

OPENAI_API_KEY = "sk-..."
VLLM_ENDPOINT = "http://vllm-server:8000/v1"

openai_client = OpenAI(api_key=OPENAI_API_KEY)
local_client = OpenAI(base_url=VLLM_ENDPOINT, api_key="dummy")

def call_with_fallback(prompt: str, prefer_local: bool = False):
    if prefer_local:
        try:
            return local_client.chat.completions.create(
                model="meta-llama/Llama-3-8B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
        except Exception:
            pass  # Fall through to OpenAI

    return openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
```

### Reliability Patterns

AI systems face unique reliability challenges: model endpoints can timeout, return garbage, or exhibit degraded quality. Three patterns are essential.

**Pattern 1 — Circuit Breaker:**

```
     ┌──────────────────────────────────────────┐
     │            Circuit Breaker States         │
     │                                          │
     │   CLOSED ──(failures > threshold)──► OPEN│
     │     ▲                                   │
     │     │                                   │
     │     │ (timeout expires)                  │
     │     │                                   │
     │  HALF-OPEN ◄─────────────────────────── │
     │     │                                   │
     │     └──(success)──► CLOSED              │
     │     └──(failure)──► OPEN                │
     └──────────────────────────────────────────┘
```

```python
import time
from enum import Enum
from dataclasses import dataclass, field

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject immediately
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: int = 30  # seconds
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    success_count_in_half: int = 0
    required_successes: int = 3

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count_in_half = 0
                return True
            return False
        return True  # HALF_OPEN: allow limited requests

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count_in_half += 1
            if self.success_count_in_half >= self.required_successes:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
```

**Pattern 2 — Retry with Exponential Backoff:**

```python
import asyncio
import random
from openai import OpenAI, RateLimitError, APIError

async def resilient_llm_call(
    prompt: str,
    model: str = "gpt-4o",
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> str:
    client = OpenAI()

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30,
            )
            return response.choices[0].message.content

        except RateLimitError:
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            await asyncio.sleep(delay)

        except APIError as e:
            if e.status_code >= 500 and attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                await asyncio.sleep(delay)
            else:
                raise
```

**Pattern 3 — Fallback Chain:**

```python
from openai import OpenAI
import anthropic

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic()

FALLBACK_CHAIN = [
    {"provider": "openai", "model": "gpt-4o"},
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
    {"provider": "anthropic", "model": "claude-3-haiku-20240307"},
]

def call_with_fallback(prompt: str) -> dict:
    errors = []
    for config in FALLBACK_CHAIN:
        try:
            if config["provider"] == "openai":
                resp = openai_client.chat.completions.create(
                    model=config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                )
                return {
                    "content": resp.choices[0].message.content,
                    "model": config["model"],
                    "fallback_used": len(errors) > 0,
                }
            else:
                resp = anthropic_client.messages.create(
                    model=config["model"],
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )
                return {
                    "content": resp.content[0].text,
                    "model": config["model"],
                    "fallback_used": len(errors) > 0,
                }
        except Exception as e:
            errors.append({"model": config["model"], "error": str(e)})

    raise RuntimeError(f"All models failed: {errors}")
```

**Combined Reliability Layer:**

```python
class ReliableLLMClient:
    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}

    def _get_breaker(self, model: str) -> CircuitBreaker:
        if model not in self.breakers:
            self.breakers[model] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30,
            )
        return self.breakers[model]

    async def call(self, prompt: str, models: list[str] = None) -> dict:
        models = models or ["gpt-4o", "gpt-4o-mini"]

        for model in models:
            breaker = self._get_breaker(model)
            if not breaker.can_execute():
                continue

            try:
                result = await resilient_llm_call(prompt, model=model)
                breaker.record_success()
                return {"content": result, "model": model}
            except Exception:
                breaker.record_failure()
                continue

        raise RuntimeError("All models unavailable (circuit breakers open)")
```

### Scaling Strategies

**Horizontal vs Vertical Scaling:**

| Dimension | Vertical (Scale Up) | Horizontal (Scale Out) |
|---|---|---|
| **What Changes** | Bigger GPU/CPU per node | More nodes/replicas |
| **Max Limit** | Single machine (8 GPUs) | Practically unlimited |
| **Downtime** | Requires restart | Zero downtime |
| **Cost Curve** | Exponential (A100 → H100) | Linear |
| **Complexity** | Low | High (orchestration, LB) |
| **Best For** | Large models that don't fit multi-node | High request volume |

**Auto-Scaling for Inference:**

```yaml
# Kubernetes HPA for vLLM serving
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Pods
      pods:
        metric:
          name: vllm:num_requests_waiting
        target:
          type: AverageValue
          averageValue: "10"
    - type: Pods
      pods:
        metric:
          name: gpu_utilization
        target:
          type: AverageValue
          averageValue: "80"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

**Scaling Decision Matrix:**

| Trigger | Action | Cool-down |
|---|---|---|
| GPU utilization > 85% | Add replica | 60s |
| Queue depth > 50 | Add replica | 30s |
| p99 latency > 10s | Add replica | 60s |
| GPU utilization < 30% | Remove replica | 300s |
| Queue depth = 0 for 5m | Remove replica | 300s |
| Error rate > 5% | Alert + add replica | Immediate |

### Multi-Region Deployment

For global AI applications, deploying across regions reduces latency and provides disaster recovery.

```
                    ┌──────────────────────┐
                    │     Global DNS       │
                    │   (Route 53 / CF)    │
                    └──┬──────┬──────┬────┘
                       │      │      │
          ┌────────────┘      │      └────────────┐
          ▼                   ▼                   ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │  US-East     │   │  EU-West     │   │  AP-South    │
   │              │   │              │   │              │
   │ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
   │ │ API GW   │ │   │ │ API GW   │ │   │ │ API GW   │ │
   │ └────┬─────┘ │   │ └────┬─────┘ │   │ └────┬─────┘ │
   │      │       │   │      │       │   │      │       │
   │ ┌────▼─────┐ │   │ ┌────▼─────┐ │   │ ┌────▼─────┐ │
   │ │ vLLM x4  │ │   │ │ vLLM x2  │ │   │ │ vLLM x2  │ │
   │ └──────────┘ │   │ └──────────┘ │   │ └──────────┘ │
   │              │   │              │   │              │
   │ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
   │ │  Redis   │ │   │ │  Redis   │ │   │ │  Redis   │ │
   │ └──────────┘ │   │ └──────────┘ │   │ └──────────┘ │
   └──────────────┘   └──────────────┘   └──────────────┘
          │                   │                   │
          └───────────┬───────┴───────┬───────────┘
                      ▼               ▼
              ┌──────────────┐ ┌──────────────┐
              │ Global Cache │ │  Monitoring  │
              │   (CDN)      │ │  (Grafana)   │
              └──────────────┘ └──────────────┘
```

**Multi-Region Considerations:**

| Factor | Strategy |
|---|---|
| **Data Residency** | Keep user data in its legal region (GDPR, etc.) |
| **Model Replication** | Pre-deploy models to all regions (avoid cold start) |
| **Cache Invalidation** | Use Redis Cluster with cross-region replication |
| **Failover** | Health-check based DNS failover (30s TTL) |
| **Cost** | Use spot instances in non-primary regions |
| **Consistency** | Eventual consistency for cache, strong for billing |

### Observability Integration

Without observability, AI systems are black boxes. Three pillars apply, plus a fourth AI-specific one: **quality**.

**The Four Pillars for AI:**

| Pillar | Tools | What to Track |
|---|---|---|
| **Metrics** | Prometheus, Datadog | Latency, throughput, token usage, cost |
| **Logs** | ELK, Loki | Request/response pairs, errors, prompts |
| **Traces** | Jaeger, OpenTelemetry | End-to-end request flow across services |
| **Quality** | Custom evals, LangSmith | Hallucination rate, relevance, coherence |

**OpenTelemetry Integration:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Setup
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("ai-gateway")
HTTPXClientInstrumentor().instrument()

# Instrumented LLM call
async def traced_llm_call(prompt: str, model: str):
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.prompt_length", len(prompt))
        span.set_attribute("llm.provider", "openai")

        response = await call_llm(prompt, model=model)

        span.set_attribute("llm.tokens.prompt", response.usage.prompt_tokens)
        span.set_attribute("llm.tokens.completion", response.usage.completion_tokens)
        span.set_attribute("llm.tokens.total", response.usage.total_tokens)
        span.set_attribute("llm.cost_usd", calculate_cost(response.usage, model))
        span.set_attribute("llm.finish_reason", response.choices[0].finish_reason)

        return response
```

**Key Metrics Dashboard:**

| Metric | Alert Threshold | Description |
|---|---|---|
| `llm_request_duration_seconds` (p99) | > 15s | Inference latency |
| `llm_requests_total` (rate) | Sudden drop > 50% | Possible outage |
| `llm_errors_total` (rate) | > 5% of requests | Error rate |
| `llm_tokens_per_request` (avg) | > expected + 50% | Possible prompt injection |
| `gpu_utilization` | > 90% sustained | Need to scale |
| `gpu_memory_used` | > 95% | OOM risk |
| `cache_hit_rate` | < 20% | Cache ineffective |
| `cost_per_hour` | > budget * 1.2 | Cost overrun |

#### Key Takeaways — Scaling, Reliability, and Cost Trade-offs

- **Model routing** (cascade from cheap to expensive) can reduce costs by 60–80% without quality loss for most workloads.
- **Circuit breakers** prevent cascading failures when model providers degrade.
- **Semantic caching** is the single highest-ROI optimization for repetitive AI workloads.
- **Horizontal scaling** with Kubernetes HPA handles traffic spikes; set scale-down cooldowns generously (5+ min) to avoid thrashing.
- **Multi-region** deployment requires model pre-loading, cache replication, and data-residency-aware routing.
- **Observability** for AI must include the fourth pillar: **quality metrics** (hallucination rate, relevance scores).

---

## Summary

| Topic | Core Principle |
|---|---|
| Architecture Pattern | Start modular monolith, extract services when scaling demands it |
| API Gateway | Single entry point for auth, routing, metering, guardrails |
| Async Processing | Decouple request from compute for workloads > 5s |
| Caching | Semantic cache = 30–60% cost reduction |
| Model Serving | vLLM (PagedAttention) for self-hosted LLM throughput |
| Cost Optimization | Route cheap-first, optimize prompts, self-host at volume |
| Reliability | Circuit breaker + retry + fallback chain |
| Scaling | HPA on GPU utilization and queue depth |
| Multi-Region | Pre-load models, replicate cache, respect data residency |
| Observability | Metrics + Logs + Traces + Quality |
