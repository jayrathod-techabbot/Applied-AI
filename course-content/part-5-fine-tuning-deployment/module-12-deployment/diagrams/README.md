# Module 12: Deployment Strategies — Diagrams

---

## 1. End-to-End Deployment Architecture

### ASCII Diagram

```
                              ┌──────────────────────────────────────────────────┐
                              │                  INTERNET                        │
                              └──────────────────────┬───────────────────────────┘
                                                     │
                              ┌──────────────────────▼───────────────────────────┐
                              │              Azure Front Door / CDN              │
                              │         (TLS termination, WAF, caching)          │
                              └──────────────────────┬───────────────────────────┘
                                                     │
                              ┌──────────────────────▼───────────────────────────┐
                              │              Azure API Management                │
                              │  ┌──────────┐  ┌────────────┐  ┌────────────┐   │
                              │  │   Auth   │  │Rate Limiter│  │  Response  │   │
                              │  │ (API Key)│  │(100 req/m) │  │   Cache    │   │
                              │  └─────┬────┘  └─────┬──────┘  └─────┬──────┘   │
                              │        └─────────────┼───────────────┘          │
                              └──────────────────────┬───────────────────────────┘
                                                     │
                         ┌───────────────────────────┼───────────────────────────┐
                         │    Azure Container Apps Environment (VNet)           │
                         │                           │                           │
                         │   ┌───────────────────────┼───────────────────┐       │
                         │   │                       ▼                   │       │
                         │   │            ┌──────────────────┐           │       │
                         │   │            │   Request Router │           │       │
                         │   │            │   (Dapr sidecar) │           │       │
                         │   │            └──┬─────┬─────┬──┘           │       │
                         │   │               │     │     │              │       │
                         │   │    ┌──────────▼┐ ┌──▼─────▼───┐ ┌───────▼────┐  │
                         │   │    │ Chat LLM  │ │ Code LLM   │ │ Embedding  │  │
                         │   │    │ Llama-70B │ │ DeepSeek-34│ │ all-MiniLM │  │
                         │   │    │ 4×A100    │ │ 2×A100     │ │ 1×T4      │  │
                         │   │    │ 2-8 reps  │ │ 1-4 reps   │ │ 1-2 reps  │  │
                         │   │    └───────────┘ └────────────┘ └────────────┘  │
                         │   └────────────────────────────────────────────────┘  │
                         │                                                       │
                         │   ┌────────────────────────────────────────────────┐  │
                         │   │              Shared Services (Dapr)            │  │
                         │   │  ┌──────────┐ ┌───────────┐ ┌──────────────┐  │  │
                         │   │  │ Pub/Sub  │ │  State    │ │  Secrets     │  │  │
                         │   │  │(Service  │ │(Redis for │ │ (Key Vault   │  │  │
                         │   │  │ Bus)     │ │ conv hist)│ │  integration)│  │  │
                         │   │  └──────────┘ └───────────┘ └──────────────┘  │  │
                         │   └────────────────────────────────────────────────┘  │
                         └───────────────────────────────────────────────────────┘
                                                     │
                         ┌───────────────────────────┼───────────────────────────┐
                         │  Platform Services        │                           │
                         │  ┌──────────┐  ┌──────────▼──────┐  ┌──────────────┐ │
                         │  │Key Vault │  │ Azure Monitor   │  │Container     │ │
                         │  │(Secrets) │  │ (Logs, Metrics, │  │Registry (ACR)│ │
                         │  │          │  │  Alerts, Traces)│  │              │ │
                         │  └──────────┘  └─────────────────┘  └──────────────┘ │
                         └───────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    Internet([Internet]) --> AFD[Azure Front Door / CDN]
    AFD --> APIM[Azure API Management]

    APIM --> Router[Dapr Request Router]

    Router --> ChatLLM[Chat LLM Container App<br/>Llama-70B · 4×A100]
    Router --> CodeLLM[Code LLM Container App<br/>DeepSeek-34B · 2×A100]
    Router --> Embed[Embedding Container App<br/>all-MiniLM · 1×T4]

    ChatLLM --> Dapr[Dapr Sidecars]
    CodeLLM --> Dapr
    Embed --> Dapr

    Dapr --> Redis[(Redis State Store)]
    Dapr --> SB[Azure Service Bus]
    Dapr --> KV[Azure Key Vault]

    ChatLLM --> AM[Azure Monitor]
    CodeLLM --> AM
    APIM --> AM

    ACR[Container Registry] --> ChatLLM
    ACR --> CodeLLM
    ACR --> Embed

    style ChatLLM fill:#4a90d9,color:#fff
    style CodeLLM fill:#4a90d9,color:#fff
    style Embed fill:#4a90d9,color:#fff
    style APIM fill:#e8a838,color:#fff
    style AFD fill:#2d8c4e,color:#fff
```

