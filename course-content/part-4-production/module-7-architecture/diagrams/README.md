# Module 7: Architecture Design — Diagrams

Architecture diagrams for AI system design patterns. Includes ASCII and Mermaid representations.

---

## 1. Full System Architecture Overview

High-level view of a production AI serving system with all layers.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                      │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐           │
│   │  Web    │   │ Mobile  │   │  API    │   │Internal │           │
│   │  App    │   │  App    │   │ Client  │   │ Service │           │
│   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘           │
└────────┼─────────────┼─────────────┼─────────────┼─────────────────┘
         └─────────────┴──────┬──────┴─────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                      API GATEWAY LAYER                               │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐             │
│  │   Auth    │ │Rate Limit│ │  Cache   │ │  Logging  │             │
│  └───────────┘ └──────────┘ └──────────┘ └───────────┘             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                    ORCHESTRATION LAYER                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Request    │  │   Model      │  │   Cost       │               │
│  │  Router     │  │   Selector   │  │   Optimizer  │               │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘               │
└─────────┼────────────────┼─────────────────┼────────────────────────┘
          │                │                 │
┌─────────▼────────────────▼─────────────────▼────────────────────────┐
│                      SERVICE LAYER                                   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Embedding   │  │  Retrieval   │  │  Generation  │              │
│  │  Service     │  │  Service     │  │  Service     │              │
│  │  (GPU)       │  │  (CPU)       │  │  (GPU)       │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐              │
│  │  Eval        │  │  Cache       │  │  Async       │              │
│  │  Service     │  │  Service     │  │  Worker Pool │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼───────────────────────┐
│                        DATA LAYER                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Vector   │  │  Redis   │  │ Message  │  │ Object   │            │
│  │ Database │  │  Cache   │  │ Queue    │  │ Storage  │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└──────────────────────────────────────────────────────────────────────┘
```

### Mermaid

```mermaid
graph TB
    subgraph Clients
        W[Web App]
        M[Mobile App]
        A[API Client]
        I[Internal Service]
    end

    subgraph Gateway["API Gateway Layer"]
        Auth[Auth]
        RL[Rate Limit]
        GC[Cache]
        Log[Logging]
    end

    subgraph Orchestration["Orchestration Layer"]
        RR[Request Router]
        MS[Model Selector]
        CO[Cost Optimizer]
    end

    subgraph Services["Service Layer"]
        ES[Embedding Service]
        RS[Retrieval Service]
        GS[Generation Service]
        EVS[Eval Service]
        CS[Cache Service]
        WP[Async Worker Pool]
    end

    subgraph Data["Data Layer"]
        VDB[(Vector DB)]
        RC[(Redis Cache)]
        MQ[(Message Queue)]
        OS[(Object Storage)]
    end

    W & M & A & I --> Gateway
    Gateway --> Orchestration
    Orchestration --> Services
    Services --> Data
```

---

## 2. Microservices Pattern for AI

Individual AI components as independently deployable services.

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway                              │
│            (Auth, Rate Limit, Routing)                       │
└──────────┬───────────┬───────────┬───────────┬──────────────┘
           │           │           │           │
     ┌─────▼─────┐ ┌──▼──────┐ ┌─▼────────┐ ┌▼───────────┐
     │ Embedding │ │ Search  │ │Generation│ │ Evaluation │
     │ Service   │ │ Service │ │ Service  │ │ Service    │
     │           │ │         │ │          │ │            │
     │ ┌───────┐ │ │┌───────┐│ │┌────────┐│ │┌──────────┐│
     │ │GPU-0  │ │ ││CPU    ││ ││GPU-1   ││ ││GPU-2     ││
     │ │Model  │ │ ││Vector ││ ││LLM     ││ ││Judge     ││
     │ └───────┘ │ ││Search ││ │└────────┘│ │└──────────┘│
     └─────┬─────┘ │└───┬───┘│ └────┬─────┘ └─────┬──────┘
           │       └────┼───┘      │              │
     ┌─────▼────────────▼──────────▼──────────────▼──────┐
     │                  Message Bus                        │
     │            (Redis Streams / Kafka)                  │
     └────────────────────────┬───────────────────────────┘
                              │
     ┌────────────────────────▼───────────────────────────┐
     │              Shared State Layer                     │
     │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  │
     │  │ Redis  │  │Vector  │  │Object  │  │Metrics │  │
     │  │ Cache  │  │  DB    │  │ Store  │  │  DB    │  │
     │  └────────┘  └────────┘  └────────┘  └────────┘  │
     └────────────────────────────────────────────────────┘
```

