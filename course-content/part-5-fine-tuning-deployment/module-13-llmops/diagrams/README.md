# Module 13: Diagrams — LLMOps

This directory contains text-based and Mermaid diagrams illustrating key concepts from Module 13.

---

## 1. LLMOps Lifecycle

### Mermaid Diagram

```mermaid
graph LR
    Design[Design] --> Build[Build]
    Build --> Evaluate[Evaluate]
    Evaluate --> Deploy[Deploy]
    Deploy --> Monitor[Monitor]
    Monitor -->|Feedback| Design

    subgraph Design Phase
        D1[Use Case Selection]
        D2[Architecture Design]
        D3[RAG vs Fine-tuning vs Agent]
    end

    subgraph Build Phase
        B1[Prompt Engineering]
        B2[RAG Pipeline]
        B3[Chain / Agent Construction]
    end

    subgraph Evaluate Phase
        E1[Offline Evals]
        E2[A/B Testing]
        E3[Safety Checks]
    end

    subgraph Deploy Phase
        DP1[Canary / Blue-Green]
        DP2[Feature Flags]
        DP3[Model Registry]
    end

    subgraph Monitor Phase
        M1[Latency & Cost]
        M2[Quality Scores]
        M3[Safety & Drift]
    end

    style Design fill:#e3f2fd
    style Build fill:#e8f5e9
    style Evaluate fill:#fff3e0
    style Deploy fill:#fce4ec
    style Monitor fill:#f3e5f5
```

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLMOps LIFECYCLE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │  DESIGN  │───▶│  BUILD   │───▶│ EVALUATE │───▶│  DEPLOY  │───▶│ MONITOR││
│  │          │    │          │    │          │    │          │    │        ││
│  │• Use case│    │• Prompt  │    │• Offline │    │• Canary  │    │• Latency││
│  │  select │    │  eng.    │    │  evals   │    │• Blue-   │    │• Cost  ││
│  │• Arch.  │    │• RAG     │    │• A/B test│    │  green   │    │• Quality││
│  │  design │    │  pipeline│    │• Safety  │    │• Feature │    │• Safety││
│  │• Model  │    │• Chains/ │    │  checks  │    │  flags   │    │• Drift ││
│  │  select │    │  agents  │    │          │    │          │    │        ││
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └───┬────┘│
│       ▲                                                            │      │
│       └────────────────────── FEEDBACK LOOP ───────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. LLMOps vs MLOps Comparison

### ASCII Diagram

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│              MLOps                  │              LLMOps                 │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│  Custom-trained models              │  Pre-trained foundation models      │
│         │                           │         │                           │
│         ▼                           │         ▼                           │
│  ┌─────────────────┐                │  ┌─────────────────┐                │
│  │ Training Pipeline│               │  │ Prompt Templates │               │
│  │ (PyTorch, TF)   │               │  │ Chains, Agents   │               │
│  └────────┬────────┘                │  └────────┬────────┘                │
│           │                          │           │                          │
│           ▼                          │           ▼                          │
│  ┌─────────────────┐                │  ┌─────────────────┐                │
│  │ Model Weights   │                │  │ RAG + Vector DB │                │
│  │ (ONNX, SavedM.) │                │  │ Fine-tuned LoRA │                │
│  └────────┬────────┘                │  └────────┬────────┘                │
│           │                          │           │                          │
│           ▼                          │           ▼                          │
│  ┌─────────────────┐                │  ┌─────────────────┐                │
│  │  Accuracy, F1   │                │  │ Hallucination   │                │
│  │  AUC, Precision │                │  │ Faithfulness    │                │
│  └─────────────────┘                │  │ Relevance       │                │
│                                     │  └─────────────────┘                │
│                                     │                                     │
│  MONITOR:                           │  MONITOR:                           │
│  • Data drift                       │  • Token usage                      │
│  • Prediction drift                 │  • Cost per query                   │
│  • Feature importance               │  • Latency P99                      │
│                                     │  • Safety scores                    │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

