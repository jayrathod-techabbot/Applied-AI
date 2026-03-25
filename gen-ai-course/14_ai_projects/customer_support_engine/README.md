# Agentic Customer Support Resolution Engine

## Overview

A stateful multi-agent system using LangGraph to classify customer issues, retrieve relevant knowledge, reason through resolution paths, and generate personalized responses. The system adapts dynamically based on conversation state and feedback loops, with human escalation as a fallback.

---

## Architecture Diagram

```
Customer Message
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph State Machine                      │
│                                                                  │
│   ┌──────────┐    ┌───────────────┐    ┌────────────────────┐  │
│   │Classifier│───▶│   Knowledge   │───▶│ Resolution Reasoner│  │
│   │  Node    │    │ Retrieval Node│    │      Node          │  │
│   └──────────┘    └───────────────┘    └──────────┬─────────┘  │
│        │                                           │            │
│   [Issue Type]                           [Resolved / Escalate] │
│        │                                           │            │
│   ┌────▼──────┐                         ┌──────────▼─────────┐ │
│   │  Routing  │                         │  Response Generator│ │
│   │   Node    │                         │       Node         │ │
│   └────┬──────┘                         └──────────┬─────────┘ │
│        │                                           │            │
│   [billing/                              ┌─────────▼──────────┐│
│    technical/                            │  Feedback Evaluator││
│    general]                              │       Node         ││
│                                          └─────────┬──────────┘│
│                                                     │           │
│                                        [Helpful / Not Helpful]  │
│                                                     │           │
│                                          ┌──────────▼──────────┐│
│                                          │ Re-route or Complete ││
│                                          └─────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
         │
   ┌─────┴──────────┐
   │  Azure Services │
   │                 │
   │ - Azure AI      │
   │   (GPT-4o)      │
   │ - Azure AI      │
   │   Search (KB)   │
   │ - Azure         │
   │   CosmosDB      │
   │   (conv state)  │
   └─────────────────┘
```

### Graph Node Descriptions

| Node | Input | Output | Condition |
|---|---|---|---|
| **Classifier** | Raw message | Issue type + severity | Always runs first |
| **Router** | Issue type | Next node path | Branches on issue type |
| **Knowledge Retrieval** | Issue type + query | Relevant KB chunks | Runs before reasoning |
| **Resolution Reasoner** | KB chunks + history | Resolution steps | Core reasoning |
| **Response Generator** | Resolution steps | Customer-facing message | Final synthesis |
| **Feedback Evaluator** | Customer reply | Helpful / Not helpful | Conditional loop |
| **Escalation** | Full state | Ticket for human agent | Triggered if unresolved |

---

## Project Structure

```
customer_support_engine/
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
│   └── support/
│       ├── __init__.py
│       ├── main.py               # FastAPI app + WebSocket for streaming
│       ├── config.py
│       │
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── state.py          # LangGraph TypedDict state schema
│       │   ├── nodes.py          # All graph node functions
│       │   ├── edges.py          # Conditional edge logic
│       │   └── builder.py        # Graph assembly + compilation
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── kb_search.py      # Azure AI Search KB retrieval
│       │   └── ticket_tool.py    # Escalation ticket creation
│       │
│       ├── memory/
│       │   ├── __init__.py
│       │   └── cosmos_checkpointer.py  # LangGraph checkpointer (Cosmos)
│       │
│       └── utils/
│           ├── __init__.py
│           └── logger.py
│
└── tests/
    ├── test_graph.py
    ├── test_nodes.py
    └── test_edges.py
```

---

## Core Code: LangGraph State + Graph

```python
# src/support/graph/state.py
from typing import Annotated, TypedDict, Literal
from langgraph.graph.message import add_messages

class SupportState(TypedDict):
    messages: Annotated[list, add_messages]
    issue_type: str                          # billing | technical | general
    severity: Literal["low", "medium", "high"]
    kb_chunks: list[str]                     # Retrieved knowledge base chunks
    resolution_steps: list[str]              # Reasoned resolution path
    resolution_status: Literal["resolved", "escalated", "pending"]
    feedback_signal: Literal["helpful", "not_helpful", "no_feedback"]
    retry_count: int                         # Prevents infinite feedback loops
    conversation_id: str
```

```python
# src/support/graph/builder.py
from langgraph.graph import StateGraph, END
from support.graph.state import SupportState
from support.graph.nodes import (
    classify_issue, route_issue, retrieve_knowledge,
    reason_resolution, generate_response,
    evaluate_feedback, escalate_to_human
)
from support.graph.edges import should_escalate, should_retry

def build_support_graph():
    builder = StateGraph(SupportState)

    # Add nodes
    builder.add_node("classifier", classify_issue)
    builder.add_node("retrieval", retrieve_knowledge)
    builder.add_node("reasoner", reason_resolution)
    builder.add_node("responder", generate_response)
    builder.add_node("feedback_eval", evaluate_feedback)
    builder.add_node("escalation", escalate_to_human)

    # Entry point
    builder.set_entry_point("classifier")

    # Edges
    builder.add_edge("classifier", "retrieval")
    builder.add_edge("retrieval", "reasoner")
    builder.add_edge("reasoner", "responder")
    builder.add_edge("responder", "feedback_eval")

    # Conditional: retry, escalate, or finish
    builder.add_conditional_edges(
        "feedback_eval",
        should_retry,
        {
            "retry": "retrieval",        # Re-retrieve with refined query
            "escalate": "escalation",    # Hand off to human
            "done": END,
        }
    )
    builder.add_edge("escalation", END)

    return builder.compile()
```

---

## Setup Instructions

### 1. Environment Setup

```bash
git clone <repo-url>
cd customer_support_engine
uv venv
uv sync
cp .env.example .env
```

### 2. Deploy Azure Infrastructure

```bash
cd infra
az group create --name rg-support-engine --location eastus
az deployment group create \
  --resource-group rg-support-engine \
  --template-file main.bicep
```

### 3. Run Locally

```bash
uv run uvicorn src.support.main:app --reload --port 8003
```

### 4. Test the Graph

```bash
uv run pytest tests/ -v
```

### 5. Deploy to Azure Container Apps

```bash
az acr build --registry <your-acr> --image support-engine:latest .
az containerapp update \
  --name support-engine-app \
  --resource-group rg-support-engine \
  --image <your-acr>.azurecr.io/support-engine:latest
```

---

## Observability Setup

Each graph node emits structured logs with:
- `conversation_id` — for end-to-end trace correlation
- `node_name` — which step in the graph
- `latency_ms` — per-node execution time
- `token_usage` — input + output tokens
- `state_snapshot` — key state fields at that node

Logs ship to Azure Monitor via Application Insights SDK. You can query full conversation traces in Log Analytics.

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
AZURE_SEARCH_INDEX=support-kb-index

AZURE_COSMOS_ENDPOINT=https://<cosmos>.documents.azure.com:443/
AZURE_COSMOS_KEY=<key>
AZURE_COSMOS_DB=support_db
AZURE_COSMOS_CONTAINER=conversations

APPINSIGHTS_CONNECTION_STRING=<connection-string>

APP_ENV=development
LOG_LEVEL=INFO
MAX_RETRY_COUNT=2
ESCALATION_SEVERITY_THRESHOLD=high
```