---

## 2. Container Build & Deploy Flow

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONTAINER BUILD & DEPLOY FLOW                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────┐    ┌───────────────┐    ┌──────────────┐    ┌────────────────┐
│  Source    │    │  Multi-Stage  │    │   Container  │    │   Production   │
│  Code     │───▶│  Docker Build │───▶│   Registry   │───▶│   Deployment   │
│           │    │               │    │   (ACR)      │    │                │
└───────────┘    └───────────────┘    └──────────────┘    └────────────────┘
     │                  │                    │                     │
     │            ┌─────┴──────┐      ┌─────┴──────┐       ┌─────┴──────┐
     │            │ Stage 1:   │      │ Image Tags │       │ Blue-Green │
     │            │ Builder    │      │ :latest    │       │ Canary     │
     │            │ (dev tools,│      │ :v1.2.0    │       │ Rolling    │
     │            │  compilers)│      │ :sha-abc123│       │            │
     │            └─────┬──────┘      └────────────┘       └────────────┘
     │                  │
     │            ┌─────┴──────┐
     │            │ Stage 2:   │
     │            │ Runtime    │
     │            │ (minimal,  │
     │            │  CUDA, app)│
     │            └────────────┘
     │
┌────┴──────────────────────────────────────┐
│  Source Contents:                          │
│  ├── Dockerfile                            │
│  ├── requirements.txt                      │
│  ├── src/                                  │
│  │   ├── api/routes.py                     │
│  │   ├── api/health.py                     │
│  │   ├── api/websocket.py                  │
│  │   └── model/server.py                   │
│  └── config/                               │
│      └── vllm_config.yaml                  │
└────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart LR
    subgraph Source["Source Repository"]
        Code[Python Source]
        DF[Dockerfile]
        Req[requirements.txt]
    end

    subgraph Build["Multi-Stage Build"]
        Stage1["Stage 1: Builder<br/>nvidia/cuda:12.1-devel<br/>Install dependencies"]
        Stage2["Stage 2: Runtime<br/>nvidia/cuda:12.1-runtime<br/>Copy artifacts only"]
        Stage1 --> Stage2
    end

    subgraph Registry["Container Registry"]
        Latest[":latest"]
        Versioned[":v1.2.0"]
        SHA[":sha-abc123"]
    end

    subgraph Deploy["Deployment Strategies"]
        BG[Blue-Green]
        Canary[Canary]
        Rolling[Rolling Update]
    end

    Source --> Build
    Build --> Registry
    Registry --> Deploy

    style Build fill:#f5a623,color:#fff
    style Registry fill:#4a90d9,color:#fff
    style Deploy fill:#2d8c4e,color:#fff
