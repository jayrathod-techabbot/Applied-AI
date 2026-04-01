# Module 8: Diagrams — CI/CD for AI

This directory contains text-based and Mermaid diagrams illustrating key concepts from Module 8.

---

## 1. End-to-End CI/CD Pipeline for LLM Applications

### Mermaid Diagram

```mermaid
graph LR
    A[Code Push] --> B[Build]
    B --> C[Unit Tests]
    C --> D[Integration Tests]
    D --> E[AI Evaluation Gate]
    E -->|Score >= 0.80| F[Build Container]
    E -->|Score < 0.80| X[Pipeline Fail]
    F --> G[Push to ACR]
    G --> H[Deploy Staging]
    H --> I[Smoke Tests]
    I -->|Pass| J[Canary Deploy 10%]
    I -->|Fail| X
    J --> K{Monitor Canary}
    K -->|Healthy| L[Promote to 50%]
    K -->|Degraded| M[Rollback]
    L --> N{Monitor 50%}
    N -->|Healthy| O[Full Rollout 100%]
    N -->|Degraded| M
    O --> P[Production Monitor]
    P -->|Anomaly| M

    style A fill:#e1f5fe
    style E fill:#fff3e0
    style J fill:#f3e5f5
    style O fill:#e8f5e9
    style X fill:#ffebee
    style M fill:#ffebee
```

### ASCII Pipeline Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE FOR LLM APPLICATIONS                            │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐                  │
│  │  SOURCE   │──▶│  BUILD   │──▶│   TEST   │──▶│   EVALUATE   │                 │
│  │          │   │          │   │          │   │  (AI Gate)   │                  │
│  │ git push │   │ pip deps │   │ unit     │   │ prompt eval  │                  │
│  │ PR merge │   │ docker   │   │ integr.  │   │ semantic sim │                  │
│  │ schedule │   │ ruff     │   │ linting  │   │ benchmark    │                  │
│  └──────────┘   └──────────┘   └──────────┘   └──────┬───────┘                  │
│                                                       │                          │
│                                              score >= 0.80?                       │
│                                                   ┌───┴───┐                      │
│                                                   │       │                      │
│                                                 YES      NO                      │
│                                                   │       │                      │
│                                                   ▼       ▼                      │
│                                          ┌────────────┐  FAIL                   │
│                                          │  PACKAGE   │  notify                 │
│                                          │ docker push│  team                   │
│                                          │ acr upload │                         │
│                                          └─────┬──────┘                         │
│                                                │                                │
│                                                ▼                                │
│                                     ┌────────────────────┐                       │
│                                     │  DEPLOY STAGING    │                       │
│                                     │  container apps    │                       │
│                                     │  slot swap         │                       │
│                                     └─────────┬──────────┘                       │
│                                               │                                  │
│                                               ▼                                  │
│                                    ┌─────────────────────┐                        │
│                                    │  SMOKE TESTS        │                        │
│                                    │  health endpoints   │                        │
│                                    │  synthetic queries  │                        │
│                                    └─────────┬───────────┘                        │
│                                              │                                   │
│                                              ▼                                   │
│                                   ┌──────────────────────┐                        │
│                                   │  CANARY DEPLOY       │                        │
│                                   │  10% → monitor       │                        │
│                                   │  50% → monitor       │                        │
│                                   │  100% → full rollout │                        │
│                                   └─────────┬────────────┘                        │
│                                             │                                    │
│                                             ▼                                    │
│                                  ┌───────────────────────┐                        │
│                                  │  PRODUCTION MONITOR   │                        │
│                                  │  latency / errors     │                        │
│                                  │  quality metrics      │                        │
│                                  │  drift detection      │                        │
│                                  └───────────┬───────────┘                        │
│                                              │                                   │
│                                     anomaly? ┼                                   │
│                                         ┌────┴────┐                              │
│                                        YES       NO                              │
│                                         │        │                               │
│                                         ▼        ▼                               │
│                                    ROLLBACK    HEALTHY                            │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Model Versioning Architecture