### Mermaid

```mermaid
graph LR
    GW[API Gateway] --> ES[Embedding Service<br/>GPU]
    GW --> SS[Search Service<br/>CPU]
    GW --> GS[Generation Service<br/>GPU]
    GW --> EVS[Evaluation Service<br/>GPU]

    ES --> MB[Message Bus<br/>Redis/Kafka]
    SS --> MB
    GS --> MB
    EVS --> MB

    MB --> RC[(Redis Cache)]
    MB --> VDB[(Vector DB)]
    MB --> OS[(Object Store)]
    MB --> MDB[(Metrics DB)]

    style ES fill:#4A90D9,color:#fff
    style GS fill:#4A90D9,color:#fff
    style EVS fill:#4A90D9,color:#fff
    style SS fill:#7B68EE,color:#fff
```

---

## 3. Event-Driven Architecture (Async Processing)

Asynchronous processing pipeline for AI inference with message queues.

```
┌──────────┐    ┌──────────────┐    ┌─────────────────────────────┐
│  Client   │───▶│  API Server  │───▶│       Task Queue            │
│           │◀───│              │    │    (Redis / Kafka / SQS)    │
│  task_id  │    │  Validate    │    │                             │
│  returned │    │  Authenticate│    │  ┌────┐┌────┐┌────┐┌────┐ │
└──────────┘    │  Rate Limit  │    │  │ T1 ││ T2 ││ T3 ││ T4 │ │
                 └──────────────┘    │  └────┘└────┘└────┘└────┘ │
                                     └─────┬──────┬──────┬───────┘
                                           │      │      │
                                     ┌─────▼──┐┌──▼────┐┌▼──────┐
                                     │Worker 1││Worker 2││Worker N│
                                     │ (GPU)  ││ (GPU)  ││ (GPU) │
                                     └───┬────┘└───┬────┘└───┬───┘
                                         │         │         │
                                     ┌───▼─────────▼─────────▼───┐
                                     │      Result Store          │
                                     │      (Redis)               │
                                     └─────────────┬──────────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Client Polls   │
                                          │  GET /task/{id}  │
                                          └─────────────────┘
```

### Mermaid — Sequence Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Server
    participant Q as Task Queue
    participant W as GPU Worker
    participant RS as Result Store

    C->>API: POST /v1/generate
    API->>Q: Enqueue task
    API-->>C: 202 Accepted {task_id}

    Q->>W: Dequeue task
    W->>W: Run inference
    W->>RS: Store result

    loop Poll until complete
        C->>API: GET /v1/tasks/{id}
        API->>RS: Fetch result
        RS-->>API: Result or pending
        API-->>C: Status + result
    end
```

---

## 4. Circuit Breaker State Machine

```
     ┌──────────────────────────────────────────┐
     │          Circuit Breaker States           │
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

### Mermaid — State Diagram

```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open: failures >= threshold
    Open --> HalfOpen: recovery timeout expires
    HalfOpen --> Closed: test requests succeed
    HalfOpen --> Open: test request fails

    state Closed {
        [*] --> Monitoring
        Monitoring --> Monitoring: success
        Monitoring --> CountFailure: failure
        CountFailure --> Monitoring: below threshold
    }

    state Open {
        [*] --> Rejecting
        Rejecting --> Rejecting: reject all requests
    }

    state HalfOpen {
        [*] --> Testing
        Testing --> Testing: allow limited probe requests
    }
```

---

## 5. Auto-Scaling Flow