```

---

## 3. Scaling Patterns

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AUTO-SCALING FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐     ┌──────────────────┐     ┌───────────────────────────┐
  │   Metrics   │     │   Scaler (KEDA/  │     │   Container Replicas      │
  │   Sources   │────▶│   HPA)           │────▶│                           │
  │             │     │                  │     │  ┌─────┐ ┌─────┐ ┌─────┐  │
  └─────────────┘     └──────────────────┘     │  │Pod 1│ │Pod 2│ │Pod 3│  │
                                                │  │ ✓   │ │ ✓   │ │ ✓   │  │
  Metrics Sources:                             │  └─────┘ └─────┘ └─────┘  │
  ┌──────────────┐                             │                           │
  │ GPU Util >80%│ ──── Scale UP (+2 pods)     │  Traffic: ██████████░ 80% │
  └──────────────┘                             └───────────────────────────┘
  ┌──────────────┐                                    │
  │ Queue > 20   │ ──── Scale UP (+1 pod)             ▼
  └──────────────┘                             ┌───────────────────────────┐
  ┌──────────────┐                             │   After Scale-Up          │
  │ GPU Util <30%│ ──── Scale DOWN (-1 pod)    │                           │
  │ for 10 min   │                             │  ┌─────┐ ┌─────┐ ┌─────┐ │
  └──────────────┘                             │  │Pod 1│ │Pod 2│ │Pod 3│ │
                                                │  │ ✓   │ │ ✓   │ │ ✓   │ │
                                                │  └─────┘ └─────┘ └─────┘ │
                                                │  ┌─────┐ ┌─────┐         │
                                                │  │Pod 4│ │Pod 5│         │
                                                │  │ ✓   │ │ ✓   │         │
                                                │  └─────┘ └─────┘         │
                                                │                           │
                                                │  Traffic: ████████░░ 60%  │
                                                └───────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────┐
  │                        SCALE-TO-ZERO PATTERN                        │
  │                                                                      │
  │   Idle (5 min)     First Request Arrives      Scaled Up             │
  │                                                                      │
  │   ┌──────────┐     ┌──────────────────┐     ┌──────────────────┐   │
  │   │          │     │  Cold Start      │     │  ┌─────┐ ┌─────┐│   │
  │   │ 0 pods   │────▶│  1. Pull image   │────▶│  │Pod 1│ │Pod 2││   │
  │   │          │     │  2. Load model   │     │  │     │ │     ││   │
  │   │ $0/hr    │     │  3. Health check │     │  └─────┘ └─────┘│   │
  │   └──────────┘     │  ~30-120 sec     │     └──────────────────┘   │
  │                     └──────────────────┘                            │
  └──────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    subgraph Metrics["Metrics Collection"]
        GPU["GPU Utilization<br/>(DCGM exporter)"]
        Queue["Request Queue Depth<br/>(vLLM metrics)"]
        TTFT["Time-to-First-Token<br/>(App metrics)"]
    end

    subgraph Scaler["Autoscaler"]
        KEDA["KEDA / HPA"]
        Rules{"Scaling Rules"}
        KEDA --> Rules
        Rules -->|GPU > 80%| ScaleUp[Scale UP +2]
        Rules -->|Queue > 20| ScaleUp
        Rules -->|GPU < 30% 10min| ScaleDown[Scale DOWN -1]
        Rules -->|Queue < 5 5min| ScaleDown
    end

    subgraph Replicas["Container Replicas"]
        P1[Pod 1]
        P2[Pod 2]
        P3[Pod 3]
        P4[Pod 4 - new]
        P5[Pod 5 - new]
    end

    GPU --> KEDA
    Queue --> KEDA
    TTFT --> KEDA

    ScaleUp --> P4
    ScaleUp --> P5
    ScaleDown --> P1

    style ScaleUp fill:#2d8c4e,color:#fff
    style ScaleDown fill:#d94a4a,color:#fff
    style KEDA fill:#e8a838,color:#fff
```

---