### Mermaid Diagram

```mermaid
graph TB
    subgraph Dev["Developer Workflow"]
        A[Code Change] --> B[Git Commit]
        B --> C[Git Push]
    end

    subgraph Versioning["Version Control Layer"]
        D[Git Repository<br/>Code + Config]
        E[DVC Remote<br/>Data + Models]
        F[MLflow Server<br/>Experiments + Registry]
    end

    subgraph Registry["Model Registry"]
        G[Model v1.0<br/>Staging]
        H[Model v1.1<br/>Production]
        I[Model v2.0<br/>Archived]
    end

    C --> D
    D --> E
    D --> F
    F --> G
    F --> H
    F --> I

    subgraph Deploy["Deployment"]
        J[CI/CD Pipeline]
        K[Fetch Model from Registry]
        L[Deploy to Container App]
    end

    H --> J
    J --> K
    K --> L

    style Dev fill:#e1f5fe
    style Versioning fill:#f3e5f5
    style Registry fill:#fff3e0
    style Deploy fill:#e8f5e9
```

### ASCII Versioning Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODEL VERSIONING ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        DEVELOPER WORKFLOW                            │    │
│  │                                                                      │    │
│  │   ┌──────────┐    ┌──────────────┐    ┌─────────────────────────┐   │    │
│  │   │  Write   │───▶│  git commit  │───▶│  dvc add + dvc push     │   │    │
│  │   │  Code    │    │  git push    │    │  (track data/models)    │   │    │
│  │   └──────────┘    └──────┬───────┘    └────────────┬────────────┘   │    │
│  │                          │                          │                │    │
│  └──────────────────────────┼──────────────────────────┼────────────────┘    │
│                             │                          │                     │
│                             ▼                          ▼                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      VERSION CONTROL LAYER                           │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐  │   │
│  │  │  Git Repo       │  │  DVC Remote     │  │  MLflow Server       │  │   │
│  │  │                 │  │                 │  │                      │  │   │
│  │  │  • Source code  │  │  • Datasets     │  │  • Experiment logs   │  │   │
│  │  │  • Config files │  │  • Model weights│  │  • Parameters        │  │   │
│  │  │  • Prompt YAML  │  │  • Artifacts    │  │  • Metrics           │  │   │
│  │  │  • IaC templates│  │                 │  │  • Model Registry    │  │   │
│  │  └─────────────────┘  └─────────────────┘  └──────────┬───────────┘  │   │
│  └────────────────────────────────────────────────────────┼──────────────┘   │
│                                                           │                  │
│                                                           ▼                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        MODEL REGISTRY                                │   │
│  │                                                                       │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │   │
│  │  │  llama3-8b    │  │  llama3-8b    │  │  llama3-8b    │            │   │
│  │  │  v1.0         │  │  v1.1         │  │  v2.0         │            │   │
│  │  │  ┌─────────┐  │  │  ┌─────────┐  │  │  ┌─────────┐  │            │   │
│  │  │  │Staging  │  │  │  │Production│  │  │  │Archived │  │            │   │
│  │  │  └─────────┘  │  │  └─────────┘  │  │  └─────────┘  │            │   │
│  │  └───────────────┘  └───────┬───────┘  └───────────────┘            │   │
│  └──────────────────────────────┼───────────────────────────────────────┘   │
│                                 │                                            │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        DEPLOYMENT                                    │   │
│  │                                                                       │   │
│  │   CI/CD Pipeline ──▶ Fetch Model ──▶ Build Container ──▶ Deploy      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Canary Deployment Traffic Flow

### Mermaid Diagram

