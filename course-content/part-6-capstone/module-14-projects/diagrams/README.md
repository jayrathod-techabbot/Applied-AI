# Module 14: Production AI Projects — Diagrams

This directory contains ASCII and Mermaid diagrams for all four capstone projects.

---

## Table of Contents

- [1. Project Architecture Overview](#1-project-architecture-overview)
- [2. Book Recommender Pipeline](#2-book-recommender-pipeline)
- [3. Customer Support State Machine](#3-customer-support-state-machine)
- [4. Market Intelligence Agent Flow](#4-market-intelligence-agent-flow)
- [5. Multi-Agent Researcher Architecture](#5-multi-agent-researcher-architecture)
- [6. Azure Infrastructure Layout](#6-azure-infrastructure-layout)
- [7. Production Deployment Flow](#7-production-deployment-flow)

---

## 1. Project Architecture Overview

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Production AI Projects — Architecture                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Client Layer                                 │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │    │
│  │  │ Book Rec │  │ Support  │  │ Market   │  │ Multi-Agent      │    │    │
│  │  │ UI       │  │ Chat UI  │  │ Intel UI │  │ Research UI      │    │    │
│  │  │ (React)  │  │ (React)  │  │ (React)  │  │ (React)          │    │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘    │    │
│  └───────┼──────────────┼──────────────┼─────────────────┼──────────────┘    │
│          │              │              │                 │                   │
│  ┌───────▼──────────────▼──────────────▼─────────────────▼──────────────┐    │
│  │                         API Gateway                                   │    │
│  │  Azure API Management: Auth · Rate Limit · Routing · Caching         │    │
│  └────────────────────────────┬─────────────────────────────────────────┘    │
│                               │                                              │
│  ┌────────────────────────────▼─────────────────────────────────────────┐    │
│  │                      Application Layer                                │    │
│  │  ┌─────────────────┐ ┌──────────────┐ ┌──────────────────────────┐   │    │
│  │  │ Book Recommender│ │ Support Eng. │ │ Market Intelligence      │   │    │
│  │  │ FastAPI         │ │ FastAPI +    │ │ + Multi-Agent Researcher │   │    │
│  │  │ (AI Search)     │ │ LangGraph    │ │ (CrewAI + LangChain)     │   │    │
│  │  └─────────────────┘ └──────────────┘ └──────────────────────────┘   │    │
│  │                       Azure Container Apps (Auto-scaling)             │    │
│  └────────────────────────────┬─────────────────────────────────────────┘    │
│                               │                                              │
│  ┌────────────────────────────▼─────────────────────────────────────────┐    │
│  │                         Data Layer                                    │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐   │    │
│  │  │ Azure AI   │ │ Cosmos DB  │ │ Blob Store │ │ Azure OpenAI     │   │    │
│  │  │ Search     │ │ (Sessions, │ │ (Raw docs, │ │ (GPT-4o,         │   │    │
│  │  │ (Vectors)  │ │  Memory)   │ │  reports)  │ │  Embeddings)     │   │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────────┘   │    │
│  │  ┌────────────┐ ┌────────────┐                                       │    │
│  │  │ Redis Cache│ │ Key Vault  │                                       │    │
│  │  │ (Hot data) │ │ (Secrets)  │                                       │    │
│  │  └────────────┘ └────────────┘                                       │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │                      Observability                                     │    │
│  │  Azure Monitor · Application Insights · Log Analytics · Dashboards    │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    subgraph Client["Client Layer"]
        UI1[Book Recommender UI]
        UI2[Support Chat UI]
        UI3[Market Intel UI]
        UI4[Research UI]
    end

    subgraph Gateway["API Gateway"]
        APIM[Azure API Management]
    end

    subgraph Apps["Application Layer - Container Apps"]
        API1[Book Recommender API]
        API2[Support Engine API]
        API3[Market Intel API]
        API4[Research API]
    end

    subgraph Data["Data Layer"]
        AISearch[Azure AI Search]
        Cosmos[Cosmos DB]
        Blob[Blob Storage]
        OpenAI[Azure OpenAI]
        Redis[Redis Cache]
        KV[Key Vault]
    end

    subgraph Obs["Observability"]
        Monitor[Azure Monitor]
        AppInsights[Application Insights]
        Logs[Log Analytics]
    end

    UI1 --> APIM
    UI2 --> APIM
    UI3 --> APIM
    UI4 --> APIM

    APIM --> API1
    APIM --> API2
    APIM --> API3
    APIM --> API4

    API1 --> AISearch
    API1 --> Cosmos
    API1 --> OpenAI
    API1 --> Redis

    API2 --> AISearch
    API2 --> Cosmos
    API2 --> OpenAI

    API3 --> Blob
    API3 --> AISearch
    API3 --> OpenAI

    API4 --> Cosmos
    API4 --> Blob
    API4 --> OpenAI

    API1 -.-> Monitor
    API2 -.-> Monitor
    API3 -.-> Monitor
    API4 -.-> Monitor

    Monitor --> AppInsights
    Monitor --> Logs
```

---

## 2. Book Recommender Pipeline

### ASCII Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        Book Recommender Pipeline                            │
│                                                                             │
│  User Query                                                                 │
│     │                                                                       │
│     ▼                                                                       │
│  ┌─────────────────┐                                                        │
│  │  Query Analyzer │  ← GPT-4o-mini: Understand intent, extract filters    │
│  │  (LLM)          │     (genre, author, year, mood)                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Embedding      │  ← text-embedding-3-small: Convert query to vector     │
│  │  Generator      │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    Azure AI Search                               │       │
│  │                                                                  │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │       │
│  │  │ Vector Search│  │ BM25 Search  │  │ Semantic Ranking     │  │       │
│  │  │ (1536-dim)   │  │ (Keywords)   │  │ (Cross-encoder)      │  │       │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │       │
│  │         │                 │                     │              │       │
│  │         └─────────────────┼─────────────────────┘              │       │
│  │                           ▼                                    │       │
│  │              ┌─────────────────────────┐                       │       │
│  │              │  Reciprocal Rank Fusion │                       │       │
│  │              │  (Combined scoring)     │                       │       │
│  │              └────────────┬────────────┘                       │       │
│  └───────────────────────────┼────────────────────────────────────┘       │
│                              │                                             │
│                              ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                    Re-Ranking Layer                              │      │
│  │                                                                  │      │
│  │  Base Score × Genre Boost × Rating Boost × Diversity Factor     │      │
│  │                                                                  │      │
│  │  Input: 20 candidates  →  Output: Top 5 personalized results    │      │
│  └────────────────────────────┬────────────────────────────────────┘      │
│                               │                                           │
│                               ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │              LLM Explanation Generator                           │      │
│  │                                                                  │      │
│  │  For each book: "Based on your interest in [X], you'll like     │      │
│  │  this because [Y]. It shares [Z] with books you've enjoyed."    │      │
│  └────────────────────────────┬────────────────────────────────────┘      │
│                               │                                           │
│                               ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                    Response Assembly                             │      │
│  │                                                                  │      │
│  │  [Book Title, Author, Cover, Score, Explanation, Buy Link] × 5  │      │
│  └─────────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart LR
    A[User Query] --> B[Query Analyzer\nGPT-4o-mini]
    B --> C[Embedding Generator\ntext-embedding-3-small]
    C --> D[Azure AI Search]

    subgraph Search["Azure AI Search"]
        D1[Vector Search]
        D2[BM25 Search]
        D3[Semantic Ranking]
        D4[RRF Fusion]
        D1 --> D4
        D2 --> D4
        D3 --> D4
    end

    D --> D1
    D --> D2
    D --> D3
    D4 --> E[Re-Ranking Layer]
    E --> F[LLM Explanation\nGenerator]
    F --> G[Response Assembly]
    G --> H[Client Response]

    style Search fill:#e1f5fe
    style E fill:#fff3e0
    style F fill:#f3e5f5
```

---

## 3. Customer Support State Machine

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Customer Support Engine — LangGraph State Machine          │
│                                                                              │
│                               ┌─────────┐                                    │
│                          ┌───▶│  START  │                                    │
│                          │    └────┬────┘                                    │
│                          │         │                                         │
│                          │         ▼                                         │
│                          │    ┌─────────────────┐                            │
│                          │    │   Intent         │                            │
│                          │    │   Classifier     │                            │
│                          │    │  (GPT-4o-mini)   │                            │
│                          │    └────────┬─────────┘                            │
│                          │         │                                         │
│                          │    ┌──────┴──────┬───────────┐                    │
│                          │    ▼             ▼           ▼                    │
│                          │ ┌─────┐    ┌──────────┐ ┌─────────┐             │
│                          │ │ KB  │    │ Account  │ │Escalate │             │
│                          │ │Retr.│    │ Lookup   │ │ (Human) │             │
│                          │ │     │    │          │ │         │             │
│                          │ └──┬──┘    └────┬─────┘ └────┬────┘             │
│                          │    │            │            │                   │
│                          │    └────────────┼────────────┘                   │
│                          │         │                                         │
│                          │         ▼                                         │
│                          │    ┌─────────────────┐                            │
│                          │    │   Resolution     │                            │
│                          │    │   Reasoner       │                            │
│                          │    │  (GPT-4o + ctx)  │                            │
│                          │    └────────┬─────────┘                            │
│                          │         │                                         │
│                          │         ▼                                         │
│                          │    ┌─────────────────┐                            │
│                          │    │  Stream Response │                            │
│                          │    │  (WebSocket)     │                            │
│                          │    └────────┬─────────┘                            │
│                          │         │                                         │
│                          └─────────┘  (loop for multi-turn)                  │
│                               ┌────┴────┐                                    │
│                               │   END   │                                    │
│                               └─────────┘                                    │
│                                                                              │
│  State Schema:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  messages: list[Message]  (accumulated conversation)                │     │
│  │  intent: str                (billing, technical, account, etc.)     │     │
│  │  kb_results: list[Doc]      (retrieved knowledge articles)          │     │
│  │  account_info: dict         (user account data)                     │     │
│  │  resolution: str            (generated response)                    │     │
│  │  escalation_needed: bool    (flag for human handoff)                │     │
│  │  confidence: float          (classification confidence)             │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
stateDiagram-v2
    [*] --> START
    START --> Classifier

    state Classifier {
        [*] --> ClassifyIntent
        ClassifyIntent --> [*]
    }

    Classifier --> KBRetrieval: technical / general
    Classifier --> AccountLookup: billing / account
    Classifier --> Escalate: escalation

    KBRetrieval --> Resolver
    AccountLookup --> Resolver
    Escalate --> [*]

    state Resolver {
        [*] --> GenerateResponse
        GenerateResponse --> StreamOutput
        StreamOutput --> [*]
    }

    Resolver --> Classifier: multi-turn
    Resolver --> [*]: final response

    note right of Classifier
        GPT-4o-mini classifies
        intent from user message
    end note

    note right of KBRetrieval
        Vector search over
        knowledge base articles
    end note

    note right of Resolver
        GPT-4o generates response
        with retrieved context
    end note
```

---

## 4. Market Intelligence Agent Flow

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Market Intelligence Agent — Multi-Agent Flow               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Orchestrator Agent                            │    │
│  │                                                                      │    │
│  │  Input: "Analyze the AI chip market for Q1 2025"                    │    │
│  │  Output: Aggregated final report                                    │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                             │
│          ┌────────────────────┼────────────────────┐                        │
│          ▼                    ▼                    ▼                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │  Retrieval   │    │  Reasoning   │    │  Validation  │                 │
│  │  Agent       │    │  Agent       │    │  Agent       │                 │
│  │              │    │              │    │              │                 │
│  │  Tools:      │    │  Analysis:   │    │  Checks:     │                 │
│  │  • Web Search│    │  • Trends    │    │  • Fact check│                 │
│  │  • RSS Feeds │    │  • Patterns  │    │  • Cross-ref │                 │
│  │  • SEC API   │    │  • Insights  │    │  • Confidence│                 │
│  │  • Playwright│    │  • Data pts  │    │  • Gap flag  │                 │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                         Data Layer                                 │    │
│  │                                                                    │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │    │
│  │  │ Blob Store │  │ AI Search  │  │ Cosmos DB  │  │ Redis Cache│  │    │
│  │  │ Raw HTML,  │  │ Indexed    │  │ Reports &  │  │ Task Queue │  │    │
│  │  │ PDFs, CSV  │  │ Chunks     │  │ Metadata   │  │ & Results  │  │    │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Pipeline Execution:                                                         │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │ Phase 1 │──▶│ Phase 2 │──▶│ Phase 3 │──▶│ Phase 4 │──▶│ Phase 5 │      │
│  │ Retrieve│   │ Store   │   │ Analyze │   │ Validate│   │ Report  │      │
│  │ & Scrape│   │ & Index │   │ & Reason│   │ & Score │   │ & Deliver│     │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart TD
    A[User/Scheduled Topic] --> B[Orchestrator Agent]

    subgraph Phase1["Phase 1: Retrieval"]
        B --> C[Web Search Tool]
        B --> D[RSS Feed Tool]
        B --> E[SEC Filing Tool]
        B --> F[Playwright Scraper]
    end

    C --> G[Raw Data Collection]
    D --> G
    E --> G
    F --> G

    subgraph Phase2["Phase 2: Storage"]
        G --> H[Blob Storage\nRaw Documents]
        H --> I[Text Splitting\n& Chunking]
        I --> J[Azure AI Search\nIndexed Chunks]
    end

    subgraph Phase3["Phase 3: Reasoning"]
        J --> K[Reasoning Agent]
        K --> L[Trend Analysis]
        K --> M[Competitive Analysis]
        K --> N[Market Opportunities]
    end

    subgraph Phase4["Phase 4: Validation"]
        L --> O[Validation Agent]
        M --> O
        N --> O
        O --> P[Fact Checking]
        O --> Q[Confidence Scoring]
        O --> R[Gap Identification]
    end

    subgraph Phase5["Phase 5: Report"]
        P --> S[Report Generator]
        Q --> S
        R --> S
        S --> T[Final Intelligence Report]
    end

    T --> U[Cosmos DB\nPersistent Storage]
    T --> V[Client Delivery]

    style Phase1 fill:#e8f5e9
    style Phase2 fill:#e3f2fd
    style Phase3 fill:#fff3e0
    style Phase4 fill:#fce4ec
    style Phase5 fill:#f3e5f5
```

---

## 5. Multi-Agent Researcher Architecture

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Researcher — CrewAI Architecture              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        CrewAI Crew                                   │    │
│  │                        Process: Sequential                           │    │
│  │                                                                      │    │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │    │
│  │  │  RESEARCHER  │───▶│    CRITIC    │───▶│    WRITER    │           │    │
│  │  │    Agent     │    │    Agent     │    │    Agent     │           │    │
│  │  │              │    │              │    │              │           │    │
│  │  │ Role:        │    │ Role:        │    │ Role:        │           │    │
│  │  │ Senior       │    │ Quality      │    │ Technical    │           │    │
│  │  │ Research     │    │ Reviewer     │    │ Writer       │           │    │
│  │  │ Analyst      │    │              │    │              │           │    │
│  │  │              │    │              │    │              │           │    │
│  │  │ Tools:       │    │ Tools:       │    │ Tools:       │           │    │
│  │  │ • SerperDev  │    │ • None       │    │ • None       │           │    │
│  │  │ • ScrapeWeb  │    │   (Analysis  │    │   (Writing   │           │    │
│  │  │              │    │    only)     │    │    only)     │           │    │
│  │  │ Goal:        │    │              │    │              │           │    │
│  │  │ Gather &     │    │ Goal:        │    │ Goal:        │           │    │
│  │  │ organize     │    │ Review &     │    │ Produce      │           │    │
│  │  │ findings     │    │ validate     │    │ polished     │           │    │
│  │  │              │    │              │    │ report       │           │    │
│  │  └──────────────┘    └──────────────┘    └──────────────┘           │    │
│  │        │                    │                    │                   │    │
│  │        └────────────────────┼────────────────────┘                   │    │
│  │                             ▼                                         │    │
│  │              ┌──────────────────────────────┐                         │    │
│  │              │    Shared Memory (Cosmos DB) │                         │    │
│  │              │                              │                         │    │
│  │              │  • Research findings         │                         │    │
│  │              │  • Critique notes            │                         │    │
│  │              │  • Draft versions            │                         │    │
│  │              │  • Conversation history      │                         │    │
│  │              │  • Source citations          │                         │    │
│  │              └──────────────────────────────┘                         │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  External Sources:                                                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │ Serper API │  │ Arxiv API  │  │ News APIs  │  │ Custom Knowledge   │    │
│  │ (Web+News) │  │ (Papers)   │  │ (Reuters,  │  │ Base (Vector DB)   │    │
│  │            │  │            │  │  Bloomberg)│  │                    │    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart LR
    subgraph Crew["CrewAI Crew"]
        direction TB

        R[Researcher Agent]
        C[Critic Agent]
        W[Writer Agent]

        R -->|Research findings| C
        C -->|Validated analysis| W
        W -->|Final report| Output
    end

    subgraph Tools["External Tools"]
        S[SerperDev Tool]
        SW[ScrapeWebsite Tool]
        A[Arxiv API]
        N[News APIs]
    end

    subgraph Memory["Shared Memory - Cosmos DB"]
        M1[Research Findings]
        M2[Critique Notes]
        M3[Draft Versions]
        M4[Source Citations]
    end

    S --> R
    SW --> R
    A --> R
    N --> R

    R -.-> M1
    C -.-> M2
    W -.-> M3
    R -.-> M4

    W --> Output[Final Research Report]

    style R fill:#e8f5e9
    style C fill:#fff3e0
    style W fill:#f3e5f5
    style Memory fill:#e3f2fd
```

---

## 6. Azure Infrastructure Layout

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Azure Infrastructure — Bicep IaC Layout                    │
│                                                                              │
│  Resource Group: rg-ai-capstone-{env}                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Networking                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  VNet: vnet-ai-capstone                                      │    │    │
│  │  │  ├── Subnet: snet-apps (Container Apps environment)         │    │    │
│  │  │  ├── Subnet: snet-services (Azure services)                 │    │    │
│  │  │  └── Subnet: snet-private (Private endpoints)               │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        AI Services                                │    │
│  │                                                                  │    │
│  │  ┌─────────────────────────┐  ┌─────────────────────────────┐   │    │
│  │  │ Azure OpenAI            │  │ Azure AI Search             │   │    │
│  │  │                         │  │                             │   │    │
│  │  │ Deployments:            │  │ SKU: Standard               │   │    │
│  │  │ • gpt-4o (10 TPM)       │  │ Partitions: 1               │   │    │
│  │  │ • gpt-4o-mini (30 TPM)  │  │ Replicas: 1                 │   │    │
│  │  │ • text-embedding-3-sm   │  │ Semantic: Enabled           │   │    │
│  │  │                         │  │ Vector: HNSW                │   │    │
│  │  └─────────────────────────┘  └─────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        Data Services                              │    │
│  │                                                                  │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │    │
│  │  │ Cosmos DB    │ │ Blob Storage │ │ Redis Cache  │            │    │
│  │  │              │ │              │ │              │            │    │
│  │  │ Serverless   │ │ Standard LRS │ │ Basic C0     │            │    │
│  │  │ Session      │ │ Containers:  │ │ Non-SSL: Off │            │    │
│  │  │ Consistency  │ │ - raw-docs   │ │ TLS 1.2      │            │    │
│  │  │              │ │ - reports    │ │              │            │    │
│  │  │ Databases:   │ │ - embeddings │              │            │    │
│  │  │ - agent-mem  │ │ - backups    │              │            │    │
│  │  │ - user-data  │ │              │              │            │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        Compute                                    │    │
│  │                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │  Azure Container Apps Environment                        │    │    │
│  │  │                                                          │    │    │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────────┐  │    │    │
│  │  │  │ book-rec-api│ │ support-api │ │ research-api      │  │    │    │
│  │  │  │ Min: 1      │ │ Min: 1      │ │ Min: 1            │  │    │    │
│  │  │  │ Max: 10     │ │ Max: 10     │ │ Max: 5            │  │    │    │
│  │  │  │ CPU: 1      │ │ CPU: 1      │ │ CPU: 2            │  │    │    │
│  │  │  │ Mem: 2Gi    │ │ Mem: 2Gi    │ │ Mem: 4Gi          │  │    │    │
│  │  │  │ Scale: HTTP │ │ Scale: HTTP │ │ Scale: HTTP       │  │    │    │
│  │  │  └─────────────┘ └─────────────┘ └───────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        Security & Observability                   │    │
│  │                                                                  │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │    │
│  │  │ Key Vault    │ │ App Insights │ │ Log Analytics            │ │    │
│  │  │              │ │              │ │                          │ │    │
│  │  │ • OpenAI key │ │ • Traces     │ │ • Application logs       │ │    │
│  │  │ • Search key │ │ • Metrics    │ │ • Performance data       │ │    │
│  │  │ • Cosmos conn│ │ • Exceptions │ │ • Custom events          │ │    │
│  │  │ • Redis conn │ │ • Requests   │ │ • Security events        │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    subgraph Networking["Networking"]
        VNet[VNet: vnet-ai-capstone]
        Subnet1[Subnet: snet-apps]
        Subnet2[Subnet: snet-services]
        Subnet3[Subnet: snet-private]
        VNet --> Subnet1
        VNet --> Subnet2
        VNet --> Subnet3
    end

    subgraph AI["AI Services"]
        OpenAI[Azure OpenAI\nGPT-4o, GPT-4o-mini, Embeddings]
        Search[Azure AI Search\nStandard SKU, HNSW]
    end

    subgraph Data["Data Services"]
        Cosmos[Cosmos DB\nServerless, Session]
        Blob[Blob Storage\nStandard LRS]
        Redis[Redis Cache\nBasic C0]
    end

    subgraph Compute["Compute - Container Apps"]
        Env[Container Apps Environment]
        App1[book-rec-api\n1-10 replicas]
        App2[support-api\n1-10 replicas]
        App3[research-api\n1-5 replicas]
        Env --> App1
        Env --> App2
        Env --> App3
    end

    subgraph Security["Security & Observability"]
        KV[Key Vault\nSecrets Management]
        AppIns[Application Insights\nTraces & Metrics]
        Logs[Log Analytics\nCentralized Logging]
    end

    App1 --> OpenAI
    App1 --> Search
    App1 --> Cosmos
    App1 --> Redis

    App2 --> OpenAI
    App2 --> Search
    App2 --> Cosmos

    App3 --> OpenAI
    App3 --> Cosmos
    App3 --> Blob

    App1 -.-> AppIns
    App2 -.-> AppIns
    App3 -.-> AppIns

    AppIns --> Logs
    OpenAI -.-> KV
    Search -.-> KV
    Cosmos -.-> KV

    style AI fill:#e1f5fe
    style Data fill:#e8f5e9
    style Compute fill:#fff3e0
    style Security fill:#fce4ec
```

---

## 7. Production Deployment Flow

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Production Deployment Flow — CI/CD Pipeline               │
│                                                                              │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
│  │  Commit  │───▶│  Build   │───▶│   Test   │───▶│  Deploy  │───▶│ Monitor│ │
│  │  (Push)  │    │  & Scan  │    │  & Eval  │    │  (Canary)│    │ & Scale│ │
│  └─────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘ │
│                                                                              │
│  Stage 1: Commit                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Developer pushes to main branch                                    │    │
│  │  GitHub Actions workflow triggered                                  │    │
│  │  Paths filter: src/**, tests/**, Dockerfile, *.bicep               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Stage 2: Build & Scan                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  1. Checkout code                                                   │    │
│  │  2. Build Docker image                                              │    │
│  │  3. Push to Azure Container Registry                                │    │
│  │  4. Trivy vulnerability scan                                        │    │
│  │  5. Bicep template validation                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Stage 3: Test & Evaluate                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  1. Unit tests (pytest) - target: >80% coverage                     │    │
│  │  2. Integration tests (API endpoints, DB connections)               │    │
│  │  3. RAG evaluation (RAGAS metrics)                                  │    │
│  │  4. Load testing (Locust - concurrent users)                        │    │
│  │  5. Security scan (prompt injection, OWASP)                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Stage 4: Deploy (Canary)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  1. Deploy to staging environment                                   │    │
│  │  2. Run smoke tests                                                 │    │
│  │  3. Deploy canary revision (10% traffic)                            │    │
│  │  4. Monitor for 10 minutes:                                         │    │
│  │     - Error rate < 1%                                               │    │
│  │     - P99 latency < 2x baseline                                     │    │
│  │     - Token usage within budget                                     │    │
│  │  5. If healthy: Gradually increase to 25% → 50% → 100%             │    │
│  │  6. If unhealthy: Auto-rollback to previous revision                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Stage 5: Monitor & Scale                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  1. Azure Monitor dashboards                                        │    │
│  │  2. Application Insights traces                                     │    │
│  │  3. Custom LLM metrics (tokens, cost, hallucination rate)           │    │
│  │  4. Alert rules:                                                    │    │
│  │     - Error rate > 2% → Critical alert                              │    │
│  │     - P99 latency > 5s → Warning alert                              │    │
│  │     - Token budget > 80% → Warning alert                            │    │
│  │     - Hallucination rate > 5% → Critical alert                      │    │
│  │  5. Auto-scaling based on HTTP concurrent requests                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart LR
    subgraph Commit["Stage 1: Commit"]
        A[Developer Push\nto main]
    end

    subgraph Build["Stage 2: Build & Scan"]
        B[Docker Build]
        C[Push to ACR]
        D[Trivy Scan]
        E[Bicep Validate]
        B --> C --> D --> E
    end

    subgraph Test["Stage 3: Test & Evaluate"]
        F[Unit Tests\n>80% coverage]
        G[Integration Tests]
        H[RAG Evaluation\nRAGAS]
        I[Load Testing\nLocust]
        J[Security Scan]
        F --> G --> H --> I --> J
    end

    subgraph Deploy["Stage 4: Deploy Canary"]
        K[Deploy to Staging]
        L[Smoke Tests]
        M[Canary 10%\nMonitor 10min]
        N{Healthy?}
        O[Promote\n25% → 50% → 100%]
        P[Auto-Rollback]
        K --> L --> M --> N
        N -->|Yes| O
        N -->|No| P
    end

    subgraph Monitor["Stage 5: Monitor & Scale"]
        Q[Azure Monitor\nDashboards]
        R[App Insights\nTraces]
        S[Custom LLM\nMetrics]
        T[Alert Rules]
        U[Auto-Scaling]
        Q --> R --> S --> T --> U
    end

    A --> B
    E --> F
    J --> K
    O --> Q
    P -.->|Fix & Retry| B

    style Commit fill:#e8f5e9
    style Build fill:#e3f2fd
    style Test fill:#fff3e0
    style Deploy fill:#fce4ec
    style Monitor fill:#f3e5f5
```

---

## 8. Book Recommender — Embedding Index Structure

### ASCII — Azure AI Search Index Schema

```
┌─────────────────────────────────────────────────────────────────┐
│              Azure AI Search Index: books-index                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Field              Type              Attributes                │
│  ─────────────────  ────────────────  ────────────────────────  │
│  book_id            String (key)      Key, retrievable          │
│  title              String            Searchable, filterable    │
│  author             String            Searchable, filterable    │
│  description        String            Searchable                │
│  genre              String            Filterable, facetable     │
│  publication_year   Int32             Filterable, sortable      │
│  avg_rating         Double            Filterable, sortable      │
│  description_vector Float[3072]       Searchable (HNSW)         │
│  cover_url          String            Retrievable               │
│  isbn               String            Filterable                │
│                                                                 │
│  Vector Config:                                                 │
│  ─────────────                                                │
│  Algorithm: HNSW (m=16, ef_construction=400)                   │
│  Metric: Cosine Similarity                                     │
│  Profile: hnsw-profile                                         │
│                                                                 │
│  Semantic Config:                                               │
│  ──────────────                                               │
│  Configuration: book-config                                    │
│  Title Field: title                                            │
│  Content Fields: description                                   │
│  Keywords Fields: genre, author                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mermaid — Re-Ranking Flow

```mermaid
flowchart LR
    A[Query: sci-fi with\nstrong female leads] --> B[Embedding\n3072-dim vector]
    B --> C{Hybrid Search}
    
    C --> D[Vector Search\nTop 50]
    C --> E[BM25 Search\nTop 50]
    C --> F[Semantic Rank\nTop 50]
    
    D --> G[RRF Fusion\nCombined Score]
    E --> G
    F --> G
    
    G --> H[Cross-Encoder\nRe-Rank]
    H --> I[Apply User\nPreferences]
    I --> J[Diversity\nFilter]
    J --> K[Top 5\nResults]
    
    L[(User Profile\nCosmos DB)] -.-> I
    M[(Book Index\nAI Search)] -.-> C
```

---

## 9. Customer Support — WebSocket Message Flow

### ASCII — Real-Time Streaming Sequence

```
┌──────────────┐                    ┌──────────────┐                    ┌──────────────┐
│   React      │                    │   FastAPI    │                    │   LangGraph  │
│   Frontend   │                    │   WebSocket  │                    │   Engine     │
│              │                    │   Server     │                    │              │
└──────┬───────┘                    └──────┬───────┘                    └──────┬───────┘
       │                                   │                                   │
       │  ── CONNECT /ws/session-123 ──▶  │                                   │
       │  ◀─────── 101 Switching ──────── │                                   │
       │                                   │                                   │
       │  ── {"type":"user_message", ──▶  │                                   │
       │     "content":"My order is..."}   │                                   │
       │                                   │  ── astream_events(config) ──▶   │
       │                                   │                                   │
       │                                   │  ◀── on_chat_model_stream ────── │
       │                                   │      (token chunk)                │
       │  ◀── {"type":"chunk", ────────── │                                   │
       │     "content":"I understand"}     │                                   │
       │                                   │                                   │
       │                                   │  ◀── on_chat_model_stream ────── │
       │  ◀── {"type":"chunk", ────────── │                                   │
       │     "content":" your order..."}   │                                   │
       │                                   │                                   │
       │     ... (streaming continues) ... │                                   │
       │                                   │                                   │
       │                                   │  ◀── on_chain_end ────────────── │
       │                                   │      (final state)                │
       │  ◀── {"type":"complete", ─────── │                                   │
       │     "intent":"billing",           │                                   │
       │     "escalated":false}            │                                   │
       │                                   │                                   │
```

### Mermaid — Support Conversation State Transitions

```mermaid
stateDiagram-v2
    [*] --> ClassifyIntent
    
    ClassifyIntent --> RetrieveKnowledge: intent classified
    
    RetrieveKnowledge --> ResolveIssue: docs retrieved
    
    ResolveIssue --> GenerateResponse: resolvable == true
    ResolveIssue --> EscalateToHuman: resolvable == false
    
    GenerateResponse --> ValidateResponse: response generated
    
    ValidateResponse --> End: passes validation
    ValidateResponse --> GenerateResponse: fails && retry < 2
    ValidateResponse --> EscalateToHuman: fails && retry >= 2
    
    EscalateToHuman --> End: ticket created
    
    End --> [*]
    
    note right of ClassifyIntent
        LLM classifies:
        - Intent category
        - Urgency level
        - Confidence score
    end note
    
    note right of RetrieveKnowledge
        Azure AI Search:
        - Vector + keyword
        - Intent filter
        - Top 5 articles
    end note
    
    note right of ValidateResponse
        Quality checks:
        - Addresses issue?
        - Polite and safe?
        - Supported by KB?
    end note
```

---

## 10. Market Intelligence — Map-Reduce Summarization

### ASCII — Summarization Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Map-Reduce Summarization                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Source Document (50,000 tokens)                                    │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Text Splitter (RecursiveCharacter)              │   │
│  │  Chunk size: 4000 tokens, Overlap: 200 tokens               │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│           ┌─────────────────┼─────────────────┐                    │
│           ▼                 ▼                 ▼                    │
│     ┌───────────┐     ┌───────────┐     ┌───────────┐             │
│     │  Chunk 1  │     │  Chunk 2  │     │  Chunk N  │   (13 chunks)│
│     │  (4000 t) │     │  (4000 t) │     │  (2000 t) │             │
│     └─────┬─────┘     └─────┬─────┘     └─────┬─────┘             │
│           │                 │                 │                     │
│           ▼                 ▼                 ▼                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    MAP PHASE                                 │   │
│  │  LLM: "Write a detailed summary of the following..."        │   │
│  │                                                              │   │
│  │  Summary 1 ◀── Chunk 1    Summary 2 ◀── Chunk 2             │   │
│  │  ...                        ...                              │   │
│  │  Summary 13 ◀── Chunk 13                                    │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    REDUCE PHASE                              │   │
│  │  LLM: "Write a comprehensive summary combining these..."    │   │
│  │                                                              │   │
│  │  Input: Summary 1 + Summary 2 + ... + Summary 13            │   │
│  │  Output: Consolidated market intelligence summary            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid — Market Intelligence Sequence

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Scraper
    participant Retriever
    participant Reasoner
    participant Validator
    participant Storage

    User->>Orchestrator: Research query
    Orchestrator->>Orchestrator: Parse & decompose
    
    par Parallel Execution
        Orchestrator->>Scraper: Scrape URLs
        Scraper->>Scraper: Playwright crawl
        Scraper->>Storage: Store raw HTML (Blob)
        Scraper-->>Orchestrator: Cleaned content
        
    and
        Orchestrator->>Retriever: Search KB
        Retriever->>Retriever: Vector + keyword search
        Retriever-->>Orchestrator: Retrieved docs
    end
    
    Orchestrator->>Reasoner: Synthesize findings
    Reasoner->>Reasoner: Cross-reference sources
    Reasoner-->>Orchestrator: Draft analysis
    
    Orchestrator->>Validator: Validate report
    Validator->>Validator: Fact-check claims
    Validator->>Validator: Score confidence
    Validator-->>Orchestrator: Validated report
    
    Orchestrator->>Storage: Store report (Cosmos DB)
    Orchestrator-->>User: Final intelligence report
```

---

## 11. Multi-Agent Researcher — Shared Memory Architecture

### ASCII — Cosmos DB Memory Containers

```
┌─────────────────────────────────────────────────────────────────────┐
│              Cosmos DB Shared Memory — Multi-Agent                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Database: CrewMemory                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Container: artifacts (partition: /research_id)             │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  {                                                          │   │
│  │    "id": "research-001-researcher-2026-04-01T10:00:00",     │   │
│  │    "research_id": "research-001",                           │   │
│  │    "agent": "researcher",                                   │   │
│  │    "content": "<markdown findings...>",                     │   │
│  │    "metadata": { "source_count": 15, "confidence": 0.85 },  │   │
│  │    "created_at": "2026-04-01T10:00:00Z",                    │   │
│  │    "ttl": 604800  // 7 days                                 │   │
│  │  }                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Container: feedback (partition: /research_id)              │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  {                                                          │   │
│  │    "id": "fb-research-001-2026-04-01T10:05:00",             │   │
│  │    "research_id": "research-001",                           │   │
│  │    "from_agent": "critic",                                  │   │
│  │    "to_agent": "writer",                                    │   │
│  │    "feedback": "<review notes...>",                         │   │
│  │    "quality_score": 7.5,                                    │   │
│  │    "created_at": "2026-04-01T10:05:00Z"                     │   │
│  │  }                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Container: conversations (partition: /research_id)         │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  {                                                          │   │
│  │    "id": "conv-research-001-001",                           │   │
│  │    "research_id": "research-001",                           │   │
│  │    "agent": "researcher",                                   │   │
│  │    "message": "Searching for AI coding assistant trends...",│   │
│  │    "timestamp": "2026-04-01T10:00:01Z"                      │   │
│  │  }                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Change Feed: Real-time notifications when agents write to memory  │
│  Consistency: Session (read-your-writes within a research session) │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid — Agent Collaboration with Memory

```mermaid
graph TB
    subgraph CrewAI Process
        direction TB
        
        A[User Topic Input] --> B[Crew Orchestrator]
        
        B --> C[Researcher Agent]
        C -->|research_findings.md| D[Critic Agent]
        D -->|review_feedback.md| E[Writer Agent]
        
        C -.->|Tools| F[SerperDev Tool]
        C -.->|Tools| G[ScrapeWebsite Tool]
        D -.->|Tools| F
        E -.->|Tools| H[FileRead Tool]
    end
    
    subgraph Cosmos DB Memory
        I[(Artifacts Container)]
        J[(Feedback Container)]
        K[(Conversations Container)]
    end
    
    C -.->|Store findings| I
    D -.->|Store critique| J
    E -.->|Store report| I
    C -.->|Log actions| K
    D -.->|Log review| K
    E -.->|Log writing| K
    
    subgraph Output
        L[Final Report PDF]
        M[Research Dashboard]
    end
    
    E --> L
    E --> M
```

---

## 12. Azure Infrastructure — Bicep Template

### Mermaid — Infrastructure Dependencies

```mermaid
graph TB
    subgraph Networking
        VNET[Virtual Network 10.0.0.0/16]
        SUB1[Subnet: app]
        SUB2[Subnet: data]
        SUB3[Subnet: mgmt]
        VNET --> SUB1
        VNET --> SUB2
        VNET --> SUB3
    end

    subgraph Compute
        ACA[Azure Container Apps Env]
        APP1[Book Recommender API]
        APP2[Customer Support API]
        APP3[Market Intel API]
        APP4[Research Orchestrator]
        ACA --> APP1
        ACA --> APP2
        ACA --> APP3
        ACA --> APP4
    end

    subgraph AI Services
        AOAI[Azure OpenAI]
        AIS[Azure AI Search]
        GPT4O[gpt-4o deployment]
        GPT4OMINI[gpt-4o-mini deployment]
        EMBED[text-embedding-3-large]
        AOAI --> GPT4O
        AOAI --> GPT4OMINI
        AOAI --> EMBED
    end

    subgraph Data
        COSMOS[Cosmos DB]
        BLOB[Blob Storage]
        KV[Key Vault]
        REDIS[Redis Cache]
    end

    subgraph Observability
        APPINS[Application Insights]
        LOGANALYTICS[Log Analytics]
    end

    APP1 --> AOAI
    APP1 --> AIS
    APP1 --> COSMOS
    APP1 --> BLOB
    APP1 --> REDIS

    APP2 --> AOAI
    APP2 --> AIS
    APP2 --> COSMOS

    APP3 --> AOAI
    APP3 --> BLOB
    APP3 --> COSMOS

    APP4 --> AOAI
    APP4 --> COSMOS

    APP1 -.->|secrets| KV
    APP2 -.->|secrets| KV
    APP3 -.->|secrets| KV
    APP4 -.->|secrets| KV

    APP1 -.->|telemetry| APPINS
    APP2 -.->|telemetry| APPINS
    APP3 -.->|telemetry| APPINS
    APP4 -.->|telemetry| APPINS

    APPINS --> LOGANALYTICS
```

---

## 13. Production Deployment — Canary Timeline

### ASCII — Canary Deployment Timeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Canary Deployment Timeline                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Time    Traffic Distribution          Action                       │
│  ──────  ────────────────────────────  ───────────────────────────  │
│  T+0     Production: 100%              Deploy new revision          │
│          Canary: 0%                    (no traffic yet)             │
│                                                                     │
│  T+1min  Production: 90%               Route 10% to canary          │
│          Canary: 10%                   Run smoke tests              │
│                                                                     │
│  T+5min  Production: 90%               Monitor metrics:             │
│          Canary: 10%                   - Error rate                 │
│                                        - p99 latency                │
│                                        - LLM quality scores         │
│                                        - Token usage rate           │
│                                                                     │
│  T+15min Production: 70%               If metrics OK:               │
│          Canary: 30%                   Increase canary to 30%       │
│                                                                     │
│  T+30min Production: 50%               Continue monitoring:         │
│          Canary: 50%                   - Compare canary vs prod     │
│                                        - Check for regressions      │
│                                                                     │
│  T+45min Production: 0%               If all metrics pass:         │
│          Canary: 100%                  Promote canary to 100%       │
│                                                                     │
│  T+46min New Production: 100%         Tag revision as stable       │
│          Old revision: retired         Clean up old revision        │
│                                                                     │
│  ─── ROLLBACK PATH ──────────────────────────────────────────────  │
│                                                                     │
│  Any     Canary: X%                  If error rate > 1% or         │
│  time    Production: (100-X)%        p99 > 5s or quality drop:     │
│                                        Immediately shift 100%      │
│                                        back to production          │
│                                        Alert on-call engineer       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid — Monitoring & Feedback Loop

```mermaid
flowchart LR
    A[Production System] --> B[OpenTelemetry SDK]
    B --> C[Application Insights]
    C --> D{Alert Rules}
    
    D -->|Latency > 5s| E[PagerDuty]
    D -->|Error rate > 2%| E
    D -->|Hallucination > 5%| F[Quality Team]
    D -->|Cost anomaly| G[FinOps Team]
    
    C --> H[Grafana Dashboards]
    H --> I[Daily Review]
    
    I --> J{Improvement Needed?}
    J -->|Yes| K[Create Ticket]
    J -->|No| L[Continue Monitoring]
    
    K --> M[Feature Branch]
    M --> N[CI/CD Pipeline]
    N --> A
    
    C --> O[LangSmith Evals]
    O --> P[Weekly Quality Report]
    P --> I
    
    style D fill:#fff3cd
    style E fill:#f8d7da
    style J fill:#d4edda
```

---

## Quick Reference — All Diagrams

| # | Diagram | Section | Type |
|---|---------|---------|------|
| 1 | Capstone Projects Ecosystem | 1 | ASCII + Mermaid |
| 2 | Book Recommender Pipeline | 2 | ASCII + Mermaid |
| 3 | Embedding Index Structure | 8 | ASCII |
| 4 | Re-Ranking Flow | 8 | Mermaid |
| 5 | Customer Support State Machine | 3 | ASCII + Mermaid |
| 6 | WebSocket Message Flow | 9 | ASCII |
| 7 | Support State Transitions | 9 | Mermaid |
| 8 | Market Intelligence Pipeline | 4 | ASCII + Mermaid |
| 9 | Map-Reduce Summarization | 10 | ASCII |
| 10 | Market Intelligence Sequence | 10 | Mermaid |
| 11 | Multi-Agent Researcher | 5 | ASCII + Mermaid |
| 12 | Shared Memory Architecture | 11 | ASCII |
| 13 | Agent Collaboration with Memory | 11 | Mermaid |
| 14 | Azure Infrastructure Layout | 6 | ASCII + Mermaid |
| 15 | Infrastructure Dependencies | 12 | Mermaid |
| 16 | CI/CD Pipeline | 7 | ASCII + Mermaid |
| 17 | Canary Deployment Timeline | 13 | ASCII |
| 18 | Monitoring Feedback Loop | 13 | Mermaid |

---

## 8. Book Recommender — Embedding Index Structure

### ASCII — Azure AI Search Index Schema

```
┌─────────────────────────────────────────────────────────────────┐
│              Azure AI Search Index: books-index                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Field              Type              Attributes                │
│  ─────────────────  ────────────────  ────────────────────────  │
│  book_id            String (key)      Key, retrievable          │
│  title              String            Searchable, filterable    │
│  author             String            Searchable, filterable    │
│  description        String            Searchable                │
│  genre              String            Filterable, facetable     │
│  publication_year   Int32             Filterable, sortable      │
│  avg_rating         Double            Filterable, sortable      │
│  description_vector Float[3072]       Searchable (HNSW)         │
│  cover_url          String            Retrievable               │
│  isbn               String            Filterable                │
│                                                                 │
│  Vector Config:                                                 │
│  ─────────────                                                │
│  Algorithm: HNSW (m=16, ef_construction=400)                   │
│  Metric: Cosine Similarity                                     │
│  Profile: hnsw-profile                                         │
│                                                                 │
│  Semantic Config:                                               │
│  ──────────────                                               │
│  Configuration: book-config                                    │
│  Title Field: title                                            │
│  Content Fields: description                                   │
│  Keywords Fields: genre, author                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mermaid — Re-Ranking Flow

```mermaid
flowchart LR
    A[Query: sci-fi with\nstrong female leads] --> B[Embedding\n3072-dim vector]
    B --> C{Hybrid Search}
    
    C --> D[Vector Search\nTop 50]
    C --> E[BM25 Search\nTop 50]
    C --> F[Semantic Rank\nTop 50]
    
    D --> G[RRF Fusion\nCombined Score]
    E --> G
    F --> G
    
    G --> H[Cross-Encoder\nRe-Rank]
    H --> I[Apply User\nPreferences]
    I --> J[Diversity\nFilter]
    J --> K[Top 5\nResults]
    
    L[(User Profile\nCosmos DB)] -.-> I
    M[(Book Index\nAI Search)] -.-> C
```

---

## 9. Customer Support — WebSocket Message Flow

### ASCII — Real-Time Streaming Sequence

```
┌──────────────┐                    ┌──────────────┐                    ┌──────────────┐
│   React      │                    │   FastAPI    │                    │   LangGraph  │
│   Frontend   │                    │   WebSocket  │                    │   Engine     │
│              │                    │   Server     │                    │              │
└──────┬───────┘                    └──────┬───────┘                    └──────┬───────┘
       │                                   │                                   │
       │  ── CONNECT /ws/session-123 ──▶  │                                   │
       │  ◀─────── 101 Switching ──────── │                                   │
       │                                   │                                   │
       │  ── {"type":"user_message", ──▶  │                                   │
       │     "content":"My order is..."}   │                                   │
       │                                   │  ── astream_events(config) ──▶   │
       │                                   │                                   │
       │                                   │  ◀── on_chat_model_stream ────── │
       │                                   │      (token chunk)                │
       │  ◀── {"type":"chunk", ────────── │                                   │
       │     "content":"I understand"}     │                                   │
       │                                   │                                   │
       │                                   │  ◀── on_chat_model_stream ────── │
       │  ◀── {"type":"chunk", ────────── │                                   │
       │     "content":" your order..."}   │                                   │
       │                                   │                                   │
       │     ... (streaming continues) ... │                                   │
       │                                   │                                   │
       │                                   │  ◀── on_chain_end ────────────── │
       │                                   │      (final state)                │
       │  ◀── {"type":"complete", ─────── │                                   │
       │     "intent":"billing",           │                                   │
       │     "escalated":false}            │                                   │
       │                                   │                                   │
```

### Mermaid — Support Conversation State Transitions

```mermaid
stateDiagram-v2
    [*] --> ClassifyIntent
    
    ClassifyIntent --> RetrieveKnowledge: intent classified
    
    RetrieveKnowledge --> ResolveIssue: docs retrieved
    
    ResolveIssue --> GenerateResponse: resolvable == true
    ResolveIssue --> EscalateToHuman: resolvable == false
    
    GenerateResponse --> ValidateResponse: response generated
    
    ValidateResponse --> End: passes validation
    ValidateResponse --> GenerateResponse: fails && retry < 2
    ValidateResponse --> EscalateToHuman: fails && retry >= 2
    
    EscalateToHuman --> End: ticket created
    
    End --> [*]
    
    note right of ClassifyIntent
        LLM classifies:
        - Intent category
        - Urgency level
        - Confidence score
    end note
    
    note right of RetrieveKnowledge
        Azure AI Search:
        - Vector + keyword
        - Intent filter
        - Top 5 articles
    end note
    
    note right of ValidateResponse
        Quality checks:
        - Addresses issue?
        - Polite and safe?
        - Supported by KB?
    end note
```

---

## 10. Market Intelligence — Map-Reduce Summarization

### ASCII — Summarization Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Map-Reduce Summarization                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Source Document (50,000 tokens)                                    │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Text Splitter (RecursiveCharacter)              │   │
│  │  Chunk size: 4000 tokens, Overlap: 200 tokens               │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│           ┌─────────────────┼─────────────────┐                    │
│           ▼                 ▼                 ▼                    │
│     ┌───────────┐     ┌───────────┐     ┌───────────┐             │
│     │  Chunk 1  │     │  Chunk 2  │     │  Chunk N  │   (13 chunks)│
│     │  (4000 t) │     │  (4000 t) │     │  (2000 t) │             │
│     └─────┬─────┘     └─────┬─────┘     └─────┬─────┘             │
│           │                 │                 │                     │
│           ▼                 ▼                 ▼                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    MAP PHASE                                 │   │
│  │  LLM: "Write a detailed summary of the following..."        │   │
│  │                                                              │   │
│  │  Summary 1 ◀── Chunk 1    Summary 2 ◀── Chunk 2             │   │
│  │  ...                        ...                              │   │
│  │  Summary 13 ◀── Chunk 13                                    │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    REDUCE PHASE                              │   │
│  │  LLM: "Write a comprehensive summary combining these..."    │   │
│  │                                                              │   │
│  │  Input: Summary 1 + Summary 2 + ... + Summary 13            │   │
│  │  Output: Consolidated market intelligence summary            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid — Market Intelligence Sequence

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Scraper
    participant Retriever
    participant Reasoner
    participant Validator
    participant Storage

    User->>Orchestrator: Research query
    Orchestrator->>Orchestrator: Parse & decompose
    
    par Parallel Execution
        Orchestrator->>Scraper: Scrape URLs
        Scraper->>Scraper: Playwright crawl
        Scraper->>Storage: Store raw HTML (Blob)
        Scraper-->>Orchestrator: Cleaned content
        
    and
        Orchestrator->>Retriever: Search KB
        Retriever->>Retriever: Vector + keyword search
        Retriever-->>Orchestrator: Retrieved docs
    end
    
    Orchestrator->>Reasoner: Synthesize findings
    Reasoner->>Reasoner: Cross-reference sources
    Reasoner-->>Orchestrator: Draft analysis
    
    Orchestrator->>Validator: Validate report
    Validator->>Validator: Fact-check claims
    Validator->>Validator: Score confidence
    Validator-->>Orchestrator: Validated report
    
    Orchestrator->>Storage: Store report (Cosmos DB)
    Orchestrator-->>User: Final intelligence report
```

---

## 11. Multi-Agent Researcher — Shared Memory Architecture

### ASCII — Cosmos DB Memory Containers

```
┌─────────────────────────────────────────────────────────────────────┐
│              Cosmos DB Shared Memory — Multi-Agent                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Database: CrewMemory                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Container: artifacts (partition: /research_id)             │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  {                                                          │   │
│  │    "id": "research-001-researcher-2026-04-01T10:00:00",     │   │
│  │    "research_id": "research-001",                           │   │
│  │    "agent": "researcher",                                   │   │
│  │    "content": "<markdown findings...>",                     │   │
│  │    "metadata": { "source_count": 15, "confidence": 0.85 },  │   │
│  │    "created_at": "2026-04-01T10:00:00Z",                    │   │
│  │    "ttl": 604800  // 7 days                                 │   │
│  │  }                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Container: feedback (partition: /research_id)              │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  {                                                          │   │
│  │    "id": "fb-research-001-2026-04-01T10:05:00",             │   │
│  │    "research_id": "research-001",                           │   │
│  │    "from_agent": "critic",                                  │   │
│  │    "to_agent": "writer",                                    │   │
│  │    "feedback": "<review notes...>",                         │   │
│  │    "quality_score": 7.5,                                    │   │
│  │    "created_at": "2026-04-01T10:05:00Z"                     │   │
│  │  }                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Container: conversations (partition: /research_id)         │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  {                                                          │   │
│  │    "id": "conv-research-001-001",                           │   │
│  │    "research_id": "research-001",                           │   │
│  │    "agent": "researcher",                                   │   │
│  │    "message": "Searching for AI coding assistant trends...",│   │
│  │    "timestamp": "2026-04-01T10:00:01Z"                      │   │
│  │  }                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Change Feed: Real-time notifications when agents write to memory  │
│  Consistency: Session (read-your-writes within a research session) │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid — Agent Collaboration with Memory

```mermaid
graph TB
    subgraph CrewAI Process
        direction TB
        
        A[User Topic Input] --> B[Crew Orchestrator]
        
        B --> C[Researcher Agent]
        C -->|research_findings.md| D[Critic Agent]
        D -->|review_feedback.md| E[Writer Agent]
        
        C -.->|Tools| F[SerperDev Tool]
        C -.->|Tools| G[ScrapeWebsite Tool]
        D -.->|Tools| F
        E -.->|Tools| H[FileRead Tool]
    end
    
    subgraph Cosmos DB Memory
        I[(Artifacts Container)]
        J[(Feedback Container)]
        K[(Conversations Container)]
    end
    
    C -.->|Store findings| I
    D -.->|Store critique| J
    E -.->|Store report| I
    C -.->|Log actions| K
    D -.->|Log review| K
    E -.->|Log writing| K
    
    subgraph Output
        L[Final Report PDF]
        M[Research Dashboard]
    end
    
    E --> L
    E --> M
```

---

## 12. Azure Infrastructure — Bicep Template

### Mermaid — Infrastructure Dependencies

```mermaid
graph TB
    subgraph Networking
        VNET[Virtual Network 10.0.0.0/16]
        SUB1[Subnet: app]
        SUB2[Subnet: data]
        SUB3[Subnet: mgmt]
        VNET --> SUB1
        VNET --> SUB2
        VNET --> SUB3
    end

    subgraph Compute
        ACA[Azure Container Apps Env]
        APP1[Book Recommender API]
        APP2[Customer Support API]
        APP3[Market Intel API]
        APP4[Research Orchestrator]
        ACA --> APP1
        ACA --> APP2
        ACA --> APP3
        ACA --> APP4
    end

    subgraph AI Services
        AOAI[Azure OpenAI]
        AIS[Azure AI Search]
        GPT4O[gpt-4o deployment]
        GPT4OMINI[gpt-4o-mini deployment]
        EMBED[text-embedding-3-large]
        AOAI --> GPT4O
        AOAI --> GPT4OMINI
        AOAI --> EMBED
    end

    subgraph Data
        COSMOS[Cosmos DB]
        BLOB[Blob Storage]
        KV[Key Vault]
        REDIS[Redis Cache]
    end

    subgraph Observability
        APPINS[Application Insights]
        LOGANALYTICS[Log Analytics]
    end

    APP1 --> AOAI
    APP1 --> AIS
    APP1 --> COSMOS
    APP1 --> BLOB
    APP1 --> REDIS

    APP2 --> AOAI
    APP2 --> AIS
    APP2 --> COSMOS

    APP3 --> AOAI
    APP3 --> BLOB
    APP3 --> COSMOS

    APP4 --> AOAI
    APP4 --> COSMOS

    APP1 -.->|secrets| KV
    APP2 -.->|secrets| KV
    APP3 -.->|secrets| KV
    APP4 -.->|secrets| KV

    APP1 -.->|telemetry| APPINS
    APP2 -.->|telemetry| APPINS
    APP3 -.->|telemetry| APPINS
    APP4 -.->|telemetry| APPINS

    APPINS --> LOGANALYTICS
```

---

## 13. Production Deployment — Canary Timeline

### ASCII — Canary Deployment Timeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Canary Deployment Timeline                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Time    Traffic Distribution          Action                       │
│  ──────  ────────────────────────────  ───────────────────────────  │
│  T+0     Production: 100%              Deploy new revision          │
│          Canary: 0%                    (no traffic yet)             │
│                                                                     │
│  T+1min  Production: 90%               Route 10% to canary          │
│          Canary: 10%                   Run smoke tests              │
│                                                                     │
│  T+5min  Production: 90%               Monitor metrics:             │
│          Canary: 10%                   - Error rate                 │
│                                        - p99 latency                │
│                                        - LLM quality scores         │
│                                        - Token usage rate           │
│                                                                     │
│  T+15min Production: 70%               If metrics OK:               │
│          Canary: 30%                   Increase canary to 30%       │
│                                                                     │
│  T+30min Production: 50%               Continue monitoring:         │
│          Canary: 50%                   - Compare canary vs prod     │
│                                        - Check for regressions      │
│                                                                     │
│  T+45min Production: 0%               If all metrics pass:         │
│          Canary: 100%                  Promote canary to 100%       │
│                                                                     │
│  T+46min New Production: 100%         Tag revision as stable       │
│          Old revision: retired         Clean up old revision        │
│                                                                     │
│  ─── ROLLBACK PATH ──────────────────────────────────────────────  │
│                                                                     │
│  Any     Canary: X%                  If error rate > 1% or         │
│  time    Production: (100-X)%        p99 > 5s or quality drop:     │
│                                        Immediately shift 100%      │
│                                        back to production          │
│                                        Alert on-call engineer       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid — Monitoring & Feedback Loop

```mermaid
flowchart LR
    A[Production System] --> B[OpenTelemetry SDK]
    B --> C[Application Insights]
    C --> D{Alert Rules}
    
    D -->|Latency > 5s| E[PagerDuty]
    D -->|Error rate > 2%| E
    D -->|Hallucination > 5%| F[Quality Team]
    D -->|Cost anomaly| G[FinOps Team]
    
    C --> H[Grafana Dashboards]
    H --> I[Daily Review]
    
    I --> J{Improvement Needed?}
    J -->|Yes| K[Create Ticket]
    J -->|No| L[Continue Monitoring]
    
    K --> M[Feature Branch]
    M --> N[CI/CD Pipeline]
    N --> A
    
    C --> O[LangSmith Evals]
    O --> P[Weekly Quality Report]
    P --> I
    
    style D fill:#fff3cd
    style E fill:#f8d7da
    style J fill:#d4edda
```

---

## Quick Reference — All Diagrams

| # | Diagram | Section | Type |
|---|---------|---------|------|
| 1 | Capstone Projects Ecosystem | 1 | ASCII + Mermaid |
| 2 | Book Recommender Pipeline | 2 | ASCII + Mermaid |
| 3 | Embedding Index Structure | 8 | ASCII |
| 4 | Re-Ranking Flow | 8 | Mermaid |
| 5 | Customer Support State Machine | 3 | ASCII + Mermaid |
| 6 | WebSocket Message Flow | 9 | ASCII |
| 7 | Support State Transitions | 9 | Mermaid |
| 8 | Market Intelligence Pipeline | 4 | ASCII + Mermaid |
| 9 | Map-Reduce Summarization | 10 | ASCII |
| 10 | Market Intelligence Sequence | 10 | Mermaid |
| 11 | Multi-Agent Researcher | 5 | ASCII + Mermaid |
| 12 | Shared Memory Architecture | 11 | ASCII |
| 13 | Agent Collaboration with Memory | 11 | Mermaid |
| 14 | Azure Infrastructure Layout | 6 | ASCII + Mermaid |
| 15 | Infrastructure Dependencies | 12 | Mermaid |
| 16 | CI/CD Pipeline | 7 | ASCII + Mermaid |
| 17 | Canary Deployment Timeline | 13 | ASCII |
| 18 | Monitoring Feedback Loop | 13 | Mermaid |

---

*End of Module 14 Diagrams*