## 4. Deployment Patterns Comparison

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BLUE-GREEN DEPLOYMENT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Phase 1: Blue Active              Phase 2: Deploy Green                  │
│   ┌──────────┐                      ┌──────────┐  ┌──────────┐            │
│   │  BLUE v1 │ ◀── 100% traffic     │  BLUE v1 │  │ GREEN v2 │            │
│   │  3 pods  │                      │  3 pods  │  │ 3 pods   │            │
│   └──────────┘                      └──────────┘  └──────────┘            │
│                                                          ▲                 │
│                                                     smoke tests            │
│                                                                             │
│   Phase 3: Switch                   Phase 4: Cleanup                        │
│   ┌──────────┐  ┌──────────┐       ┌──────────┐  ┌──────────┐            │
│   │  BLUE v1 │  │ GREEN v2 │ ◀──   │  (tear   │  │ GREEN v2 │ ◀── 100%  │
│   │  3 pods  │  │ 3 pods   │ 100%  │  down)   │  │ 3 pods   │            │
│   └──────────┘  └──────────┘       └──────────┘  └──────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          CANARY DEPLOYMENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   T+0 min                    T+30 min                   T+90 min           │
│   ┌──────────┐ ┌────────┐   ┌──────────┐ ┌────────┐  ┌──────────┐        │
│   │  v1 (95%)│ │v2 (5%) │   │  v1 (80%)│ │v2(20%)│  │  v1 (0%) │        │
│   │  8 pods  │ │1 pod   │   │  6 pods  │ │2 pods │  │          │        │
│   └──────────┘ └────────┘   └──────────┘ └────────┘  │  v2 (100%)│        │
│                                                       │  8 pods   │        │
│   Monitor: errors, latency  Monitor: same             └──────────┘        │
│   Rollback: shift to v1     Rollback: shift to v1                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROLLING UPDATE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Step 1              Step 2              Step 3              Step 4       │
│   ┌────────┐         ┌────────┐         ┌────────┐         ┌────────┐     │
│   │v1      │         │v1      │         │        │         │        │     │
│   │pod-1   │         │pod-1   │         │        │         │        │     │
│   ├────────┤         ├────────┤         ├────────┤         ├────────┤     │
│   │v1      │         │v1      │         │v1      │         │        │     │
│   │pod-2   │         │pod-2   │         │pod-2   │         │        │     │
│   ├────────┤         ├────────┤         ├────────┤         ├────────┤     │
│   │v1      │         │v2 ◀──  │         │v2      │         │v2      │     │
│   │pod-3   │         │pod-3   │         │pod-3   │         │pod-3   │     │
│   ├────────┤         ├────────┤         ├────────┤         ├────────┤     │
│   │v1      │         │v1      │         │v2 ◀──  │         │v2      │     │
│   │pod-4   │         │pod-4   │         │pod-4   │         │pod-4   │     │
│   └────────┘         └────────┘         └────────┘         └────────┘     │
│                                                                             │
│   maxSurge: 1         New pod created    Old pod terminated  Complete      │
│   maxUnavailable: 0   before old dies    after new ready                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph LR
    subgraph BlueGreen["Blue-Green Deployment"]
        BG1["BLUE v1<br/>100% traffic"] -->|Deploy GREEN| BG2["BLUE v1 + GREEN v2<br/>Smoke tests"]
        BG2 -->|Switch LB| BG3["GREEN v2<br/>100% traffic"]
        BG3 -->|Teardown| BG4["BLUE v1 removed"]
    end

    subgraph Canary["Canary Deployment"]
        C1["v1: 95% · v2: 5%"] -->|Monitor 30m| C2["v1: 80% · v2: 20%"]
        C2 -->|Monitor 30m| C3["v1: 50% · v2: 50%"]
        C3 -->|Monitor 30m| C4["v1: 0% · v2: 100%"]
    end

    subgraph Rolling["Rolling Update"]
        R1["4×v1"] --> R2["3×v1 + 1×v2"]
        R2 --> R3["2×v1 + 2×v2"]
        R3 --> R4["1×v1 + 3×v2"]
        R4 --> R5["4×v2"]
    end

    style BG3 fill:#2d8c4e,color:#fff
    style C4 fill:#2d8c4e,color:#fff
    style R5 fill:#2d8c4e,color:#fff