```mermaid
graph TD
    Users[Users] --> LB[Load Balancer / Ingress]

    LB -->|90% traffic| Stable[Stable Version<br/>v1.1 — Production]
    LB -->|10% traffic| Canary[Canary Version<br/>v1.2 — New Release]

    Stable --> Monitor1[Metrics: OK]
    Canary --> Monitor2[Metrics: Check]

    Monitor2 -->|Healthy| Decision{Decision}
    Monitor2 -->|Error rate > 1%| Rollback[Rollback to v1.1]
    Monitor2 -->|Latency > 2s| Rollback

    Decision -->|Increase traffic| Increase[Canary → 50%]
    Increase --> Monitor3[Monitor at 50%]
    Monitor3 -->|Healthy| FullRollout[Canary → 100%]
    Monitor3 -->|Degraded| Rollback

    FullRollout --> Promote[Promote v1.2 to Stable]
    Rollback --> Stable

    style Users fill:#e1f5fe
    style Stable fill:#e8f5e9
    style Canary fill:#fff3e0
    style Rollback fill:#ffebee
    style FullRollout fill:#e8f5e9
    style Promote fill:#e8f5e9
```

### ASCII Canary Deployment

```
                        ┌──────────────┐
                        │    USERS     │
                        └──────┬───────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   LOAD BALANCER     │
                    │   (Traffic Router)  │
                    └──────┬────────┬─────┘
                           │        │
                    90%    │        │   10%
                           │        │
              ┌────────────┘        └────────────┐
              │                                   │
              ▼                                   ▼
   ┌──────────────────────┐          ┌──────────────────────┐
   │    STABLE (v1.1)     │          │    CANARY (v1.2)     │
   │                      │          │                      │
   │  • Proven stable     │          │  • New prompt/model  │
   │  • Full traffic      │          │  • Limited traffic   │
   │  • Baseline metrics  │          │  • Monitor closely   │
   └──────────┬───────────┘          └──────────┬───────────┘
              │                                   │
              ▼                                   ▼
   ┌──────────────────────┐          ┌──────────────────────┐
   │    METRICS           │          │    METRICS           │
   │                      │          │                      │
   │  error_rate: 0.2%   │          │  error_rate: ???     │
   │  latency_p95: 800ms │          │  latency_p95: ???    │
   │  quality: 0.92      │          │  quality: ???        │
   └──────────────────────┘          └──────────┬───────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │   CANARY HEALTHY?     │
                                    │                       │
                                    │  error_rate  < 1%?    │
                                    │  latency_p95 < 2s?    │
                                    │  quality     > 0.80?  │
                                    └───────┬───────┬───────┘
                                           ╱         ╲
                                         YES          NO
                                         ╱              ╲
                                        ▼                ▼
                              ┌──────────────┐   ┌──────────────┐
                              │ INCREASE     │   │   ROLLBACK   │
                              │ CANARY       │   │              │
                              │              │   │  Route 100%  │
                              │  10% → 50%   │   │  to stable   │
                              │  50% → 100%  │   │  v1.1        │
                              └──────┬───────┘   └──────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  PROMOTE     │
                              │  v1.2 as     │
                              │  new stable  │
                              └──────────────┘
```

---

## 4. Prompt Versioning Architecture

### Mermaid Diagram

```mermaid
graph TB
    subgraph Storage["Prompt Storage"]
        A[prompts/chatbot/system/v1.yaml]
        B[prompts/chatbot/system/v2.yaml]
        C[prompts/chatbot/summarization/v1.yaml]
        D[prompts/support/triage/v1.yaml]
    end

    subgraph Registry["Prompt Registry Service"]
        E[REST API]
        F[Version Resolver]
        G[Stage Manager<br/>draft → staging → production]
    end

    subgraph App["Application"]
        H[PromptClient.get<br/>service=chatbot<br/>prompt=system<br/>stage=production]
    end

    subgraph CI["CI/CD Integration"]
        I[PR: prompt change]
        J[Eval Gate]
        K[Deploy new version]
    end

    A --> E
    B --> E
    C --> E
    D --> E
    E --> F
    F --> G
    G --> H
    I --> J
    J -->|Pass| K
    K --> E

    style Storage fill:#f3e5f5
    style Registry fill:#fff3e0
    style App fill:#e1f5fe
    style CI fill:#e8f5e9
```

