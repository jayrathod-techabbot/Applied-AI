# Multi-Agent Researcher

## Overview

An agentic AI platform where specialized agents coordinate research collection, fact verification, and structured synthesis across multiple data sources to autonomously produce accurate, structured insights with minimal human oversight.

---

## Architecture Diagram

```
                        ┌──────────────────────────────────────────┐
                        │            Azure Container Apps           │
                        │                                           │
  User Query ──────────▶│   ┌──────────────────────────────────┐   │
                        │   │           CrewAI Crew             │   │
                        │   │   (role-based agent delegation)   │   │
                        │   └────┬──────────┬──────────┬────────┘   │
                        │        │          │          │             │
                        │  ┌─────▼───┐ ┌───▼───┐ ┌───▼──────┐     │
                        │  │Research │ │Critic │ │ Writer   │     │
                        │  │ Agent   │ │ Agent │ │  Agent   │     │
                        │  └─────┬───┘ └───┬───┘ └───┬──────┘     │
                        │        │          │          │             │
                        │   ┌────▼──────────▼──────────▼──────┐    │
                        │   │        Shared Crew Memory         │    │
                        │   └───────────────────────────────────┘   │
                        └──────────────────────────────────────────┘
                                         │
                         ┌───────────────┼──────────────┐
                         │               │              │
                  ┌──────▼──────┐ ┌──────▼──────┐ ┌────▼──────────┐
                  │  Azure AI   │ │  Azure AI   │ │  Azure Cosmos │
                  │  (GPT-4o)   │ │  Search     │ │  DB (memory)  │
                  └─────────────┘ └─────────────┘ └───────────────┘
```

### Agent Roles

| Agent | Role | Tools |
|---|---|---|
| **Researcher** | Gathers raw information from search and documents | Azure AI Search, Web search |
| **Critic** | Verifies facts, flags contradictions, requests re-search if needed | LLM cross-check, Source comparison |
| **Writer** | Synthesizes verified data into structured markdown report | GPT-4o, Formatting tools |

### Delegation Flow
```
Query → Researcher collects raw data
      → Critic verifies and scores each claim
      → If claim fails: Researcher re-queries with refined terms
      → Writer synthesizes verified claims into final report
      → Report saved to Cosmos DB with source provenance
```

---

## Project Structure

```
multi_agent_researcher/
├── .env.example
├── pyproject.toml
├── README.md
├── INTERVIEW.md
│
├── infra/
│   ├── main.bicep
│   ├── container_app.bicep
│   ├── cosmos_db.bicep
│   └── ai_search.bicep
│
├── src/
│   └── researcher/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       │
│       ├── crew/
│       │   ├── __init__.py
│       │   ├── agents.py         # CrewAI agent definitions
│       │   ├── tasks.py          # Task definitions per agent
│       │   └── crew.py           # Crew assembly + kickoff
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search_tool.py    # Azure AI Search wrapper
│       │   └── memory_tool.py    # Cosmos DB read/write
│       │
│       └── utils/
│           ├── __init__.py
│           └── logger.py
│
└── tests/
    ├── test_crew.py
    └── test_tools.py
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+, UV, Azure CLI, Azure subscription

### 1. Environment Setup

```bash
git clone <repo-url>
cd multi_agent_researcher
uv venv
uv sync
cp .env.example .env
```

### 2. Deploy Azure Infrastructure

```bash
cd infra
az group create --name rg-researcher --location eastus
az deployment group create \
  --resource-group rg-researcher \
  --template-file main.bicep
```

### 3. Run Locally

```bash
uv run uvicorn src.researcher.main:app --reload --port 8001
```

### 4. Deploy to Azure Container Apps

```bash
az acr build --registry <your-acr> --image multi-researcher:latest .
az containerapp update \
  --name researcher-app \
  --resource-group rg-researcher \
  --image <your-acr>.azurecr.io/multi-researcher:latest
```

---

## Core Code: Crew Assembly

```python
# src/researcher/crew/crew.py
from crewai import Crew, Process
from researcher.crew.agents import build_researcher, build_critic, build_writer
from researcher.crew.tasks import research_task, critic_task, write_task

def build_research_crew(query: str) -> Crew:
    researcher = build_researcher()
    critic = build_critic()
    writer = build_writer()

    return Crew(
        agents=[researcher, critic, writer],
        tasks=[
            research_task(researcher, query),
            critic_task(critic),
            write_task(writer),
        ],
        process=Process.sequential,   # Researcher → Critic → Writer
        memory=True,                  # Shared crew memory via Cosmos DB
        verbose=True,
    )

async def run_research(query: str) -> dict:
    crew = build_research_crew(query)
    result = crew.kickoff()
    return {"query": query, "report": result}
```

---

## Environment Variables

```env
# .env.example
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

AZURE_SEARCH_ENDPOINT=https://<search>.search.windows.net
AZURE_SEARCH_KEY=<key>
AZURE_SEARCH_INDEX=research-index

AZURE_COSMOS_ENDPOINT=https://<cosmos>.documents.azure.com:443/
AZURE_COSMOS_KEY=<key>
AZURE_COSMOS_DB=researcher_db
AZURE_COSMOS_CONTAINER=memory

APP_ENV=development
LOG_LEVEL=INFO
```
