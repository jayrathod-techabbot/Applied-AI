# Module 9: Diagrams — Monitoring & Observability

This directory contains text-based and Mermaid diagrams illustrating key concepts from Module 9.

---

## 1. End-to-End LLM Observability Architecture

### Mermaid Diagram

```mermaid
graph TB
    subgraph Users["User Layer"]
        U1[Web App]
        U2[Mobile App]
        U3[API Client]
    end

    subgraph Gateway["API Gateway"]
        AG[API Gateway + Rate Limiting]
    end

    subgraph Services["Application Services"]
        S1[RAG Pipeline]
        S2[Agent Service]
        S3[Chat Service]
    end

    subgraph External["External APIs"]
        LLM1[OpenAI GPT-4o]
        LLM2[Anthropic Claude]
        EMB[Embedding Model]
    end

    subgraph Telemetry["Telemetry Layer"]
        OTel[OTel Collector]
    end

    subgraph Storage["Observability Backends"]
        T[Traces - Jaeger/Tempo]
        M[Metrics - Prometheus]
        L[Logs - Elasticsearch]
    end

    subgraph Analysis["Analysis & Alerting"]
        G[Grafana Dashboard]
        A[Alert Manager]
        D[Drift Detector]
    end

    U1 & U2 & U3 --> AG
    AG --> S1 & S2 & S3
    S1 --> EMB
    S1 & S2 & S3 --> LLM1 & LLM2

    S1 & S2 & S3 -.->|"traces, metrics, logs"| OTel
    OTel --> T & M & L
    T & M & L --> G
    M --> A
    M --> D
    A -->|"alerts"| PagerDuty[PagerDuty/Slack]

    style Users fill:#e1f5fe
    style Gateway fill:#fff3e0
    style Services fill:#e8f5e9
    style External fill:#f3e5f5
    style Telemetry fill:#fff9c4
    style Storage fill:#fce4ec
    style Analysis fill:#e0f2f1
```

### ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LLM OBSERVABILITY ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                                │
│  │  Web App  │  │  Mobile   │  │  API      │   USER LAYER                   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘                                │
│        │              │              │                                       │
│        ▼              ▼              ▼                                       │
│  ┌─────────────────────────────────────────┐                                │
│  │          API Gateway + Auth             │   GATEWAY                      │
│  │     (Rate Limiting, Request Routing)    │                                │
│  └──────────────────┬──────────────────────┘                                │
│                     │                                                        │
│        ┌────────────┼────────────┐                                          │
│        ▼            ▼            ▼                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                                    │
│  │   RAG    │ │  Agent   │ │  Chat    │   SERVICES                         │
│  │ Pipeline │ │ Service  │ │ Service  │                                    │
│  │          │ │          │ │          │                                     │
│  │ Embed →  │ │ Think →  │ │ Generate │                                    │
│  │ Search → │ │ Act →    │ │ Response │                                    │
│  │ Generate │ │ Observe  │ │          │                                    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                                    │
│       │            │            │                                           │
│       ▼            ▼            ▼                                           │
│  ┌─────────────────────────────────────────┐   EXTERNAL                     │
│  │  OpenAI  │  Anthropic  │  Embeddings   │   APIS                         │
│  └─────────────────────────────────────────┘                                │
│                                                                              │
│  ════════════════════════════════════════════   TELEMETRY LAYER              │
│       │            │            │                                           │
│       ▼            ▼            ▼                                           │
│  ┌─────────────────────────────────────────┐                                │
│  │         OpenTelemetry Collector         │                                │
│  │  Receives → Processes → Routes          │                                │
│  └───┬────────────┬────────────┬───────────┘                                │
│      │            │            │                                            │
│      ▼            ▼            ▼                                            │
│  ┌────────┐  ┌──────────┐  ┌──────────┐                                    │
│  │ Traces │  │ Metrics  │  │  Logs    │   STORAGE                          │
│  │ Jaeger │  │Prometheus│  │ Elastic  │                                    │
│  └───┬────┘  └────┬─────┘  └────┬─────┘                                    │
│      │            │             │                                           │
│      ▼            ▼             ▼                                           │
│  ┌─────────────────────────────────────────┐                                │
│  │           Grafana Dashboard             │   ANALYSIS                     │
│  │  Traffic │ Latency │ Cost │ Quality     │                                │
│  └────────────────────┬────────────────────┘                                │
│                       │                                                      │
│                       ▼                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │         Alert Manager                   │   ALERTING                     │
│  │  Critical → Page │ Warning → Channel    │                                │
│  └─────────────────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Distributed Trace for a RAG Pipeline