---

## 3. Deployment Strategies

### Mermaid Diagram

```mermaid
graph TD
    subgraph Blue-Green
        LB1[Load Balancer] -->|100%| Blue[Blue - Current]
        LB1 -.->|0%| Green[Green - New]
        LB1 -.->|Switch| Green
    end

    subgraph Canary
        LB2[Load Balancer] -->|90%| Stable[Stable Version]
        LB2 -->|10%| Canary[Canary Version]
    end

    subgraph Shadow
        LB3[Load Balancer] -->|100%| Primary[Primary Version]
        LB3 -->|Mirror| ShadowV[Shadow Version]
        ShadowV -->|Drop| Void[Responses Discarded]
    end

    style Blue fill:#bbdefb
    style Green fill:#c8e6c9
    style Stable fill:#c8e6c9
    style Canary fill:#fff9c4
    style Primary fill:#c8e6c9
    style ShadowV fill:#e0e0e0
```

### ASCII Diagram

```
BLUE-GREEN DEPLOYMENT                CANARY DEPLOYMENT
┌──────────────────────┐             ┌──────────────────────┐
│     Load Balancer    │             │     Load Balancer    │
└──────────┬───────────┘             └──────────┬───────────┘
           │                                    │
     ┌─────┴─────┐                      ┌───────┴───────┐
     │           │                      │               │
┌────▼────┐ ┌────▼────┐          ┌─────▼─────┐  ┌──────▼──────┐
│  BLUE   │ │  GREEN  │          │  STABLE   │  │   CANARY    │
│ (v1.0)  │ │ (v2.0)  │          │   (90%)   │  │    (10%)    │
│ Active  │ │ Standby │          │           │  │             │
└─────────┘ └─────────┘          └───────────┘  └─────────────┘

Traffic: 100% → 0%                Traffic: 90% → 10%
Instant switch on success         Gradual increase if healthy


SHADOW DEPLOYMENT                  FEATURE FLAGS
┌──────────────────────┐          ┌──────────────────────┐
│     Load Balancer    │          │   Feature Flag Svc   │
└──────────┬───────────┘          └──────────┬───────────┘
           │                                 │
     ┌─────┴─────┐                    ┌──────┴──────┐
     │           │                    │             │
┌────▼────┐ ┌────▼────┐        ┌─────▼─────┐ ┌─────▼─────┐
│PRIMARY  │ │ SHADOW  │        │  FLAG ON  │ │  FLAG OFF │
│ 100%    │ │ Mirror  │        │ New Model │ │ Old Model │
│ Served  │ │ Dropped │        │  (gpt-4o) │ │(gpt-4o-mi)│
└─────────┘ └─────────┘        └───────────┘ └───────────┘
```

---

## 4. Monitoring Stack Architecture

### Mermaid Diagram

