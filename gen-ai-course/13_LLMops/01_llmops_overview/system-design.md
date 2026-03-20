# LLMops System Design

## Table of Contents
1. [Design Principles](#design-principles)
2. [Architecture Patterns](#architecture-patterns)
3. [High-Level Designs](#high-level-designs)
4. [Component Deep Dives](#component-deep-dives)
5. [Scaling Strategies](#scaling-strateges)
6. [Failure Handling](#failure-handling)
7. [Security Architecture](#security-architecture)
8. [Cost Optimization Architecture](#cost-optimization-architecture)

---

## Design Principles

### 1. Reliability
```
┌─────────────────────────────────────────────────────────────────┐
│                      Reliability Principles                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Fail Fast, Recover Fast                                    │
│     ├── Circuit breakers                                       │
│     ├── Health checks                                          │
│     └── Graceful degradation                                  │
│                                                                  │
│  2. Idempotency                                                │
│     ├── Request deduplication                                  │
│     └── Idempotent operations                                 │
│                                                                  │
│  3. Observability                                              │
│     ├── Distributed tracing                                     │
│     └── Comprehensive logging                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Scalability
- Horizontal scaling for stateless services
- Vertical scaling for GPU workloads
- Connection pooling for database access
- Caching layers for common requests

### 3. Security
- Defense in depth
- Least privilege access
- Zero trust architecture
- Regular security audits

### 4. Cost-Efficiency
- Pay only for what you use
- Optimize token usage
- Implement smart caching
- Use appropriate model tiers

---

## Architecture Patterns

### Pattern 1: API-Based LLM Service

```
┌─────────────────────────────────────────────────────────────────┐
│                 API-Based LLM Service Architecture              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐                                                  │
│   │  Client │                                                  │
│   └────┬────┘                                                  │
│        │ HTTPS                                                 │
│        ▼                                                       │
│   ┌─────────────────────────────────────────┐                  │
│   │           API Gateway                    │                  │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │                  │
│   │  │ Auth   │ │ Rate   │ │ Router │    │                  │
│   │  │ Check  │ │ Limit  │ │       │    │                  │
│   │  └─────────┘ └─────────┘ └─────────┘    │                  │
│   └────────────────┬────────────────────────┘                  │
│                    │                                            │
│                    ▼                                            │
│   ┌─────────────────────────────────────────┐                  │
│   │        LLM Service Layer                │                  │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │                  │
│   │  │ Prompt  │ │ Request │ │ Response│    │                  │
│   │  │ Manager │ │ Batcher │ │ Parser  │    │                  │
│   │  └─────────┘ └─────────┘ └─────────┘    │                  │
│   └────────────────┬────────────────────────┘                  │
│                    │                                            │
│         ┌──────────┼──────────┐                                │
│         ▼          ▼          ▼                                │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                            │
│   │ Cache  │ │ Vector  │ │ LLM     │                            │
│   │ Layer  │ │ Store   │ │ Provider│                            │
│   │(Redis) │ │(Pinecone)│ │(OpenAI)│                            │
│   └─────────┘ └─────────┘ └─────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**
- **API Gateway**: Handles auth, rate limiting, routing
- **Prompt Manager**: Manages prompt versions and templates
- **Request Batcher**: Batches multiple requests for efficiency
- **Response Parser**: Parses and validates LLM responses
- **Cache Layer**: Redis for semantic caching
- **Vector Store**: For RAG-based applications

### Pattern 2: Self-Hosted LLM Service

```
┌─────────────────────────────────────────────────────────────────┐
│              Self-Hosted LLM Service Architecture               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐                                                  │
│   │  Client │                                                  │
│   └────┬────┘                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────┐                  │
│   │         Load Balancer (nginx/HAProxy)   │                  │
│   └────────────────┬────────────────────────┘                  │
│                    │                                            │
│                    ▼                                            │
│   ┌─────────────────────────────────────────┐                  │
│   │      Inference API Server (FastAPI)     │                  │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │                  │
│   │  │ Request │ │ Model   │ │ Output  │    │                  │
│   │  │ Queue   │ │ Loader  │ │ Validator│   │                  │
│   │  └─────────┘ └─────────┘ └─────────┘    │                  │
│   └────────────────┬────────────────────────┘                  │
│                    │                                            │
│                    ▼                                            │
│   ┌─────────────────────────────────────────┐                  │
│   │        Model Inference Workers           │                  │
│   │  ┌─────────────────────────────────┐    │                  │
│   │  │ GPU Pods (1 per model version)  │    │                  │
│   │  │ ┌─────────┐ ┌─────────────────┐ │    │                  │
│   │  │ │ vLLM/   │ │ CUDA Runtime   │ │    │                  │
│   │  │ │ TGI     │ │                │ │    │                  │
│   │  │ └─────────┘ └─────────────────┘ │    │                  │
│   │  └─────────────────────────────────┘    │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                  │
│   ┌─────────────────────────────────────────┐                  │
│   │      Model Storage (NFS/S3)              │                  │
│   │  ├── model-v1.safetensors               │                  │
│   │  ├── model-v2.safetensors               │                  │
│   │  └── config.json                        │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pattern 3: Hybrid Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Hybrid LLM Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌─────────────────┐                          │
│                    │  Request Router │                          │
│                    │  (Smart Router) │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│          ┌──────────────────┼──────────────────┐               │
│          │                  │                  │               │
│    ┌─────▼─────┐     ┌──────▼──────┐    ┌─────▼─────┐        │
│    │  Simple   │     │ Complex      │    │ Sensitive │        │
│    │  Queries  │     │ Reasoning    │    │ Data      │        │
│    └─────┬─────┘     └──────┬──────┘    └─────┬─────┘        │
│          │                  │                  │               │
│          ▼                  ▼                  ▼               │
│   ┌────────────┐     ┌────────────┐     ┌────────────┐        │
│   │ Self-Hosted│     │ API-Based  │     │ Local      │        │
│   │ (7B model) │     │ (GPT-4)    │     │ (Privacy)  │        │
│   │ Low Latency│     │ High Qual. │     │            │        │
│   └────────────┘     └────────────┘     └────────────┘        │
│                                                                  │
│   Benefits:                                                      │
│   ├── Cost-effective for simple tasks                           │
│   ├── High quality for complex tasks                           │
│   └── Privacy preserved for sensitive data                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## High-Level Designs

### Design 1: Chatbot Service

```
┌─────────────────────────────────────────────────────────────────┐
│                    Chatbot Service Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Frontend (Web/Mobile)                    ││
│  └────────────────────────────┬────────────────────────────────┘│
│                               │ WebSocket/HTTP                   │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    WebSocket Gateway                         ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               ││
│  │  │ Connection│  │  Message  │  │  Room    │               ││
│  │  │ Manager  │  │  Queue    │  │  Manager │               ││
│  │  └──────────┘  └──────────┘  └──────────┘               ││
│  └────────────────────────────┬────────────────────────────────┘│
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                 Chat Service Layer                          ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               ││
│  │  │ Session  │  │  Context  │  │  Message  │               ││
│  │  │ Manager  │  │  Builder  │  │  Processor│               ││
│  │  └──────────┘  └──────────┘  └──────────┘               ││
│  └────────────────────────────┬────────────────────────────────┘│
│                               │                                  │
│           ┌───────────────────┼───────────────────┐            │
│           ▼                   ▼                   ▼            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     │
│  │   Memory    │     │    RAG      │     │    LLM      │     │
│  │  (History)  │     │   Pipeline  │     │   Provider  │     │
│  │             │     │             │     │             │     │
│  │ Redis +     │     │ Vector DB  │     │ OpenAI/     │     │
│  │ Summarizer  │     │ + Retriever │     │ Anthropic   │     │
│  └─────────────┘     └─────────────┘     └─────────────┘     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Storage Layer                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  ││
│  │  │ Message  │  │  User    │  │  Session │                  ││
│  │  │ Store    │  │  Profile │  │  Store   │                  ││
│  │  │(Postgres)│  │  (Redis) │  │  (Redis) │                  ││
│  │  └──────────┘  └──────────┘  └──────────┘                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Components:**

1. **WebSocket Gateway**: Manages real-time connections
2. **Session Manager**: Handles conversation state
3. **Context Builder**: Builds prompt context from history
4. **Memory**: Stores conversation history with summarization
5. **RAG Pipeline**: For knowledge-augmented responses

### Design 2: RAG-Based Q&A System

```
┌─────────────────────────────────────────────────────────────────┐
│                  RAG-Based Q&A Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Query ───────────────────────────────────────────────────▶   │
│                                                                    │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Query Processing                      │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│   │  │ Intent      │  │ Entity      │  │ Query       │    │   │
│   │  │ Detection   │  │ Extraction  │  │ Rewriting   │    │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│   └────────────────────────┬────────────────────────────────┘   │
│                            │                                      │
│                            ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 Retrieval Pipeline                        │   │
│   │                                                          │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│   │  │ Query       │  │ Hybrid      │  │ Re-Ranking  │    │   │
│   │  │ Embedding   │──▶│ Search     │──▶│ (Cross-     │    │   │
│   │  │ (text-ada)  │  │ (BM25 +     │  │  Encoder)   │    │   │
│   │  └─────────────┘  │  Vector)    │  └─────────────┘    │   │
│   │                    └─────────────┘         │            │   │
│   │                                          │            │   │
│   │                                          ▼            │   │
│   │  ┌─────────────────────────────────────────────────┐   │   │
│   │  │ Context Preparation                            │   │   │
│   │  │ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │   │   │
│   │  │ │ Citation    │ │ Source      │ │ Context   │ │   │   │
│   │  │ │ Generator   │ │ Metadata    │ │ Truncation│ │   │   │
│   │  │ └─────────────┘ └─────────────┘ └───────────┘ │   │   │
│   │  └─────────────────────────────────────────────────┘   │   │
│   └────────────────────────┬────────────────────────────────┘   │
│                            │                                      │
│                            ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    LLM Generation                        │   │
│   │                                                          │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│   │  │ Prompt      │  │ Token       │  │ Response    │    │   │
│   │  │ Template    │──▶│ Generation  │──▶│ Validator   │    │   │
│   │  │ (RAG)       │  │             │  │             │    │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                    │
│   ◀─────────────────────────────────────────────────── Result    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Design 3: Batch Processing System

```
┌─────────────────────────────────────────────────────────────────┐
│                  Batch Processing Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │                   Job Submission                           │ │
│   │     ┌──────────────────────────────────────────────────┐  │ │
│   │     │  REST API / File Upload / Scheduled Trigger     │  │ │
│   │     └──────────────────────────────────────────────────┘  │ │
│   │                           │                                │ │
│   └───────────────────────────┼────────────────────────────────┘ │
│                               ▼                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │               Job Queue (Redis/RabbitMQ)                  │ │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │ │
│   │  │ Job #1  │  │ Job #2  │  │ Job #3  │  │ Job #4  │      │ │
│   │  │ (Queue) │  │(Queue)  │  │(Queue)  │  │(Queue)  │      │ │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │ │
│   └───────────────────────────┬────────────────────────────────┘ │
│                               │                                  │
│         ┌─────────────────────┼─────────────────────┐            │
│         │                     │                     │            │
│         ▼                     ▼                     ▼            │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│   │ Worker 1    │     │ Worker 2    │     │ Worker N    │       │
│   │ (GPU Node)  │     │ (GPU Node)  │     │ (GPU Node)  │       │
│   │             │     │             │     │             │       │
│   │ Batch Size: │     │ Batch Size: │     │ Batch Size: │       │
│   │    16       │     │    16       │     │    16       │       │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│          │                   │                     │             │
│          └───────────────────┼─────────────────────┘             │
│                              ▼                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │                  Results Storage                          │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│   │  │ Database   │  │  Object    │  │  Metrics   │      │   │
│   │  │ (Postgres) │  │  Storage   │  │  (Prometheus│      │   │
│   │  │            │  │  (S3/GCS)  │  │   /StatsD)  │      │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dives

### Component 1: Request Router

```python
class LLMRouter:
    """
    Intelligent request routing based on query complexity
    """
    
    def __init__(self):
        self.routing_rules = [
            # Simple factual queries -> small, fast model
            {
                "condition": lambda q: self.is_simple_fact(q),
                "model": "gpt-3.5-turbo",
                "priority": 1
            },
            # Code generation -> code-optimized model
            {
                "condition": lambda q: self.is_code_request(q),
                "model": "gpt-4-code",
                "priority": 2
            },
            # Complex reasoning -> largest model
            {
                "condition": lambda q: self.is_complex(q),
                "model": "gpt-4",
                "priority": 3
            }
        ]
    
    def route(self, query: str, user_tier: str = "free") -> str:
        # Check user tier for rate limits
        max_model = self.get_max_model_for_tier(user_tier)
        
        # Find best matching rule
        for rule in sorted(self.routing_rules, key=lambda r: r["priority"]):
            if rule["condition"](query):
                return self.choose_model(rule["model"], max_model)
        
        return "gpt-3.5-turbo"  # Default fallback
    
    def is_simple_fact(self, query: str) -> bool:
        # Check for simple question patterns
        simple_patterns = ["what is", "who is", "when did", "where is"]
        return any(query.lower().startswith(p) for p in simple_patterns)
    
    def is_code_request(self, query: str) -> bool:
        code_indicators = ["write code", "function", "class", "implement"]
        return any(indicator in query.lower() for indicator in code_indicators)
    
    def is_complex(self, query: str) -> bool:
        # Check for complexity indicators
        complex_indicators = ["analyze", "compare", "design", "explain in detail"]
        return any(indicator in query.lower() for indicator in complex_indicators)
```

### Component 2: Circuit Breaker

```python
import asyncio
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_recovery(self) -> bool:
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### Component 3: Load Balancer for LLM

```python
class LoadBalancer:
    """
    Load balancer for multiple LLM model instances
    """
    
    def __init__(self, strategy: str = "weighted_round_robin"):
        self.strategy = strategy
        self.instances = []
        self.current_index = 0
        self.instance_stats = {}  # Track per-instance stats
    
    def add_instance(self, instance_id: str, weight: int = 1, max_tokens: int = 1000):
        self.instances.append({
            "id": instance_id,
            "weight": weight,
            "max_tokens": max_tokens,
            "current_load": 0
        })
        self.instance_stats[instance_id] = {
            "requests": 0,
            "errors": 0,
            "total_latency": 0
        }
    
    def select_instance(self, required_tokens: int = None) -> dict:
        if self.strategy == "weighted_round_robin":
            return self._weighted_round_robin(required_tokens)
        elif self.strategy == "least_loaded":
            return self._least_loaded(required_tokens)
        elif self.strategy == "latency_based":
            return self._latency_based(required_tokens)
        else:
            return self.instances[0]
    
    def _weighted_round_robin(self, required_tokens: int = None) -> dict:
        # Skip weights to implement round-robin within weight
        selected = self.instances[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.instances)
        return selected
    
    def _least_loaded(self, required_tokens: int = None) -> dict:
        # Filter by token capacity if needed
        candidates = self.instances
        if required_tokens:
            candidates = [i for i in candidates if i["max_tokens"] >= required_tokens]
        
        # Select least loaded
        return min(candidates, key=lambda x: x["current_load"])
    
    def _latency_based(self, required_tokens: int = None) -> dict:
        # Select instance with lowest average latency
        instance_latencies = {
            i["id"]: (
                self.instance_stats[i["id"]]["total_latency"] / 
                max(self.instance_stats[i["id"]]["requests"], 1)
            )
            for i in self.instances
        }
        best_id = min(instance_latencies, key=instance_latencies.get)
        return next(i for i in self.instances if i["id"] == best_id)
```

---

## Scaling Strategies

### Horizontal Scaling with Kubernetes

```yaml
# Kubernetes deployment for LLM inference
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference
  labels:
    app: llm-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-inference
  template:
    metadata:
      labels:
        app: llm-inference
    spec:
      containers:
      - name: inference
        image: your-registry/vllm:latest
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "32Gi"
            cpu: "8"
          limits:
            nvidia.com/gpu: 1
            memory: "64Gi"
            cpu: "16"
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-2-70b-hf"
        - name: TENSOR_PARALLEL_SIZE
          value: "2"
        - name: MAX_NUM_BATCHED_TOKENS
          value: "8192"
---
apiVersion: v1
kind: Service
metadata:
  name: llm-inference-service
spec:
  selector:
    app: llm-inference
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-inference
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "50"
```

### Vertical Scaling Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│               Vertical Scaling Strategy                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Model Size    VRAM Required    Recommended GPU                │
│  ─────────────────────────────────────────────────────────────  │
│  7B            ~14 GB           A10G, T4, L4                   │
│  13B           ~26 GB           A100 40GB, A30                │
│  34B           ~68 GB           A100 80GB x2                  │
│  70B           ~140 GB          A100 80GB x4                  │
│                                                                  │
│  Key Considerations:                                            │
│  ─────────────────────────────────────────────────────────────  │
│  • Quantization can reduce VRAM by 2-4x                        │
│  • Tensor parallelism splits large models across GPUs         │
│  • Pipeline parallelism reduces communication overhead         │
│  • Consider inference frameworks (vLLM, TGI) for optimization  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failure Handling

### Retry Strategy with Exponential Backoff

```python
class RetryStrategy:
    """
    Comprehensive retry strategy for LLM calls
    """
    
    def __init__(self):
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0,
            "jitter": True
        }
        
        # Retryable errors
        self.retryable_errors = {
            "rate_limit_exceeded": True,
            "service_unavailable": True,
            "timeout": True,
            "internal_error": True,
            "network_error": True
        }
        
        # Non-retryable errors
        self.non_retryable_errors = {
            "invalid_request_error": True,
            "authentication_error": True,
            "permission_error": True,
            "content_filter": True
        }
    
    async def execute_with_retry(self, func, *args, **kwargs):
        last_exception = None
        
        for attempt in range(self.retry_config["max_retries"]):
            try:
                return await func(*args, **kwargs)
                
            except Exception as e:
                error_type = self._classify_error(e)
                last_exception = e
                
                if error_type in self.non_retryable_errors:
                    raise
                
                if error_type in self.retryable_errors:
                    delay = self._calculate_delay(attempt)
                    print(f"Retry {attempt + 1} after {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                
                raise
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        delay = self.retry_config["base_delay"] * (
            self.retry_config["exponential_base"] ** attempt
        )
        
        # Cap at max delay
        delay = min(delay, self.retry_config["max_delay"])
        
        # Add jitter
        if self.retry_config["jitter"]:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay
```

### Fallback Chain

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fallback Chain                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Request                                                        │
│      │                                                           │
│      ▼                                                           │
│   ┌───────────┐                                                  │
│   │ Primary   │  gpt-4                                          │
│   │ Model     │  ─────────▶ Success ──▶ Response              │
│   │ (gpt-4)  │  │                                                │
│   └─────┬─────┘  │                                                │
│         │ Failed │                                                │
│         ▼        │                                                │
│   ┌───────────┐  │                                                │
│   │ Fallback 1│  │ gpt-3.5-turbo                                 │
│   │ (gpt-3.5) │  ─────────▶ Success ──▶ Response                │
│   └─────┬─────┘  │                                                │
│         │ Failed │                                                │
│         ▼        │                                                │
│   ┌───────────┐  │                                                │
│   │ Fallback 2│  │ claude-3-sonnet                              │
│   │ (Claude)  │  ─────────▶ Success ──▶ Response                │
│   └─────┬─────┘  │                                                │
│         │ Failed │                                                │
│         ▼        │                                                │
│   ┌───────────┐  │                                                │
│   │ Fallback 3│  │ cached response                              │
│   │ (Cache)   │  ─────────▶ Success ──▶ Response              │
│   └─────┬─────┘  │                                                │
│         │ Failed │                                                │
│         ▼        │                                                │
│      Error ◀─────┘                                                │
│                                                                  │
│   All fallbacks exhausted - Return error with context           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### API Key Management

```python
# Secure API key handling
import os
from cryptography.fernet import Fernet

class SecureKeyManager:
    """
    Secure management of API keys
    """
    
    def __init__(self):
        # Load encryption key from secure vault
        self.encryption_key = self._load_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def get_key(self, provider: str) -> str:
        # 1. Check environment variable
        key = os.environ.get(f"{provider.upper()}_API_KEY")
        if key:
            return key
        
        # 2. Check secure vault (HashiCorp Vault, AWS Secrets Manager, etc.)
        key = self._get_from_vault(provider)
        if key:
            return key
        
        raise MissingAPIKeyError(f"No API key found for {provider}")
    
    def _encrypt_key(self, key: str) -> bytes:
        return self.cipher.encrypt(key.encode())
    
    def _decrypt_key(self, encrypted_key: bytes) -> str:
        return self.cipher.decrypt(encrypted_key).decode()
```

### Input/Output Filtering

```
┌─────────────────────────────────────────────────────────────────┐
│                  Input/Output Security Pipeline                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Input ──────────────────────────────────────────────▶    │
│                                                                    │
│   ┌─────────────┐                                               │
│   │  Input      │   1. Validate format                          │
│   │  Validator  │   2. Check length                             │
│   │             │   3. Sanitize special chars                   │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────┐                                               │
│   │  Prompt     │   1. Check for injection patterns            │
│   │  Injector   │   2. Escape user content                      │
│   │  Defense    │   3. Separate contexts                        │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│        [LLM Processing]                                          │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────┐                                               │
│   │  Output     │   1. Validate response format                │
│   │  Validator  │   2. Filter sensitive data                   │
│   │             │   3. Check for leaks                          │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   Safe Response ◀─────────────────────────────────────────     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Optimization Architecture

### Token Budget Management

```python
class TokenBudgetManager:
    """
    Manage token budgets for cost control
    """
    
    def __init__(self, daily_budget_usd: float):
        self.daily_budget_usd = daily_budget_usd
        self.today_spend = 0
        self.today_tokens = 0
        self._reset_if_new_day()
    
    def _reset_if_new_day(self):
        today = datetime.now().date()
        if hasattr(self, 'last_date') and self.last_date != today:
            self.today_spend = 0
            self.today_tokens = 0
        self.last_date = today
    
    async def check_budget(self, estimated_tokens: int) -> bool:
        """Check if request fits within budget"""
        self._reset_if_new_day()
        
        estimated_cost = self._estimate_cost(estimated_tokens)
        remaining = self.daily_budget_usd - self.today_spend
        
        return estimated_cost <= remaining
    
    async def record_usage(self, input_tokens: int, output_tokens: int):
        """Record actual token usage"""
        cost = self._calculate_cost(input_tokens, output_tokens)
        self.today_spend += cost
        self.today_tokens += input_tokens + output_tokens
    
    def _estimate_cost(self, tokens: int) -> float:
        # Estimate based on average cost per token
        avg_cost_per_token = 0.00001  # Approximate
        return tokens * avg_cost_per_token
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Actual pricing (example)
        input_cost = (input_tokens / 1000) * 0.03  # gpt-4 pricing
        output_cost = (output_tokens / 1000) * 0.06
        return input_cost + output_cost
```

### Caching Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Level Caching                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Request ───────────────────────────────────────────────────▶   │
│                                                                    │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │                    L1: In-Memory Cache                       │ │
│   │                    (Redis Cluster)                          │ │
│   │                                                            │ │
│   │  Check: Exact match, similarity > 0.95                      │ │
│   │  TTL: 1 hour                                               │ │
│   │  Hit Rate Target: 30-50%                                   │ │
│   └──────────────────────────┬──────────────────────────────────┘ │
│                              │ Miss                                │
│                              ▼                                     │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │                    L2: Semantic Cache                        │ │
│   │                    (Vector Store)                           │ │
│   │                                                            │ │
│   │  Check: Similarity > 0.85                                  │ │
│   │  TTL: 24 hours                                             │ │
│   │  Hit Rate Target: 20-30%                                    │ │
│   └──────────────────────────┬──────────────────────────────────┘ │
│                              │ Miss                                │
│                              ▼                                     │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │                    L3: API Provider Cache                    │ │
│   │                    (Provider's cache)                       │ │
│   │                                                            │ │
│   │  Check: Same prompt within window                          │ │
│   │  TTL: Provider-defined                                      │ │
│   └──────────────────────────┬──────────────────────────────────┘ │
│                              │ Miss                                │
│                              ▼                                     │
│                        [LLM Call]                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

Key system design patterns covered:

1. **Three Architecture Patterns**: API-based, Self-hosted, Hybrid
2. **Component Deep Dives**: Router, Circuit Breaker, Load Balancer
3. **Scaling Strategies**: Horizontal (K8s), Vertical (GPU)
4. **Failure Handling**: Retry logic, Fallback chains
5. **Security**: Key management, Input/Output filtering
6. **Cost Optimization**: Budget management, Multi-level caching