### ASCII Prompt Versioning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROMPT VERSIONING ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        GIT REPOSITORY                                 │   │
│  │                                                                       │   │
│  │   prompts/                                                            │   │
│  │   ├── chatbot/                                                        │   │
│  │   │   ├── system_prompt/                                              │   │
│  │   │   │   ├── v1.yaml    ← archived                                   │   │
│  │   │   │   ├── v2.yaml    ← production    ┌────────────────────┐       │   │
│  │   │   │   └── v3.yaml    ← staging       │ version: "3.0"     │       │   │
│  │   │   └── summarization/                  │ model: gpt-4o      │       │   │
│  │   │       ├── v1.yaml                     │ system: "..."      │       │   │
│  │   │       └── v2.yaml  ← production       │ eval_score: 0.87   │       │   │
│  │   └── support/                            └────────────────────┘       │   │
│  │       └── triage/                                                       │   │
│  │           └── v1.yaml                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     PROMPT REGISTRY SERVICE                           │   │
│  │                                                                       │   │
│  │   ┌─────────────┐    ┌──────────────┐    ┌───────────────────┐       │   │
│  │   │  REST API   │───▶│   Version    │───▶│  Stage Manager    │       │   │
│  │   │             │    │   Resolver   │    │                   │       │   │
│  │   │  GET /prompt│    │              │    │  draft            │       │   │
│  │   │  POST /prom │    │  "latest" →  │    │  staging          │       │   │
│  │   │  PUT /prom  │    │  "v2"        │    │  production ◄──── │───────│───│
│  │   └─────────────┘    └──────────────┘    │  deprecated       │       │   │
│  │                                           └───────────────────┘       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      APPLICATION RUNTIME                              │   │
│  │                                                                       │   │
│  │   prompt = registry.get(                                              │   │
│  │       service="chatbot",                                              │   │
│  │       prompt="system_prompt",                                         │   │
│  │       stage="production"  ← resolves to v2.yaml                      │   │
│  │   )                                                                   │   │
│  │                                                                       │   │
│  │   response = llm.chat(                                                │   │
│  │       system=prompt["system"],                                        │   │
│  │       user=user_input                                                 │   │
│  │   )                                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Rollback Decision Flow

### Mermaid Diagram

```mermaid
graph TD
    A[Production Monitoring] --> B{Error Rate > 1%?}
    B -->|Yes| C[TRIGGER ROLLBACK]
    B -->|No| D{P95 Latency > 2s?}
    D -->|Yes| C
    D -->|No| E{Quality Score < 0.80?}
    E -->|Yes| C
    E -->|No| F{User Complaints Spike?}
    F -->|Yes| C
    F -->|No| G[ALL HEALTHY]

    C --> H{Auto-Rollback Enabled?}
    H -->|Yes| I[Execute Rollback]
    H -->|No| J[Alert Team → Manual Decision]

    I --> K[Shift Traffic to Previous Version]
    J --> L{Team Approves Rollback?}
    L -->|Yes| K
    L -->|No| M[Continue Monitoring]

    K --> N[Notify Team]
    N --> O[Post-Incident Review]

    style C fill:#ffebee
    style G fill:#e8f5e9
    style I fill:#fff3e0
    style O fill:#e1f5fe
```