```mermaid
graph TB
    App[LLM Application] -->|Traces| OTel[OpenTelemetry Collector]
    App -->|Metrics| Prom[Prometheus]
    App -->|Logs| LogA[Log Analytics]

    OTel -->|Export| Tempo[Tempo / Jaeger]
    Prom --> Grafana[Grafana Dashboard]
    Tempo --> Grafana
    LogA --> Grafana

    Grafana --> Alert[Alert Manager]
    Alert --> Slack[Slack Notifications]
    Alert --> Pager[PagerDuty]

    subgraph LLM Metrics
        Token[Token Usage]
        Cost[Cost per Request]
        Lat[Latency P50/P99]
        Hall[Hallucination Rate]
    end

    Prom --> LLM Metrics

    style App fill:#e3f2fd
    style Grafana fill:#fff3e0
    style Alert fill:#ffebee
```

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MONITORING STACK                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐                                                     │
│  │ LLM Application │                                                     │
│  │                 │                                                     │
│  │ ┌─────────────┐ │    ┌──────────────┐    ┌──────────────────┐        │
│  │ │ OpenTelemetry│─┼───▶│   Traces     │───▶│  Tempo / Jaeger  │        │
│  │ └─────────────┘ │    └──────────────┘    └──────────────────┘        │
│  │ ┌─────────────┐ │    ┌──────────────┐    ┌──────────────────┐        │
│  │ │ Prometheus  │─┼───▶│   Metrics    │───▶│   Prometheus DB  │        │
│  │ └─────────────┘ │    └──────────────┘    └──────────────────┘        │
│  │ ┌─────────────┐ │    ┌──────────────┐    ┌──────────────────┐        │
│  │ │ App Insights│─┼───▶│    Logs      │───▶│  Log Analytics   │        │
│  │ └─────────────┘ │    └──────────────┘    └──────────────────┘        │
│  └─────────────────┘                                                     │
│                                                                          │
│                         ┌──────────────────┐                             │
│                         │  Grafana          │                             │
│                         │  ┌──────────────┐ │                             │
│                         │  │ Dashboards   │ │                             │
│                         │  │ • Latency    │ │    ┌──────────────┐        │
│                         │  │ • Cost       │ │───▶│ Alert Manager│        │
│                         │  │ • Tokens     │ │    └──────┬───────┘        │
│                         │  │ • Quality    │ │           │                 │
│                         │  │ • Safety     │ │    ┌──────┴───────┐        │
│                         │  └──────────────┘ │    │  Slack /     │        │
│                         └──────────────────┘    │  PagerDuty   │        │
│                                                 └──────────────┘        │
│                                                                          │
│  LLM-SPECIFIC METRICS:                                                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────────────┐    │
│  │ Token Usage│ │ Cost/Query │ │Latency P99 │ │ Hallucination Rate│    │
│  │ (histogram)│ │ (counter)  │ │(histogram) │ │    (gauge)        │    │
│  └────────────┘ └────────────┘ └────────────┘ └───────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Defense Layers

### Mermaid Diagram

```mermaid
graph TD
    User[User Input] --> L1[Layer 1: WAF / Rate Limiting]
    L1 --> L2[Layer 2: Input Sanitization]
    L2 --> L3[Layer 3: PII Detection & Redaction]
    L3 --> L4[Layer 4: Prompt Injection Classifier]
    L4 --> L5[Layer 5: Content Safety Check]
    L5 --> LLM[LLM Inference]
    LLM --> O1[Layer 6: Output PII Check]
    O1 --> O2[Layer 7: Hallucination Detection]
    O2 --> O3[Layer 8: Content Safety Check]
    O3 --> O4[Layer 9: Output Formatting & Validation]
    O4 --> Response[Response to User]

    style L1 fill:#ffcdd2
    style L2 fill:#ffcdd2
    style L3 fill:#fff9c4
    style L4 fill:#ffcdd2
    style L5 fill:#ffcdd2
    style LLM fill:#c8e6c9
    style O1 fill:#fff9c4
    style O2 fill:#e1bee7
    style O3 fill:#ffcdd2
    style O4 fill:#bbdefb
```

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SECURITY DEFENSE-IN-DEPTH                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUT PIPELINE                                                         │
│  ─────────────                                                          │
│                                                                          │
│  User Input                                                             │
│      │                                                                   │
│      ▼                                                                   │
│  ┌──────────────────────────────┐                                       │
│  │ L1: WAF / Rate Limiting      │  Block abusive traffic                │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L2: Input Sanitization       │  Detect known injection patterns      │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L3: PII Detection            │  Redact emails, SSNs, phones          │
│  │     & Redaction              │                                       │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L4: Injection Classifier     │  ML-based prompt injection detection  │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L5: Content Safety Check     │  Hate, violence, sexual content       │
│  └──────────────┬───────────────┘                                       │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │      LLM INFERENCE           │  Azure OpenAI / Self-hosted           │
│  └──────────────┬───────────────┘                                       │
│                 │                                                        │
│  OUTPUT PIPELINE                                                        │
│  ──────────────                                                         │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L6: Output PII Check         │  Verify no PII leaked in response     │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L7: Hallucination Detection  │  Faithfulness check against context   │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L8: Content Safety Check     │  Verify output safety                 │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                       │
│  │ L9: Output Validation        │  Format, schema, completeness         │
│  └──────────────┬───────────────┘                                       │
│                 │                                                        │
│                 ▼                                                        │
│          Response to User                                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Cost Optimization Architecture