### Mermaid Diagram

```mermaid
gantt
    title RAG Pipeline Trace - Request req_abc123 (Total: 1,850ms)
    dateFormat X
    axisFormat %L ms

    section Gateway
    Auth Validation           :a1, 0, 5
    Rate Limit Check          :a2, 0, 3

    section Retrieval
    Query Embedding           :b1, 5, 55
    Vector Search (top-5)     :b2, 55, 135
    Reranking                 :b3, 135, 185

    section LLM Generation
    Prompt Construction       :c1, 185, 190
    API Call (gpt-4o)         :c2, 190, 1790
    Response Parsing          :c3, 1790, 1835

    section Post-Processing
    Citation Formatting       :d1, 1835, 1850
```

### ASCII Trace Waterfall

```
Trace: rag-request-abc123 (Total: 1,850ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0ms        200ms       400ms       600ms       800ms      1000ms    1850ms
│          │           │           │           │           │          │
├─ api_gateway (5ms)
│ ██
│
├─ retrieval_pipeline (180ms)
│ ├─ query_embedding (50ms)
│ │ ██████████
│ ├─ vector_search (80ms)
│ │ ████████████████████
│ └─ reranking (50ms)
│   ██████████
│
├─ llm_generation (1,650ms)
│ ├─ prompt_construction (5ms)
│ │ █
│ ├─ api_call gpt-4o (1,600ms)     ← Bottleneck (86% of total time)
│ │ ████████████████████████████████████████████████████████████████████
│ └─ response_parsing (45ms)
│   █████████
│
└─ post_processing (15ms)
  ███

Breakdown:
  Retrieval:   180ms ( 9.7%)  ██████████
  LLM:       1,650ms (89.2%)  ████████████████████████████████████████████████
  Other:        20ms ( 1.1%)  █
```

---

## 3. Drift Detection Pipeline

### Mermaid Diagram

```mermaid
graph LR
    subgraph Reference["Reference Distribution (Training)"]
        REF[Embeddings<br/>Quality Scores<br/>Token Counts]
    end

    subgraph Current["Current Distribution (Production)"]
        CUR[Live Embeddings<br/>Live Quality Scores<br/>Live Token Counts]
    end

    subgraph Detection["Drift Detection"]
        KS[KS Test]
        PSI[PSI Calculator]
        EMB[Embedding<br/>Similarity]
    end

    subgraph Decision["Decision Engine"]
        COMP{Compare<br/>Thresholds}
    end

    subgraph Actions["Actions"]
        OK[✅ No Action]
        WATCH[👁️ Watch List]
        ALERT[🚨 Alert +<br/>Retrain Trigger]
    end

    REF --> KS & PSI & EMB
    CUR --> KS & PSI & EMB
    KS --> COMP
    PSI --> COMP
    EMB --> COMP
    COMP -->|p > 0.05, PSI < 0.1| OK
    COMP -->|0.1 < PSI < 0.2| WATCH
    COMP -->|p < 0.05 OR PSI > 0.2| ALERT

    style Reference fill:#e8f5e9
    style Current fill:#fff3e0
    style Detection fill:#e1f5fe
    style Decision fill:#f3e5f5
    style OK fill:#c8e6c9
    style WATCH fill:#fff9c4
    style ALERT fill:#ffcdd2
```