```

---

## 5. Model Serving Architecture

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         vLLM / TGI SERVING ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────────────┘

  Client Request                          Model Server
  ──────────────                          ────────────

  POST /v1/completions                    ┌─────────────────────────────────┐
  { "prompt": "...",                ────▶│  API Layer (FastAPI/Starlette)  │
    "max_tokens": 256 }                  │  ┌───────────┐ ┌─────────────┐  │
                                         │  │Tokenizer  │ │  Request    │  │
                                         │  │(Sentence- │ │  Scheduler  │  │
                                         │  │ Piece)    │ │             │  │
                                         │  └─────┬─────┘ └──────┬──────┘  │
                                         │        │              │         │
                                         │        ▼              ▼         │
  Streaming tokens ◀──────────────────── │  ┌─────────────────────────────┐ │
  data: {"token": "The"}                 │  │     Continuous Batcher      │ │
  data: {"token": " answer"}             │  │  (PagedAttention Scheduler) │ │
  data: {"token": " is..."}              │  └──────────────┬──────────────┘ │
  data: [DONE]                           │                 │               │
                                         │        ┌────────▼────────┐      │
                                         │        │  GPU Executor   │      │
                                         │        │  ┌────────────┐ │      │
                                         │        │  │ Model      │ │      │
                                         │        │  │ Weights    │ │      │
                                         │        │  │ (INT4 AWQ) │ │      │
                                         │        │  ├────────────┤ │      │
                                         │        │  │ KV Cache   │ │      │
                                         │        │  │ (Paged)    │ │      │
                                         │        │  ├────────────┤ │      │
                                         │        │  │ Attention  │ │      │
                                         │        │  │ Kernels    │ │      │
                                         │        │  └────────────┘ │      │
                                         │        └─────────────────┘      │
                                         └─────────────────────────────────┘
                                                        │
                                               ┌────────▼────────┐
                                               │  NVIDIA A100    │
                                               │  80GB HBM2e     │
                                               │  ┌────────────┐ │
                                               │  │Weights 35GB│ │
                                               │  │KV Cache 25GB│ │
                                               │  │Overhead 5GB │ │
                                               │  │Free     15GB│ │
                                               │  └────────────┘ │
                                               └─────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    Client[Client Application] -->|POST /v1/completions| API[API Layer<br/>FastAPI]

    API --> Tokenizer[Tokenizer<br/>SentencePiece]
    API --> Scheduler[Request Scheduler]

    Tokenizer --> Batcher[Continuous Batcher<br/>PagedAttention]
    Scheduler --> Batcher

    Batcher --> GPU[GPU Executor]

    GPU --> Weights[Model Weights<br/>INT4 AWQ · 35GB]
    GPU --> KVCache[KV Cache<br/>Paged · 25GB]
    GPU --> Kernels[Attention Kernels<br/>Flash Attention]

    GPU -->|Stream tokens| Client

    subgraph A100["NVIDIA A100 80GB"]
        Weights
        KVCache
        Kernels
    end

    style GPU fill:#76b900,color:#fff
    style API fill:#4a90d9,color:#fff
    style Batcher fill:#e8a838,color:#fff
```

---

