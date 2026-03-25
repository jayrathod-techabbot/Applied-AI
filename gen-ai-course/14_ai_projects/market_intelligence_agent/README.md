# Market Intelligence Agent

## Overview

A multi-agent intelligence platform that autonomously monitors market signals, analyzes competitor activity, and synthesizes strategic insights. Specialized agents coordinate retrieval, reasoning, and validation workflows to produce executive-ready narratives with confidence scoring.

---

## Architecture Diagram

```
                        ┌─────────────────────────────────────────┐
                        │         Azure Container Apps             │
                        │                                          │
  User / Scheduler ────▶│  ┌──────────────────────────────────┐   │
                        │  │       Orchestrator Agent          │   │
                        │  │   (LangChain AgentExecutor)       │   │
                        │  └──────┬──────────┬─────────────────┘   │
                        │         │          │                      │
                        │  ┌──────▼──┐  ┌───▼──────┐              │
                        │  │Retrieval│  │Reasoning │              │
                        │  │ Agent   │  │  Agent   │              │
                        │  └──────┬──┘  └───┬──────┘              │
                        │         │          │                      │
                        │  ┌──────▼──────────▼──────┐             │
                        │  │    Validation Agent     │             │
                        │  │  (Confidence Scoring)   │             │
                        │  └─────────────────────────┘             │
                        └─────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
             ┌──────▼──────┐   ┌────────▼───────┐  ┌──────▼──────┐
             │  Azure AI   │   │  Azure AI      │  │  Azure Blob │
             │  Search     │   │  (GPT-4o)      │  │  Storage    │
             │ (Vector DB) │   │                │  │  (Reports)  │
             └─────────────┘   └────────────────┘  └─────────────┘
```

### Agent Roles

| Agent | Responsibility |
|---|---|
| **Orchestrator** | Receives query, plans workflow, delegates to sub-agents |
| **Retrieval Agent** | Fetches market data from Azure AI Search (vector + keyword hybrid) |
| **Reasoning Agent** | Synthesizes retrieved chunks into structured analysis using GPT-4o |
| **Validation Agent** | Cross-checks claims against source chunks, assigns confidence score |

### Data Flow
1. Query enters Orchestrator
2. Retrieval Agent fetches top-k relevant document chunks from Azure AI Search
3. Reasoning Agent generates analysis grounded in retrieved context
4. Validation Agent compares claims to source embeddings, scores confidence
5. Final narrative + confidence report saved to Azure Blob Storage

---

## Project Structure

```
market_intelligence_agent/
├── .env.example                  # Environment variable template
├── pyproject.toml                # UV project config + dependencies
├── README.md                     # This file
├── INTERVIEW.md                  # Interview Q&A for this project
│
├── infra/                        # Azure infrastructure (Bicep)
│   ├── main.bicep
│   ├── container_app.bicep
│   ├── ai_search.bicep
│   └── storage.bicep
│
├── src/
│   └── market_intel/
│       ├── __init__.py
│       ├── main.py               # Entry point / FastAPI app
│       ├── config.py             # Settings (pydantic-settings)
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── orchestrator.py   # Master agent
│       │   ├── retrieval.py      # Azure AI Search retrieval
│       │   ├── reasoning.py      # GPT-4o reasoning chain
│       │   └── validation.py     # Confidence scoring
│       │
│       ├── pipelines/
│       │   ├── __init__.py
│       │   └── rag_pipeline.py   # RAG chain (LangChain)
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search_tool.py    # Azure AI Search tool wrapper
│       │   └── storage_tool.py   # Blob storage read/write
│       │
│       └── utils/
│           ├── __init__.py
│           ├── embeddings.py     # Azure OpenAI embeddings
│           └── logger.py
│
└── tests/
    ├── test_retrieval.py
    ├── test_reasoning.py
    └── test_validation.py
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- [UV](https://docs.astral.sh/uv/) installed
- Azure CLI installed and logged in (`az login`)
- Azure subscription with: OpenAI, AI Search, Container Apps, Blob Storage enabled

### 1. Clone & Set Up Environment

```bash
git clone <repo-url>
cd market_intelligence_agent

# Create virtual environment and install deps with UV
uv venv
uv sync
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Fill in your Azure credentials in .env
```

### 3. Deploy Azure Infrastructure

```bash
cd infra
az group create --name rg-market-intel --location eastus
az deployment group create \
  --resource-group rg-market-intel \
  --template-file main.bicep
```

### 4. Run Locally

```bash
uv run uvicorn src.market_intel.main:app --reload --port 8000
```

### 5. Deploy to Azure Container Apps

```bash
az acr build --registry <your-acr> --image market-intel:latest .
az containerapp update \
  --name market-intel-app \
  --resource-group rg-market-intel \
  --image <your-acr>.azurecr.io/market-intel:latest
```

---

## Environment Variables

```env
# .env.example

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_KEY=<your-key>
AZURE_SEARCH_INDEX=market-intel-index

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=<your-connection-string>
AZURE_STORAGE_CONTAINER=reports

# App
APP_ENV=development
LOG_LEVEL=INFO
CONFIDENCE_THRESHOLD=0.75
```