```
                     ┌───────────────────┐
                     │  Auto Scaler      │
                     │                   │
                     │  Triggers:        │
                     │  - GPU util > 80% │
                     │  - Queue > 50     │
                     │  - P95 > 5s       │
                     └─────────┬─────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │ Scale Up            │                      │ Scale Down
         ▼                     │                      ▼
┌───────────────┐             │            ┌───────────────┐
│ Add GPU Nodes │             │            │Remove GPU Nodes│
│               │             │            │               │
│ ┌───┐┌───┐┌───┐┌───┐┌───┐ │            │ ┌───┐┌───┐    │
│ │GPU││GPU││GPU││GPU││GPU│ │            │ │GPU││GPU│    │
│ │ 1 ││ 2 ││ 3 ││ 4 ││ 5 │ │            │ │ 1 ││ 2 │    │
│ └───┘└───┘└───┘└───┘└───┘ │            │ └───┘└───┘    │
└───────────────┘             │            └───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Cooldown Period  │
                    │  (5 minutes)      │
                    └───────────────────┘
```

### Mermaid — Auto-Scaling Decision Flow

```mermaid
graph TD
    M[Monitor Metrics] --> D{GPU util > 80%?}
    D -->|Yes| SU[Scale Up: Add instances]
    D -->|No| QD{Queue depth > 50?}
    QD -->|Yes| SU
    QD -->|No| LU{GPU util < 30%?}
    LU -->|Yes| SD[Scale Down: Remove instances]
    LU -->|No| NC[No Change]

    SU --> CD[Cooldown 5 min]
    SD --> CD
    CD --> M
    NC --> M

    style SU fill:#4CAF50,color:#fff
    style SD fill:#F44336,color:#fff
    style NC fill:#9E9E9E,color:#fff
```

---

## 6. Multi-Region Deployment with Failover

```
                         ┌──────────────┐
                         │  Global DNS  │
                         │  (Route53)   │
                         └──────┬───────┘
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
         ┌───────▼──────┐ ┌────▼────────┐ ┌──▼──────────┐
         │  us-east-1   │ │ eu-west-1   │ │ ap-south-1  │
         │  PRIMARY     │ │ SECONDARY   │ │ SECONDARY   │
         │              │ │             │ │             │
         │ ┌──────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │
         │ │API GW    │ │ │ │API GW   │ │ │ │API GW   │ │
         │ └────┬─────┘ │ │ └───┬─────┘ │ │ └───┬─────┘ │
         │      │       │ │     │       │ │     │       │
         │ ┌────▼─────┐ │ │┌────▼─────┐ │ │┌────▼─────┐ │
         │ │Model     │ │ ││Model     │ │ ││Model     │ │
         │ │Cluster   │ │ ││Cluster   │ │ ││Cluster   │ │
         │ │(10 GPUs) │ │ ││(6 GPUs)  │ │ ││(4 GPUs)  │ │
         │ └────┬─────┘ │ │└────┬─────┘ │ │└────┬─────┘ │
         │      │       │ │     │       │ │     │       │
         │ ┌────▼─────┐ │ │┌────▼─────┐ │ │┌────▼─────┐ │
         │ │Vector DB │ │ ││Vector DB │ │ ││Vector DB │ │
         │ │(Primary) │◄├─┤│(Replica) │◄├─┤│(Replica) │ │
         │ └──────────┘ │ │└──────────┘ │ │└──────────┘ │
         └──────────────┘ └─────────────┘ └─────────────┘
               │                  │                │
               └──────────────────┴────────────────┘
                     Async Replication (RPO < 5min)
```

### Mermaid — Multi-Region with Subgraphs

```mermaid
graph TB
    DNS[Global DNS] --> USE[US-East Primary]
    DNS --> EUW[EU-West Secondary]
    DNS --> APS[AP-South Secondary]

    USE <-->|Async Sync| EUW
    EUW <-->|Async Sync| APS
    APS <-->|Async Sync| USE

    subgraph USE
        USE_GW[API GW] --> USE_GPU[Model Cluster 10 GPUs]
        USE_GPU --> USE_VDB[(Vector DB Primary)]
    end

    subgraph EUW
        EUW_GW[API GW] --> EUW_GPU[Model Cluster 6 GPUs]
        EUW_GPU --> EUW_VDB[(Vector DB Replica)]
    end

    subgraph APS
        APS_GW[API GW] --> APS_GPU[Model Cluster 4 GPUs]
        APS_GPU --> APS_VDB[(Vector DB Replica)]
    end
```

