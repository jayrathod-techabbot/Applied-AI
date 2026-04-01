# Module 12: Deployment Strategies — Core Concepts

---

## Table of Contents

- [12.1 Deployment Overview](#121-deployment-overview)
  - [Containerization for LLM Applications](#containerization-for-llm-applications)
  - [Kubernetes Fundamentals](#kubernetes-fundamentals)
  - [Serverless Deployment](#serverless-deployment)
  - [API Design for LLM Applications](#api-design-for-llm-applications)
- [12.2 Deployment Techniques and Patterns](#122-deployment-techniques-and-patterns)
  - [Model Serving Frameworks](#model-serving-frameworks)
  - [GPU Optimization](#gpu-optimization)
  - [Auto-Scaling Strategies](#auto-scaling-strategies)
  - [Health Checks and Monitoring](#health-checks-and-monitoring)
  - [Deployment Patterns](#deployment-patterns)
  - [Cost Optimization](#cost-optimization)
- [12.3 Azure-Based Deployment with Container Apps](#123-azure-based-deployment-with-container-apps)
  - [Azure Container Apps](#azure-container-apps)
  - [Azure API Management](#azure-api-management)
  - [End-to-End Azure Deployment](#end-to-end-azure-deployment)
- [Key Takeaways](#key-takeaways)

---

## 12.1 Deployment Overview

### Containerization for LLM Applications

Containerization packages an LLM application with all its dependencies, configurations, and model artifacts into a portable, reproducible unit. Docker is the de facto standard.

#### Why Containers for LLM Apps?

| Benefit | Description |
|---------|-------------|
| **Reproducibility** | Identical environments across dev, staging, and production |
| **Isolation** | Model dependencies don't conflict with host or other services |
| **Portability** | Run on any container runtime (Docker, Podman, containerd) |
| **Scalability** | Orchestrate with Kubernetes, ECS, or Container Apps |
| **Version Control** | Tag images to track model and code versions |

#### Dockerfile for a vLLM-Served LLM

```dockerfile
# ---------- Stage 1: Build ----------
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y python3 python3-pip git && \
    pip install --upgrade pip

WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
WORKDIR /app

COPY src/ ./src/
COPY config/ ./config/

# Pre-download model during build (optional — trade image size for faster cold start)
# RUN python3 src/download_model.py --model meta-llama/Llama-3-8B-Instruct

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
CMD ["--model", "meta-llama/Llama-3-8B-Instruct", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--dtype", "auto", \
     "--max-model-len", "8192"]
```

#### Multi-Stage Build Benefits for LLM Images

```
Image Size Comparison (approximate):
┌──────────────────────────────┬────────────┐
│ Approach                     │ Size       │
├──────────────────────────────┼────────────┤
│ Single-stage (dev tools)     │ ~12 GB     │
│ Multi-stage (runtime only)   │ ~6 GB      │
│ Multi-stage + distroless     │ ~5 GB      │
│ Distroless + model baked in  │ ~20 GB+    │
└──────────────────────────────┴────────────┘
```

#### Docker Compose for Local Development

```yaml
# docker-compose.yml
version: "3.9"

services:
  llm-server:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - model-cache:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - HF_TOKEN=${HF_TOKEN}

  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - llm-server

volumes:
  model-cache:
```

---

### Kubernetes Fundamentals

Kubernetes (K8s) orchestrates containers at scale. For LLM deployments it manages GPU scheduling, rolling updates, and service discovery.

#### Core Concepts

| Concept | Description | LLM Relevance |
|---------|-------------|---------------|
| **Pod** | Smallest deployable unit; one or more containers | Runs a single model server instance |
| **Service** | Stable network endpoint for pods | Exposes model API behind a ClusterIP or LoadBalancer |
| **Deployment** | Declarative pod management | Ensures desired replica count, handles updates |
| **ConfigMap / Secret** | Externalized config and credentials | Store model names, API keys, HuggingFace tokens |
| **HorizontalPodAutoscaler** | Auto-scale pods on metrics | Scale replicas on GPU utilization or request queue depth |
| **Node Pool / Node Group** | Group of VMs with specific hardware | GPU node pool (e.g., Standard_NC6s_v3) |

#### Kubernetes Deployment Manifest

```yaml
# llm-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-server
  labels:
    app: llm-server
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-server
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: llm-server
        version: v1
    spec:
      containers:
        - name: vllm
          image: myregistry.azurecr.io/llm-server:v1.2.0
          ports:
            - containerPort: 8000
              protocol: TCP
          env:
            - name: MODEL_NAME
              value: "meta-llama/Llama-3-8B-Instruct"
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-credentials
                  key: token
          resources:
            requests:
              cpu: "4"
              memory: "16Gi"
              nvidia.com/gpu: "1"
            limits:
              cpu: "8"
              memory: "32Gi"
              nvidia.com/gpu: "1"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 60
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 120
            periodSeconds: 30
            failureThreshold: 5
      nodeSelector:
        accelerator: nvidia-tesla-a100
      tolerations:
        - key: "nvidia.com/gpu"
          operator: "Exists"
          effect: "NoSchedule"
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service
spec:
  selector:
    app: llm-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

#### HPA for LLM Pods

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-server
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
          name: gpu_utilization
        target:
          type: AverageValue
          averageValue: "80"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 120
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

---

### Serverless Deployment

Serverless abstracts infrastructure management. You pay per invocation or provisioned capacity rather than per VM.

#### Serverless Options Comparison

| Platform | Max Timeout | GPU Support | Cold Start | Best For |
|----------|-------------|-------------|------------|----------|
| **Azure Functions** | 230 s | No (CPU only) | Moderate | Lightweight preprocessing, orchestration |
| **AWS Lambda** | 15 min | No | Moderate | Event-driven pipelines |
| **Azure Container Apps** | None | Yes (preview) | Low | LLM serving with scale-to-zero |
| **AWS Bedrock** | N/A | Managed | Low | Managed foundation model API |
| **Google Cloud Run** | 60 min | Yes (L4, T4) | Low | Containerized LLM APIs |
| **Modal** | 24 hrs | Yes (A100) | Low (warm pool) | GPU-heavy ML workloads |

#### Azure Functions Example (Orchestration Layer)

```python
# function_app.py — Azure Functions (Python v2)
import azure.functions as func
import httpx
import json

app = func.FunctionApp()

@app.route(route="generate", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def generate(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    prompt = body.get("prompt", "")
    max_tokens = body.get("max_tokens", 256)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://llm-server.internal:8000/v1/completions",
            json={
                "model": "meta-llama/Llama-3-8B-Instruct",
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
        )

    return func.HttpResponse(
        json.dumps(response.json()),
        mimetype="application/json",
        status_code=200,
    )
```

---

### API Design for LLM Applications

#### REST Endpoint Design

```python
# src/api/routes.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from sse_starlette.sse import EventSourceResponse
import asyncio

app = FastAPI(title="LLM Inference API", version="2.0.0")

class CompletionRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32000)
    max_tokens: int = Field(default=256, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stop: Optional[List[str]] = None

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    result = await model.generate(
        prompt=request.prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        stop=request.stop,
    )
    return {
        "id": result.request_id,
        "object": "text_completion",
        "choices": [{"text": result.text, "index": 0, "finish_reason": result.finish_reason}],
        "usage": {
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
        },
    }

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatRequest):
    if request.stream:
        return EventSourceResponse(chat_stream(request))
    result = await model.chat(messages=request.messages, **request.model_dump(exclude={"stream"}))
    return format_chat_response(result)

async def chat_stream(request: ChatRequest):
    async for chunk in model.chat_stream(messages=request.messages, max_tokens=request.max_tokens):
        yield {
            "data": json.dumps({
                "choices": [{"delta": {"content": chunk.text}}],
            })
        }
    yield {"data": "[DONE]"}

@app.get("/health")
async def health():
    if not model.is_ready():
        raise HTTPException(status_code=503, detail="Model loading")
    return {"status": "healthy"}
```

#### Streaming with Server-Sent Events (SSE)

```
Client                         Server
  │                              │
  │── POST /v1/chat/completions─▶│
  │   { "stream": true }         │
  │                              │
  │◀── data: {"choices":[{"      │
  │       delta":{"content":"The"}}]}  │
  │                              │
  │◀── data: {"choices":[{"      │
  │       delta":{"content":" answer"}}]}  │
  │                              │
  │◀── data: [DONE]              │
  │                              │
```

#### WebSocket for Bidirectional Streaming

```python
# src/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, client_id: str):
        await ws.accept()
        self.active[client_id] = ws

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)

manager = ConnectionManager()

@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(ws: WebSocket, client_id: str):
    await manager.connect(ws, client_id)
    try:
        while True:
            data = await ws.receive_json()
            messages = data.get("messages", [])

            async for chunk in model.chat_stream(messages=messages):
                await ws.send_json({
                    "type": "token",
                    "content": chunk.text,
                })

            await ws.send_json({"type": "done"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

---

## 12.2 Deployment Techniques and Patterns

### Model Serving Frameworks

| Framework | Protocol | Quantization | Continuous Batching | Multi-GPU | License |
|-----------|----------|-------------|--------------------|-----------|---------|
| **vLLM** | OpenAI-compatible | AWQ, GPTQ, FP8 | Yes (PagedAttention) | Tensor parallel | Apache 2.0 |
| **TGI** (Text Generation Inference) | OpenAI-compatible | GPTQ, AWQ, EETQ | Yes | Tensor parallel | Apache 2.0 |
| **TensorRT-LLM** | Triton / custom | INT8, INT4, FP8 | Yes | Tensor + pipeline | Apache 2.0 |
| **Ollama** | REST | GGUF (llama.cpp) | Limited | No | MIT |
| **LMDeploy** | OpenAI-compatible | W4A16, KV cache | Yes | Tensor parallel | Apache 2.0 |

#### vLLM Launch Configuration

```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --tensor-parallel-size 4 \
    --dtype auto \
    --quantization awq \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.90 \
    --enable-prefix-caching \
    --host 0.0.0.0 \
    --port 8000
```

#### TGI Launch Configuration

```bash
text-generation-launcher \
    --model-id meta-llama/Llama-3-70B-Instruct \
    --num-shard 4 \
    --quantize awq \
    --max-input-length 3072 \
    --max-total-tokens 4096 \
    --max-batch-prefill-tokens 6144 \
    --max-batch-total-tokens 32768 \
    --hostname 0.0.0.0 \
    --port 8000
```

---

### GPU Optimization

#### GPU Memory Breakdown for a 70B Model

```
┌─────────────────────────────────────────────────┐
│              GPU VRAM (80 GB A100)              │
├─────────────────────────────────────────────────┤
│  Model Weights (FP16)     │  ~140 GB  ✗ too big│
│  Model Weights (INT4 AWQ) │  ~35 GB   ✓        │
│  KV Cache (4K ctx, batch=8)│ ~20 GB   ✓        │
│  Activations / Overhead   │  ~5 GB    ✓        │
│  Reserved / Fragmentation │  ~20 GB   ✓        │
├─────────────────────────────────────────────────┤
│  Total                    │  ~80 GB             │
└─────────────────────────────────────────────────┘
```

#### Key Optimization Techniques

| Technique | Impact | Trade-off |
|-----------|--------|-----------|
| **Quantization (AWQ/GPTQ)** | 2-4x memory reduction | Minor quality loss (~1%) |
| **PagedAttention (vLLM)** | Near-zero KV cache waste | Slight overhead |
| **Prefix Caching** | Faster repeated prompts | Memory for cache |
| **Speculative Decoding** | 1.5-2x throughput gain | Extra draft model memory |
| **Continuous Batching** | Max GPU utilization | Slightly higher latency variance |
| **KV Cache Quantization (FP8)** | 2x KV cache capacity | Minimal quality impact |

#### Python: Benchmarking Inference

```python
# benchmarks/throughput_test.py
import asyncio
import time
import httpx

CONCURRENCY = 32
REQUESTS = 500
API_URL = "http://localhost:8000/v1/completions"

payload = {
    "model": "meta-llama/Llama-3-8B-Instruct",
    "prompt": "Explain the theory of relativity in three paragraphs.",
    "max_tokens": 256,
    "temperature": 0.7,
}

async def send_request(client: httpx.AsyncClient, sem: asyncio.Semaphore):
    async with sem:
        start = time.perf_counter()
        resp = await client.post(API_URL, json=payload, timeout=120)
        elapsed = time.perf_counter() - start
        data = resp.json()
        tokens = data["usage"]["completion_tokens"]
        return elapsed, tokens

async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, sem) for _ in range(REQUESTS)]
        results = await asyncio.gather(*tasks)

    latencies = [r[0] for r in results]
    total_tokens = sum(r[1] for r in results)
    total_time = max(latencies)

    print(f"Total requests:   {REQUESTS}")
    print(f"Total tokens:     {total_tokens}")
    print(f"Throughput:       {total_tokens / total_time:.1f} tokens/s")
    print(f"Avg latency:      {sum(latencies)/len(latencies):.2f} s")
    print(f"P95 latency:      {sorted(latencies)[int(0.95*len(latencies))]:.2f} s")
    print(f"P99 latency:      {sorted(latencies)[int(0.99*len(latencies))]:.2f} s")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Auto-Scaling Strategies

#### Scaling Decision Matrix

| Signal | Source | Scale-Up Trigger | Scale-Down Trigger |
|--------|--------|-------------------|-------------------|
| **GPU Utilization** | DCGM exporter | > 80% for 2 min | < 30% for 10 min |
| **Request Queue Depth** | App metrics | > 50 pending | < 5 pending |
| **Token Latency (TTFT)** | App metrics | > 2 s | < 500 ms |
| **Throughput** | App metrics | < 100 tok/s | > 500 tok/s |
| **Concurrent Requests** | App metrics | > 80% capacity | < 20% capacity |

#### Custom Metrics Adapter for K8s HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-queue-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-server
  minReplicas: 1
  maxReplicas: 8
  metrics:
    - type: External
      external:
        metric:
          name: vllm_pending_requests
          selector:
            matchLabels:
              model: llama-3-8b
        target:
          type: AverageValue
          averageValue: "20"
```

---

### Health Checks

Health checks ensure reliability by detecting unhealthy pods and routing traffic only to ready instances.

```
Health Check Flow:
                  ┌──────────────┐
  Request ───────▶│ Load Balancer│
                  └──────┬───────┘
                         │ (only healthy backends)
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Pod A    │  │ Pod B    │  │ Pod C    │
    │ /health  │  │ /health  │  │ /health  │
    │ ✓ 200    │  │ ✓ 200    │  │ ✗ 503    │
    └──────────┘  └──────────┘  └──────────┘
      (serving)     (serving)    (draining)
```

#### Health Check Endpoints

```python
# src/api/health.py
import time
from enum import Enum

class ServerStatus(str, Enum):
    LOADING = "loading"
    READY = "ready"
    DRAINING = "draining"
    ERROR = "error"

class HealthChecker:
    def __init__(self):
        self.status = ServerStatus.LOADING
        self.model_loaded_at: float | None = None
        self.error_message: str | None = None

    def mark_ready(self):
        self.status = ServerStatus.READY
        self.model_loaded_at = time.time()

    def mark_draining(self):
        self.status = ServerStatus.DRAINING

    def mark_error(self, msg: str):
        self.status = ServerStatus.ERROR
        self.error_message = msg

    def check(self) -> tuple[int, dict]:
        if self.status == ServerStatus.READY:
            return 200, {"status": "healthy", "uptime_s": time.time() - self.model_loaded_at}
        elif self.status == ServerStatus.LOADING:
            return 503, {"status": "loading"}
        elif self.status == ServerStatus.DRAINING:
            return 503, {"status": "draining"}
        else:
            return 500, {"status": "error", "detail": self.error_message}
```

---

### Deployment Patterns

#### Blue-Green Deployment

```
                        ┌──────────────────┐
                        │   Load Balancer  │
                        └────────┬─────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
           ┌─────────────┐              ┌─────────────┐
           │  BLUE (v1)  │              │ GREEN (v2)  │
           │  Llama-3-8B │              │ Llama-3-8B  │
           │  3 replicas │              │ 3 replicas  │
           │  ACTIVE ✓   │              │ STANDBY     │
           └─────────────┘              └─────────────┘

  Step 1: Deploy GREEN (v2) alongside BLUE (v1)
  Step 2: Run smoke tests on GREEN
  Step 3: Switch LB to GREEN
  Step 4: Drain and decommission BLUE
```

| Aspect | Blue-Green | Canary | Rolling |
|--------|-----------|--------|---------|
| **Downtime** | Zero | Zero | Zero |
| **Risk** | Low (instant rollback) | Lowest (gradual) | Moderate |
| **Resource Cost** | 2x during switch | 1x + canary | 1x + surge |
| **Rollback Speed** | Instant (switch LB) | Instant (shift traffic) | Slower (roll back pods) |
| **Complexity** | Low | Medium | Low |
| **Best For** | Critical models | Risk-averse releases | Standard updates |

#### Canary Deployment with Istio

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: llm-vs
spec:
  hosts:
    - llm-service
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: llm-service
            subset: v2
    - route:
        - destination:
            host: llm-service
            subset: v1
          weight: 90
        - destination:
            host: llm-service
            subset: v2
          weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: llm-dr
spec:
  host: llm-service
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
```

---

### Cost Optimization

#### Cost Comparison: LLM Hosting Options

| Option | 70B Model (8×A100) | Monthly Cost (est.) | Pros | Cons |
|--------|--------------------|--------------------|------|------|
| **Dedicated VMs** | ND96amsr_A100_v4 | ~$27,000/mo | Full control, predictable | Always-on cost |
| **Spot/Preemptible** | ND96amsr spot | ~$9,000/mo | 60-70% savings | Can be evicted |
| **Azure Container Apps** | Per-replica GPU | ~$6,000-15,000/mo | Scale-to-zero, managed | GPU preview |
| **Managed API (OpenAI)** | GPT-4o pricing | Variable | Zero ops | Per-token cost |
| **Quantized on fewer GPUs** | 2×A100 (INT4) | ~$7,000/mo | Lower hardware | Quality trade-off |

#### Optimization Strategies

```python
# config/cost_policy.yaml
scaling:
  scale_to_zero:
    enabled: true
    idle_timeout_seconds: 300    # 5 min idle → scale to 0
    min_replicas: 0
    max_replicas: 6

  schedule:
    # Scale up during business hours
    - cron: "0 8 * * 1-5"
      min_replicas: 2
    - cron: "0 20 * * 1-5"
      min_replicas: 0

spot_instances:
  enabled: true
  max_spot_percentage: 70        # 70% spot, 30% on-demand
  eviction_policy: "checkpoint"  # Save KV cache before eviction
```

---

## 12.3 Azure-Based Deployment with Container Apps

### Azure Container Apps

Azure Container Apps (ACA) provides a managed, serverless container platform with built-in Dapr integration, KEDA-based scaling, and environment-level networking.

#### ACA Feature Matrix for LLM Workloads

| Feature | Support | Notes |
|---------|---------|-------|
| GPU containers | Preview (NVIDIA T4, A100) | Request GPU-enabled environment |
| Scale to zero | Yes (KEDA) | HTTP + custom scaler |
| Ingress | HTTP, TCP, gRPC | Built-in TLS |
| Revisions | Yes | Traffic splitting for canary |
| Dapr integration | Yes | Service-to-service, pub/sub |
| Managed identity | Yes | Access Key Vault, ACR, Storage |
| VNet integration | Yes | Private endpoints for DB, KV |
| Max request timeout | 24 hours | Suitable for long generations |

#### Deploy with Azure CLI

```bash
# 1. Create resource group
az group create --name rg-llm-prod --location eastus

# 2. Create Container App Environment with GPU
az containerapp env create \
    --name llm-environment \
    --resource-group rg-llm-prod \
    --location eastus \
    --infrastructure "gpu"  # GPU-enabled environment

# 3. Create Container App
az containerapp create \
    --name llm-server \
    --resource-group rg-llm-prod \
    --environment llm-environment \
    --image myregistry.azurecr.io/llm-server:v1.2.0 \
    --target-port 8000 \
    --ingress external \
    --min-replicas 0 \
    --max-replicas 5 \
    --cpu 4 \
    --memory 16Gi \
    --env-vars \
        "MODEL_NAME=meta-llama/Llama-3-8B-Instruct" \
        "HF_TOKEN=secretref:hf-token" \
    --secrets \
        "hf-token=keyvault:https://my-kv.vault.azure.net/secrets/HF-Token"

# 4. Configure autoscaler
az containerapp update \
    --name llm-server \
    --resource-group rg-llm-prod \
    --scale-rule-name "http-rule" \
    --scale-rule-type "http" \
    --scale-rule-http-concurrency 10 \
    --scale-rule-metadata "concurrentRequests=10"
```

#### Bicep Infrastructure as Code

```bicep
// infra/main.bicep
param location string = resourceGroup().location
param environmentName string = 'llm-environment'
param appName string = 'llm-server'
param acrName string = 'myregistry'
param imageName string = 'llm-server:v1.2.0'

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource llmApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: managedIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'vllm'
          image: '${acr.properties.loginServer}/${imageName}'
          resources: {
            cpu: 4
            memory: '16Gi'
          }
          env: [
            { name: 'MODEL_NAME', value: 'meta-llama/Llama-3-8B-Instruct' }
          ]
          probes: [
            {
              type: 'liveness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 120
              periodSeconds: 30
            }
            {
              type: 'readiness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 60
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 5
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: { concurrentRequests: '10' }
            }
          }
        ]
      }
    }
  }
}
```

---

### Azure API Management

Azure API Management (APIM) sits in front of your LLM endpoint to provide authentication, rate limiting, response caching, and observability.

#### APIM Policy for LLM Gateway

```xml
<!-- APIM Inbound Policy -->
<policies>
    <inbound>
        <base />
        <!-- Validate API key -->
        <validate-header
            header-name="Authorization"
            failed-validation-httpcode="401"
            failed-validation-error-message="Invalid API key" />

        <!-- Rate limiting: 100 req/min per subscription -->
        <rate-limit-by-key
            calls="100"
            renewal-period="60"
            counter-key="@(context.Subscription.Id)" />

        <!-- Token budget: track via custom header -->
        <set-header name="x-request-id" exists-action="override">
            <value>@(Guid.NewGuid().ToString())</value>
        </set-header>

        <!-- Route to backend -->
        <set-backend-service
            base-url="https://llm-server.internal:8000" />
    </inbound>

    <backend>
        <base />
        <forward-request timeout="120" />
    </backend>

    <outbound>
        <base />
        <!-- Cache non-streaming responses for 60s -->
        <cache-store
            duration="60"
            vary-by-header="Authorization" />
    </outbound>
</policies>
```

#### APIM Architecture

```
                    ┌─────────────────────────────────────────┐
                    │            Azure API Management         │
                    │  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
  Clients ────────▶│  │Auth/RBAC │ │Rate Limit│ │ Caching │ │
                    │  └────┬─────┘ └────┬─────┘ └────┬────┘ │
                    │       └────────────┼────────────┘      │
                    └────────────────────┼───────────────────┘
                                         │
                    ┌────────────────────┼───────────────────┐
                    │  Azure Container Apps (Internal)       │
                    │       │              │             │    │
                    │  ┌────▼────┐   ┌────▼────┐  ┌────▼──┐ │
                    │  │LLM v1  │   │LLM v2  │  │Embed  │ │
                    │  │(90%)   │   │(10%)   │  │       │ │
                    │  └─────────┘   └─────────┘  └───────┘ │
                    └────────────────────────────────────────┘
```

---

### End-to-End Azure Deployment

#### Full Pipeline: Code → Container → Production

```bash
# 1. Build and push image
az acr build \
    --registry myregistry \
    --image llm-server:v1.2.0 \
    --file Dockerfile .

# 2. Deploy to Container Apps
az containerapp update \
    --name llm-server \
    --resource-group rg-llm-prod \
    --image myregistry.azurecr.io/llm-server:v1.2.0

# 3. Verify deployment
az containerapp revision list \
    --name llm-server \
    --resource-group rg-llm-prod \
    --output table

# 4. Run smoke test
curl -X POST https://llm-server.<region>.azurecontainerapps.io/v1/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{
        "prompt": "Hello, world!",
        "max_tokens": 50
    }'
```

#### CI/CD with GitHub Actions

```yaml
# .github/workflows/deploy-llm.yml
name: Build & Deploy LLM Server

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'Dockerfile'
      - 'requirements.txt'

env:
  ACR_NAME: myregistry
  APP_NAME: llm-server
  RESOURCE_GROUP: rg-llm-prod

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Build & Push Image
        run: |
          az acr build \
            --registry ${{ env.ACR_NAME }} \
            --image ${{ env.APP_NAME }}:${{ github.sha }} \
            --file Dockerfile .

      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name ${{ env.APP_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.ACR_NAME }}.azurecr.io/${{ env.APP_NAME }}:${{ github.sha }}

      - name: Health Check
        run: |
          sleep 30
          ENDPOINT=$(az containerapp show \
            --name ${{ env.APP_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --query "properties.configuration.ingress.fqdn" -o tsv)
          curl -sf "https://${ENDPOINT}/health" || exit 1
```

---

## Key Takeaways

| # | Concept | Summary |
|---|---------|---------|
| 1 | **Containerize everything** | Docker + multi-stage builds keep images lean and reproducible |
| 2 | **Choose the right orchestrator** | K8s for full control, Azure Container Apps for managed simplicity |
| 3 | **Use GPU-optimized serving** | vLLM or TGI with PagedAttention and continuous batching maximize throughput |
| 4 | **Quantize for production** | AWQ/GPTQ INT4 cuts VRAM 2-4x with minimal quality loss |
| 5 | **Design APIs for streaming** | SSE and WebSocket reduce perceived latency for generative outputs |
| 6 | **Health checks are mandatory** | Liveness + readiness probes prevent cascading failures |
| 7 | **Use progressive rollouts** | Blue-green for instant rollback, canary for risk mitigation |
| 8 | **Scale on the right signals** | GPU utilization, queue depth, and TTFT are better than CPU alone |
| 9 | **APIM as a gateway** | Centralize auth, rate limiting, and caching at the API layer |
| 10 | **Automate with CI/CD** | Every commit should build, test, and deploy through a pipeline |

---

*End of Module 12 — Deployment Strategies*