## 6. Health Check & Traffic Flow

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HEALTH CHECK & TRAFFIC FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

                     ┌──────────────────────┐
                     │    Load Balancer     │
                     │  (Kubernetes Service)│
                     └──────────┬───────────┘
                                │
                    Only routes to READY pods
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
     ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
     │   Pod A     │    │   Pod B     │    │   Pod C     │
     │             │    │             │    │             │
     │ ┌─────────┐ │    │ ┌─────────┐ │    │ ┌─────────┐ │
     │ │Readiness│ │    │ │Readiness│ │    │ │Readiness│ │
     │ │ Probe   │ │    │ │ Probe   │ │    │ │ Probe   │ │
     │ │ ✓ 200   │ │    │ │ ✓ 200   │ │    │ │ ✗ 503   │ │
     │ └─────────┘ │    │ └─────────┘ │    │ └─────────┘ │
     │ ┌─────────┐ │    │ ┌─────────┐ │    │ ┌─────────┐ │
     │ │Liveness │ │    │ │Liveness │ │    │ │Liveness │ │
     │ │ Probe   │ │    │ │ Probe   │ │    │ │ Probe   │ │
     │ │ ✓ 200   │ │    │ │ ✓ 200   │ │    │ │ ✗ 503   │ │
     │ └─────────┘ │    │ └─────────┘ │    │ └─────────┘ │
     │             │    │             │    │             │
     │ Model:      │    │ Model:      │    │ Model:      │
     │ LOADED ✓    │    │ LOADED ✓    │    │ LOADING...  │
     │             │    │             │    │             │
     │ Status:     │    │ Status:     │    │ Status:     │
     │ SERVING     │    │ SERVING     │    │ NOT READY   │
     └─────────────┘    └─────────────┘    └─────────────┘
          RECEIVE            RECEIVE          EXCLUDED
          TRAFFIC            TRAFFIC          FROM LB

  ┌─────────────────────────────────────────────────────────┐
  │                    Probe Configuration                   │
  │                                                         │
  │  Readiness:  GET /health  every 10s                     │
  │              initialDelay: 60s  (model loading)         │
  │              → removes pod from Service on failure      │
  │                                                         │
  │  Liveness:   GET /health  every 30s                     │
  │              initialDelay: 120s                         │
  │              failureThreshold: 5                        │
  │              → restarts container on repeated failure    │
  └─────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    LB[Load Balancer<br/>Kubernetes Service] -->|Only healthy| PodA[Pod A<br/>READY]
    LB -->|Only healthy| PodB[Pod B<br/>READY]
    LB -.-x|Excluded| PodC[Pod C<br/>NOT READY]

    PodA --> RA[Readiness ✓]
    PodA --> LA[Liveness ✓]
    PodB --> RB[Readiness ✓]
    PodB --> LB2[Liveness ✓]
    PodC --> RC[Readiness ✗]
    PodC --> LC[Liveness ✗]

    RC --> Remove[Remove from<br/>Service endpoints]
    LC -->|After 5 failures| Restart[Restart<br/>container]

    style PodA fill:#2d8c4e,color:#fff
    style PodB fill:#2d8c4e,color:#fff
    style PodC fill:#d94a4a,color:#fff
```

---

## 7. CI/CD Pipeline Flow

### Mermaid Diagram

```mermaid
graph LR
    Dev[Developer Push] --> Build[Build Image<br/>ACR Build]
    Build --> Scan[Security Scan<br/>Trivy]
    Scan --> Test[Integration Tests<br/>GPU Runner]
    Test --> Perf[Performance Test<br/>Throughput Benchmark]
    Perf --> Stage[Deploy Staging<br/>Container App]
    Stage --> Smoke[Smoke Tests<br/>Health + API]
    Smoke --> Approve{Manual<br/>Approval}
    Approve -->|Approved| Canary[Canary Deploy<br/>10% traffic]
    Canary --> Monitor[Monitor 10min<br/>Error Rate < 1%]
    Monitor -->|Pass| Promote[Promote 100%]
    Monitor -->|Fail| Rollback[Rollback to v1]
    Promote --> Done[Production ✓]

    style Promote fill:#2d8c4e,color:#fff
    style Rollback fill:#d94a4a,color:#fff
    style Approve fill:#e8a838,color:#fff
```

---

*End of Module 12 Diagrams*