### ASCII Rollback Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                       ROLLBACK DECISION FLOW                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    ┌─────────────────────┐                            │
│                    │  PRODUCTION         │                            │
│                    │  MONITORING         │                            │
│                    └──────────┬──────────┘                            │
│                               │                                      │
│                    ┌──────────▼──────────┐                            │
│                    │  Check Error Rate   │                            │
│                    │  > 1%?              │                            │
│                    └──┬──────────────┬───┘                            │
│                      YES             NO                               │
│                       │               │                              │
│                       │    ┌──────────▼──────────┐                   │
│                       │    │  Check P95 Latency  │                   │
│                       │    │  > 2000ms?          │                   │
│                       │    └──┬──────────────┬───┘                   │
│                       │      YES             NO                      │
│                       │       │               │                     │
│                       │       │    ┌──────────▼──────────┐          │
│                       │       │    │  Check Quality      │          │
│                       │       │    │  Score < 0.80?      │          │
│                       │       │    └──┬──────────────┬───┘          │
│                       │      YES    NO               │              │
│                       │       │     │     ┌──────────▼──────────┐  │
│                       │       │     │     │  ALL METRICS OK     │  │
│                       │       │     │     │  Continue Monitor   │  │
│                       │       │     │     └─────────────────────┘  │
│                       │       │     │                              │
│               ┌───────▼───────▼─────┤                              │
│               │                     │                              │
│               ▼                     │                              │
│    ┌────────────────────┐           │                              │
│    │  AUTO-ROLLBACK     │           │                              │
│    │  ENABLED?          │           │                              │
│    └──┬─────────────┬───┘           │                              │
│      YES            NO              │                              │
│       │              │              │                              │
│       ▼              ▼              │                              │
│  ┌──────────┐  ┌───────────┐       │                              │
│  │ EXECUTE  │  │ ALERT     │       │                              │
│  │ ROLLBACK │  │ TEAM      │       │                              │
│  │          │  │ Manual    │       │                              │
│  │ Shift to │  │ Review    │       │                              │
│  │ previous │  │ Required  │       │                              │
│  │ version  │  └─────┬─────┘       │                              │
│  └────┬─────┘        │             │                              │
│       │              ▼             │                              │
│       │        ┌───────────┐       │                              │
│       │        │ APPROVE?  │       │                              │
│       │        └──┬────┬───┘       │                              │
│       │          YES    NO         │                              │
│       │           │      │         │                              │
│       ◀───────────┘      │         │                              │
│       │                  ▼         │                              │
│       ▼           ┌───────────┐    │                              │
│  ┌──────────┐     │ CONTINUE  │    │                              │
│  │ NOTIFY   │     │ MONITOR   │    │                              │
│  │ TEAM     │     └───────────┘    │                              │
│  └────┬─────┘                      │                              │
│       │                            │                              │
│       ▼                            │                              │
│  ┌──────────────┐                  │                              │
│  │ POST-MORTEM  │                  │                              │
│  │ REVIEW       │                  │                              │
│  └──────────────┘                  │                              │
│                                    │                              │
└────────────────────────────────────┴──────────────────────────────┘
```

---

## 6. Experiment Tracking Flow

### Mermaid Diagram

```mermaid
graph LR
    subgraph Experiment["Experiment Run"]
        A[Define Parameters] --> B[Train Model]
        B --> C[Log Metrics]
        C --> D[Save Artifacts]
    end

    subgraph Tracking["MLflow Tracking Server"]
        E[(Experiment DB)]
        F[Run Comparison UI]
    end

    subgraph Registry["Model Registry"]
        G[Version 1.0<br/>Stage: None]
        H[Version 1.1<br/>Stage: Staging]
        I[Version 1.2<br/>Stage: Production]
    end

    A --> E
    C --> E
    D --> E
    E --> F
    F -->|Best Run| G
    G -->|Promote| H
    H -->|Promote| I

    subgraph Deploy["Deployment"]
        J[CI/CD Pipeline]
        K[Fetch Production Model]
        L[Deploy]
    end

    I --> J
    J --> K
    K --> L

    style Experiment fill:#e1f5fe
    style Tracking fill:#f3e5f5
    style Registry fill:#fff3e0
    style Deploy fill:#e8f5e9