---

## 7. Cost Optimization — Model Routing Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│                  COST OPTIMIZATION PYRAMID                       │
│                                                                  │
│                         ┌───────┐                               │
│                         │ Model │  Most Impact                  │
│                        ┌┤Route  ├┐                              │
│                       ┌┤└───────┘├┐                             │
│                      ┌┤│ Caching │├┐                            │
│                     ┌┤│└─────────┘│├┐                           │
│                    ┌┤││  Batching  ││├┐                          │
│                   ┌┤│││ Token Opt  │││├┐                         │
│                  ┌┤││││───────────││││├┐                        │
│                  ││││││ Infra Opt  ││││││  Least Impact          │
│                  └┴┴┴┴┴───────────┴┴┴┴┴┘                        │
│                                                                  │
│  Savings:   70%    50%    30%    20%    10%   5%               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  MODEL ROUTING DECISION TREE                     │
│                                                                  │
│                      ┌──────────┐                               │
│                      │ Incoming │                               │
│                      │ Request  │                               │
│                      └────┬─────┘                               │
│                           │                                     │
│                    ┌──────▼──────┐                               │
│                    │  Complexity │                               │
│                    │  Classifier │                               │
│                    └──┬───┬───┬──┘                               │
│                       │   │   │                                  │
│              ┌────────┘   │   └────────┐                        │
│              ▼            ▼            ▼                        │
│        ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│        │  Simple  │ │ Standard │ │ Complex  │                  │
│        │          │ │          │ │          │                  │
│        │ GPT-4o   │ │ GPT-4o   │ │ GPT-4o   │                  │
│        │ Nano     │ │ Mini     │ │ Standard │                  │
│        │          │ │          │ │          │                  │
│        │ $0.15/1M │ │ $0.60/1M │ │ $5.00/1M │                  │
│        │ tokens   │ │ tokens   │ │ tokens   │                  │
│        └──────────┘ └──────────┘ └──────────┘                  │
│                                                                  │
│  40% of traffic  │  40% of traffic  │  20% of traffic           │
└─────────────────────────────────────────────────────────────────┘
```

### Mermaid — Cost Optimization Flow

```mermaid
graph TD
    R[Incoming Request] --> C{Exact Cache Hit?}
    C -->|Yes| CR[Return Cached<br/>Cost: $0]
    C -->|No| S{Semantic Cache Hit?}
    S -->|Yes| SR[Return Similar<br/>Cost: $0]
    S -->|No| CX{Complexity?}
    CX -->|Simple| N[Route to Nano<br/>$0.15/1M tokens]
    CX -->|Standard| M[Route to Mini<br/>$0.60/1M tokens]
    CX -->|Complex| ST[Route to Standard<br/>$5.00/1M tokens]

    N --> PC[Populate Cache]
    M --> PC
    ST --> PC
    PC --> R2[Return Response]

    style CR fill:#4CAF50,color:#fff
    style SR fill:#4CAF50,color:#fff
    style N fill:#8BC34A,color:#fff
    style M fill:#FFC107,color:#fff
    style ST fill:#F44336,color:#fff