### Mermaid Diagram

```mermaid
graph TD
    Query[User Query] --> Classifier[Complexity Classifier]
    Classifier -->|Simple| Budget[GPT-4o-mini]
    Classifier -->|Moderate| Standard[GPT-4o]
    Classifier -->|Complex| Premium[GPT-4o]

    Query --> Cache[Semantic Cache]
    Cache -->|Hit| Response[Return Cached Response]
    Cache -->|Miss| Classifier

    Budget --> Response
    Standard --> Response
    Premium --> Response

    Response --> Metrics[Cost & Quality Metrics]
    Metrics -->|Quality Below Threshold| Escalate[Escalate to Premium]
    Escalate --> Premium

    style Budget fill:#c8e6c9
    style Standard fill:#fff9c4
    style Premium fill:#ffcdd2
    style Cache fill:#e1bee7
    style Classifier fill:#bbdefb
```

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COST OPTIMIZATION ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Query                                                             │
│      │                                                                   │
│      ▼                                                                   │
│  ┌──────────────────┐                                                   │
│  │ Semantic Cache   │──── Cache Hit ────▶ Return Cached (Cost: $0)     │
│  │ (Redis + Embed.) │                                                   │
│  └────────┬─────────┘                                                   │
│           │ Cache Miss                                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │ Complexity       │                                                   │
│  │ Classifier       │                                                   │
│  │ (GPT-4o-mini)    │                                                   │
│  └───┬────┬────┬────┘                                                   │
│      │    │    │                                                         │
│      │    │    └───────────────┐                                         │
│      │    │                   │                                         │
│      ▼    ▼                   ▼                                         │
│  ┌──────┐ ┌──────────┐ ┌───────────┐                                   │
│  │Simple│ │Moderate  │ │ Complex   │                                   │
│  │      │ │          │ │           │                                   │
│  │$0.15 │ │$2.50     │ │$2.50      │                                   │
│  │/1M   │ │/1M in    │ │/1M in     │                                   │
│  │tokens│ │tokens    │ │tokens     │                                   │
│  └──┬───┘ └────┬─────┘ └─────┬─────┘                                   │
│     │          │             │                                          │
│     ▼          ▼             ▼                                          │
│  ┌──────────────────────────────────┐                                   │
│  │         Response                 │                                   │
│  └──────────────┬───────────────────┘                                   │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────────┐                                   │
│  │     Quality Evaluation           │                                   │
│  │  ┌────────────────────────────┐  │                                   │
│  │  │ If quality < threshold:    │  │                                   │
│  │  │ ESCALATE to GPT-4o        │  │                                   │
│  │  └────────────────────────────┘  │                                   │
│  └──────────────────────────────────┘                                   │
│                                                                          │
│  SAVINGS SUMMARY:                                                       │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │  Simple queries (60%):  $0.15/M  vs  $2.50/M  = 94% saved   │       │
│  │  Moderate queries (25%): $2.50/M vs  $2.50/M  = same cost   │       │
│  │  Complex queries (15%): $2.50/M  vs  $2.50/M  = same cost   │       │
│  │  Cache hits (+15%):     $0.00    vs  $2.50/M  = 100% saved  │       │
│  │  ──────────────────────────────────────────────────────────  │       │
│  │  TOTAL SAVINGS: ~60-70% compared to all-GPT-4o               │       │
│  └──────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```