### ASCII Drift Detection Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DRIFT DETECTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────┐          ┌───────────────────┐                   │
│  │   REFERENCE DATA  │          │   CURRENT DATA    │                   │
│  │   (Training/Last  │          │   (Live Traffic)  │                   │
│  │    30 days)       │          │   (Rolling 24h)   │                   │
│  │                   │          │                   │                   │
│  │  • Embeddings     │          │  • Embeddings     │                   │
│  │  • Quality scores │          │  • Quality scores │                   │
│  │  • Token counts   │          │  • Token counts   │                   │
│  │  • Topic clusters │          │  • Topic clusters │                   │
│  └────────┬──────────┘          └────────┬──────────┘                   │
│           │                              │                              │
│           ▼                              ▼                              │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    STATISTICAL TESTS                           │     │
│  │                                                                │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐     │     │
│  │  │  KS Test     │  │  PSI         │  │  Embedding       │     │     │
│  │  │  (continuous │  │  (population │  │  Cosine Sim.     │     │     │
│  │  │   features)  │  │   stability) │  │  (semantic)      │     │     │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘     │     │
│  │         │                 │                    │               │     │
│  │         ▼                 ▼                    ▼               │     │
│  │  ┌────────────────────────────────────────────────────────┐   │     │
│  │  │                  COMPOSITE SCORE                       │   │     │
│  │  │  score = w1*ks_stat + w2*psi + w3*(1-cosine_sim)      │   │     │
│  │  └────────────────────────┬───────────────────────────────┘   │     │
│  └───────────────────────────┼───────────────────────────────────┘     │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    DECISION THRESHOLDS                         │     │
│  │                                                                │     │
│  │  Score < 0.1  ──▶  ✅  No drift detected. Continue monitoring  │     │
│  │  0.1 ≤ s < 0.3 ──▶  👁️  Moderate drift. Add to watch list     │     │
│  │  Score ≥ 0.3  ──▶  🚨  Significant drift. Trigger alert +     │     │
│  │                       evaluate retraining pipeline             │     │
│  └────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Alert Routing and Escalation

### Mermaid Diagram

```mermaid
graph TD
    METRIC[Metric Threshold Exceeded] --> EVAL{Evaluate Severity}

    EVAL -->|Error Rate > 10%| CRIT[CRITICAL]
    EVAL -->|P95 Latency > 5s| WARN[WARNING]
    EVAL -->|Cost > 80% Budget| WARN
    EVAL -->|New Model Deployed| INFO[INFO]

    CRIT --> PAGE[Page On-Call Engineer]
    CRIT --> AUTO[Auto-Failover if Available]

    WARN --> CHANNEL[Post to #llm-alerts]
    WARN --> TICKET[Create Investigation Ticket]

    INFO --> LOG[Log for Awareness]

    PAGE --> ACK{Acknowledged<br/>in 15 min?}
    ACK -->|Yes| INVESTIGATE[Investigate]
    ACK -->|No| ESCALATE[Escalate to Manager]

    style CRIT fill:#ffcdd2
    style WARN fill:#fff9c4
    style INFO fill:#c8e6c9
    style PAGE fill:#ffcdd2
    style ESCALATE fill:#ff8a80
```

### ASCII Alert Escalation Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ALERT ESCALATION MATRIX                            │
├──────────┬──────────────┬──────────────────┬────────────┬───────────────┤
│ Severity │ Condition    │ Channel          │ Response   │ Escalation    │
│          │              │                  │ Time       │               │
├──────────┼──────────────┼──────────────────┼────────────┼───────────────┤
│ CRITICAL │ Error rate   │ PagerDuty page   │ 15 min     │ → Manager     │
│          │ > 10%        │ + Slack #incidents│            │ at 30 min     │
│          │ Service down │                  │            │ → VP at 1 hr  │
├──────────┼──────────────┼──────────────────┼────────────┼───────────────┤
│ WARNING  │ P95 > 5s     │ Slack #llm-alerts│ 1 hour     │ → On-call     │
│          │ Cost > 80%   │ + Jira ticket    │            │ at 2 hours    │
│          │ PSI > 0.15   │                  │            │               │
├──────────┼──────────────┼──────────────────┼────────────┼───────────────┤
│ INFO     │ Deployment   │ Slack #llm-info  │ Next standup│ None         │
│          │ Traffic ±20% │ + Log entry      │            │               │
│          │ Model switch │                  │            │               │
└──────────┴──────────────┴──────────────────┴────────────┴───────────────┘
```

---

## 5. Monitoring Feedback Loop

### Mermaid Diagram

```mermaid
graph TD
    subgraph Monitor["1. MONITOR"]
        M1[Collect Traces]
        M2[Track Metrics]
        M3[Log User Feedback]
        M4[Detect Drift]
    end

    subgraph Analyze["2. ANALYZE"]
        A1[Find Failure Patterns]
        A2[Cluster Errors]
        A3[Correlate Signals]
        A4[Root Cause Analysis]
    end

    subgraph Improve["3. IMPROVE"]
        I1[Update Knowledge Base]
        I2[Refine Prompts]
        I3[Fine-tune Model]
        I4[Improve Retrieval]
    end

    subgraph Validate["4. VALIDATE"]
        V1[A/B Testing]
        V2[Canary Deployment]
        V3[Regression Suite]
        V4[Quality Evaluation]
    end

    Monitor --> Analyze
    Analyze --> Improve
    Improve --> Validate
    Validate -->|"Continuous"| Monitor

    style Monitor fill:#e1f5fe
    style Analyze fill:#fff3e0
    style Improve fill:#e8f5e9
    style Validate fill:#f3e5f5