```

### ASCII Experiment Tracking Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       EXPERIMENT TRACKING FLOW                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                        EXPERIMENT RUN                               │     │
│  │                                                                     │     │
│  │  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌──────────┐  │     │
│  │  │  Define    │──▶│   Train    │──▶│    Log     │──▶│  Save    │  │     │
│  │  │  Params    │   │   Model    │   │  Metrics   │   │ Artifacts│  │     │
│  │  │            │   │            │   │            │   │          │  │     │
│  │  │ lr, epochs │   │ GPU hours  │   │ loss, acc  │   │ model.bin│  │     │
│  │  └────────────┘   └────────────┘   └─────┬──────┘   └────┬─────┘  │     │
│  └───────────────────────────────────────────┼───────────────┼────────┘     │
│                                              │               │              │
│                                              ▼               ▼              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                     MLFLOW TRACKING SERVER                         │     │
│  │                                                                     │     │
│  │    ┌─────────────────────┐     ┌──────────────────────────┐       │     │
│  │    │  (Experiment DB)    │────▶│  Run Comparison UI       │       │     │
│  │    │                     │     │                          │       │     │
│  │    │  Run 1: acc=0.89   │     │  Sort by accuracy        │       │     │
│  │    │  Run 2: acc=0.92   │     │  Best run → promote      │       │     │
│  │    │  Run 3: acc=0.91   │     │                          │       │     │
│  │    └─────────────────────┘     └────────────┬─────────────┘       │     │
│  └─────────────────────────────────────────────┼─────────────────────┘     │
│                                                │                            │
│                                                ▼                            │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                       MODEL REGISTRY                               │     │
│  │                                                                     │     │
│  │   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐     │     │
│  │   │  v1.0         │    │  v1.1         │    │  v1.2         │     │     │
│  │   │  None         │───▶│  Staging      │───▶│  Production   │     │     │
│  │   │               │    │               │    │               │     │     │
│  │   │  [evaluate]   │    │  [validate]   │    │  [deploy]     │     │     │
│  │   └───────────────┘    └───────────────┘    └───────┬───────┘     │     │
│  └─────────────────────────────────────────────────────┼─────────────┘     │
│                                                        │                    │
│                                                        ▼                    │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                        DEPLOYMENT                                  │     │
│  │                                                                     │     │
│  │   CI/CD Pipeline ──▶ Fetch Model ──▶ Build Container ──▶ Deploy   │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Blue-Green Deployment Strategy

### Mermaid Diagram

```mermaid
graph TD
    subgraph Before["Before: All traffic on Blue"]
        LB1[Load Balancer] -->|100%| Blue1[Blue v1.1 — ACTIVE]
        Green1[Green v1.2 — IDLE]
    end

    subgraph After["After: Switch to Green"]
        LB2[Load Balancer] -->|100%| Green2[Green v1.2 — ACTIVE]
        Blue2[Blue v1.1 — STANDBY]
    end

    Before -->|Atomic Switch| After
    After -->|Rollback if needed| Before

    style Blue1 fill:#bbdefb
    style Green1 fill:#e0e0e0
    style Green2 fill:#c8e6c9
    style Blue2 fill:#e0e0e0