```

---

## 8. Multi-Layer Caching Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    REQUEST FLOW                                │
│                                                               │
│  Request ──▶ ┌─────────────────────────────────────────────┐ │
│              │           LAYER 1: Exact Match              │ │
│              │     Hash(model + query) → Redis lookup      │ │
│              │     Latency: ~1ms  │  Hit Rate: ~15%       │ │
│              └──────────────┬──────────────────────────────┘ │
│                             │ MISS                            │
│              ┌──────────────▼──────────────────────────────┐ │
│              │           LAYER 2: Semantic Cache           │ │
│              │     Embed query → Vector similarity search  │ │
│              │     Threshold: 0.95  │  Hit Rate: ~25%     │ │
│              └──────────────┬──────────────────────────────┘ │
│                             │ MISS                            │
│              ┌──────────────▼──────────────────────────────┐ │
│              │           LAYER 3: KV Cache                 │ │
│              │     Reuse cached KV states for prefixes     │ │
│              │     Saves 30-50% compute  │  Hit: ~20%     │ │
│              └──────────────┬──────────────────────────────┘ │
│                             │ MISS                            │
│              ┌──────────────▼──────────────────────────────┐ │
│              │           LAYER 4: Full Inference           │ │
│              │     Run model → Generate response           │ │
│              │     Latency: 500ms+  │  Cost: Full         │ │
│              └──────────────┬──────────────────────────────┘ │
│                             │                                 │
│              ┌──────────────▼──────────────────────────────┐ │
│              │         POPULATE ALL CACHE LAYERS           │ │
│              │     Store result in Layers 1, 2, 3          │ │
│              └─────────────────────────────────────────────┘ │
│                                                               │
│  Response ◀────────────────────────────────────────────────── │
└──────────────────────────────────────────────────────────────┘
```

### Mermaid — Cache Layer Flow

```mermaid
graph TD
    R[Request] --> L1{Layer 1: Exact Match}
    L1 -->|Hit| H1[Return Cached - 1ms]
    L1 -->|Miss| L2{Layer 2: Semantic Cache}
    L2 -->|Hit| H2[Return Similar - 5ms]
    L2 -->|Miss| L3{Layer 3: KV Prefix Cache}
    L3 -->|Hit| INF[Inference - Saves 30-50% compute]
    L3 -->|Miss| INF2[Full Inference - 500ms+]

    INF --> POP[Populate All Layers]
    INF2 --> POP
    POP --> RESP[Return Response]

    style H1 fill:#4CAF50,color:#fff
    style H2 fill:#8BC34A,color:#fff
    style INF fill:#FFC107,color:#000
    style INF2 fill:#F44336,color:#fff
```

---

## 9. vLLM Model Serving Architecture (PagedAttention)

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

### Mermaid — vLLM Request Flow

```mermaid
graph LR
    API[API Request] --> SCH[Scheduler]
    SCH -->|Continuous Batch| PA[PagedAttention Engine]
    PA --> GPU0[GPU 0<br/>KV Pages]
    PA --> GPU1[GPU 1<br/>KV Pages]
    PA --> GPUN[GPU N<br/>KV Pages]
    GPU0 --> OUT[Response Stream]
    GPU1 --> OUT
    GPUN --> OUT

    style PA fill:#4A90D9,color:#fff
    style SCH fill:#7B68EE,color:#fff
```

---

## 10. Fallback Chain with Reliability Layers

```mermaid
graph TD
    REQ[Incoming Request] --> CB{Circuit Breaker<br/>Open?}
    CB -->|Yes| FALLBACK[Skip to Fallback]
    CB -->|No| RETRY[Retry with Backoff]
    RETRY --> M1{GPT-4o}
    M1 -->|Success| R1[Return Response]
    M1 -->|Failure| M2{GPT-4o-mini}
    M2 -->|Success| R2[Return Response]
    M2 -->|Failure| M3{Claude Haiku}
    M3 -->|Success| R3[Return Response]
    M3 -->|Failure| CACHE{Semantic Cache}
    CACHE -->|Hit| R4[Return Cached]
    CACHE -->|Miss| TEMPLATE[Return Template Response]

    FALLBACK --> CACHE

    style R1 fill:#4CAF50,color:#fff
    style R2 fill:#8BC34A,color:#fff
    style R3 fill:#FFC107,color:#000
    style R4 fill:#FF9800,color:#fff
    style TEMPLATE fill:#F44336,color:#fff
```

---

## Diagram Conventions

- **Solid boxes** (`┌───┐`) represent services or components
- **Arrows** (`──▶`) show data/control flow
- **Dashed lines** indicate async or secondary paths
- **Color coding** in Mermaid: Green = optimal, Yellow = acceptable, Red = costly/degraded
- **Vertical layers** represent abstraction levels (clients at top, data at bottom)
- **State diagrams** use `stateDiagram-v2` for circuit breaker and deployment patterns
- **Sequence diagrams** use `sequenceDiagram` for async request flows