```

### ASCII Feedback Loop

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  CONTINUOUS IMPROVEMENT FEEDBACK LOOP                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐         ┌──────────────┐                              │
│  │   MONITOR    │────────▶│   ANALYZE    │                              │
│  │              │         │              │                              │
│  │ • Traces     │         │ • Patterns   │                              │
│  │ • Metrics    │         │ • Clusters   │                              │
│  │ • Feedback   │         │ • Correlate  │                              │
│  │ • Drift      │         │ • Root cause │                              │
│  └──────────────┘         └──────┬───────┘                              │
│         ▲                        │                                       │
│         │                        ▼                                       │
│         │               ┌──────────────┐         ┌──────────────┐       │
│         │               │   IMPROVE    │────────▶│   VALIDATE   │       │
│         │               │              │         │              │       │
│         │               │ • KB update  │         │ • A/B test   │       │
│         │               │ • Prompts    │         │ • Canary     │       │
│         │               │ • Fine-tune  │         │ • Regression │       │
│         │               │ • Retrieval  │         │ • Quality    │       │
│         │               └──────────────┘         └──────┬───────┘       │
│         │                                               │               │
│         └───────────────────────────────────────────────┘               │
│                         Deploy improvements                             │
│                         and continue monitoring                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Cost Tracking Architecture

### Mermaid Diagram

```mermaid
graph LR
    REQ[LLM Request] --> TRACK[Cost Tracker]
    TRACK --> CALC{Calculate Cost}
    CALC -->|token_count × rate| STORE[Time Series DB]

    STORE --> DASH[Cost Dashboard]
    STORE --> ALERT_BUDGET{Budget Check}
    STORE --> ATTRIB[Cost Attribution]

    ALERT_BUDGET -->|< 50%| GREEN[✅ On Track]
    ALERT_BUDGET -->|50-80%| YELLOW[⚠️ Warning]
    ALERT_BUDGET -->|> 80%| RED[🚨 Alert]
    ALERT_BUDGET -->|> 100%| THROTTLE[🛑 Throttle]

    ATTRIB --> BY_FEATURE[By Feature]
    ATTRIB --> BY_USER[By User]
    ATTRIB --> BY_MODEL[By Model]

    style GREEN fill:#c8e6c9
    style YELLOW fill:#fff9c4
    style RED fill:#ffcdd2
    style THROTTLE fill:#ff8a80
```

### ASCII Cost Tracking Dashboard

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COST TRACKING DASHBOARD                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Daily Budget: $50.00          Current Spend: $32.15 (64.3%)           │
│  ████████████████████████████████████░░░░░░░░░░░░░░░░░                  │
│                                                                         │
│  ┌───────────────────────┬───────────────────────┐                      │
│  │  BY MODEL             │  BY FEATURE           │                      │
│  │  gpt-4o:    $21.30    │  Chat:      $15.20    │                      │
│  │  gpt-4o-mini: $7.50   │  RAG:       $10.80    │                      │
│  │  claude-3.5:  $3.35   │  Agent:      $6.15    │                      │
│  └───────────────────────┴───────────────────────┘                      │
│                                                                         │
│  ┌──────────────────────────────────────────────┐                       │
│  │  HOURLY TREND (last 24h)                     │                       │
│  │  $2.50│    ╭─╮                               │                       │
│  │  $2.00│ ╭──╯  ╰──╮   ╭╮                     │                       │
│  │  $1.50│─╯        ╰───╯╰─╮                   │                       │
│  │  $1.00│                 ╰──                  │                       │
│  │  $0.50│                                      │                       │
│  │       └──────────────────────────            │                       │
│  │       00:00    06:00   12:00  18:00  24:00   │                       │
│  └──────────────────────────────────────────────┘                       │
│                                                                         │
│  Alerts: ⚠️ gpt-4o usage up 23% vs yesterday                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---