```

### ASCII Blue-Green Deployment

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       BLUE-GREEN DEPLOYMENT                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BEFORE (Stable)                                                            │
│   ─────────────                                                              │
│                                                                              │
│                    ┌───────────────────┐                                     │
│                    │   LOAD BALANCER   │                                     │
│                    └───────┬───┬───────┘                                     │
│                          ╱     ╲                                             │
│                    100% ╱       ╲ 0%                                         │
│                       ╱         ╲                                            │
│              ┌───────▼───┐  ┌────▼──────┐                                   │
│              │   BLUE    │  │  GREEN    │                                   │
│              │  v1.1     │  │  v1.2     │                                   │
│              │  ┌─────┐  │  │  ┌─────┐  │                                   │
│              │  │ACTIVE│  │  │  │IDLE │  │                                   │
│              │  └─────┘  │  │  └─────┘  │                                   │
│              └───────────┘  └───────────┘                                   │
│                                                                              │
│                                                                              │
│   AFTER (New Release)                                                        │
│   ───────────────────                                                        │
│                                                                              │
│                    ┌───────────────────┐                                     │
│                    │   LOAD BALANCER   │                                     │
│                    └───────┬───┬───────┘                                     │
│                          ╱     ╲                                             │
│                     0% ╱       ╲ 100%                                        │
│                      ╱         ╲                                             │
│              ┌───────▼───┐  ┌────▼──────┐                                   │
│              │   BLUE    │  │  GREEN    │                                   │
│              │  v1.1     │  │  v1.2     │                                   │
│              │  ┌─────┐  │  │  ┌─────┐  │                                   │
│              │  │STDBY│  │  │  │ACTIVE│  │                                   │
│              │  └─────┘  │  │  └─────┘  │                                   │
│              └───────────┘  └───────────┘                                   │
│                                                                              │
│   Rollback: flip traffic back to Blue instantly                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. DVC Pipeline Architecture

### Mermaid Diagram

```mermaid
graph LR
    subgraph Source["Source Code (Git)"]
        A[src/prepare_data.py]
        B[src/train.py]
        C[src/evaluate.py]
        D[params.yaml]
    end

    subgraph Pipeline["DVC Pipeline (dvc.yaml)"]
        E[prepare] --> F[train]
        F --> G[evaluate]
    end

    subgraph Remote["DVC Remote Storage"]
        H[data/processed/]
        I[models/fine_tuned/]
        J[metrics/train.json]
        K[metrics/eval.json]
    end

    A --> E
    B --> F
    C --> G
    D -.->|params| F
    E -->|outs| H
    F -->|outs| I
    F -->|metrics| J
    G -->|metrics| K

    style Source fill:#e1f5fe
    style Pipeline fill:#f3e5f5
    style Remote fill:#fff3e0
```

### ASCII DVC Pipeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          DVC PIPELINE ARCHITECTURE                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                       SOURCE CODE (Git)                            │     │
│  │                                                                     │     │
│  │   src/prepare_data.py    src/train.py    src/evaluate.py          │     │
│  │   params.yaml                                                       │     │
│  └────────────┬──────────────────┬──────────────────┬─────────────────┘     │
│               │                  │                  │                        │
│               ▼                  ▼                  ▼                        │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                       DVC PIPELINE                                  │     │
│  │                                                                     │     │
│  │   ┌──────────┐      ┌──────────┐      ┌──────────┐                │     │
│  │   │ PREPARE  │─────▶│  TRAIN   │─────▶│ EVALUATE │                │     │
│  │   │          │      │          │      │          │                │     │
│  │   │ deps:    │      │ deps:    │      │ deps:    │                │     │
│  │   │  src.py  │      │  src.py  │      │  src.py  │                │     │
│  │   │  raw/    │      │  proc./  │      │  model/  │                │     │
│  │   │          │      │ params:  │      │          │                │     │
│  │   │ outs:    │      │  lr, ep  │      │ metrics: │                │     │
│  │   │  proc./  │      │          │      │  eval.js │                │     │
│  │   └──────────┘      │ outs:    │      └──────────┘                │     │
│  │                      │  model/  │                                   │     │
│  │                      │ metrics: │                                   │     │
│  │                      │  train.j │                                   │     │
│  │                      └──────────┘                                   │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│               │                  │                  │                        │
│               ▼                  ▼                  ▼                        │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                       DVC REMOTE STORAGE                           │     │
│  │                                                                     │     │
│  │   data/processed/    models/fine_tuned/    metrics/                │     │
│  │                                                                     │     │
│  │   (Azure Blob, S3, GCS — actual files stored here)                │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│   Commands:                                                                  │
│   dvc repro        → Reproduce pipeline                                      │
│   dvc push         → Upload artifacts to remote                              │
│   dvc pull         → Download artifacts from remote                          │
│   dvc metrics diff → Compare metrics across runs                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```
