# Multi-Agent Customer Support System

An AI-powered customer support automation system that routes incoming tickets to specialist agents using intent classification, retrieves relevant answers from domain-specific knowledge bases, and escalates low-confidence cases to human agents.

---

## Architecture

```
                         ┌─────────────────────────────────────┐
                         │         SUPPORT GATEWAY              │
                         │    FastAPI (port 8000)               │
                         │    Streamlit UI (port 8501)          │
                         └──────────────┬──────────────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────────────┐
                         │        ORCHESTRATOR (HUB)            │
                         │                                      │
                         │  ┌─────────┐    ┌─────────────────┐ │
                         │  │ intake  │───►│intent_classifier│ │
                         │  └─────────┘    └────────┬────────┘ │
                         │                          │           │
                         │                    ┌─────▼──────┐   │
                         │                    │   router   │   │
                         │                    └─────┬──────┘   │
                         └──────────────────────────┼──────────┘
                                                    │
                     ┌──────────────┬───────────────┼──────────────┐
                     ▼              ▼                ▼              ▼
          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  ┌───────────┐
          │  BILLING     │ │  TECHNICAL   │ │   GENERAL    │  │ ESCALATE  │
          │   AGENT      │ │    AGENT     │ │    AGENT     │  │  DIRECT   │
          │ (spoke 1)    │ │  (spoke 2)   │ │  (spoke 3)   │  │           │
          │              │ │              │ │              │  │           │
          │ billing_kb   │ │  tech_kb     │ │ general_kb   │  │           │
          │ (TF-IDF)     │ │  (TF-IDF)    │ │ (TF-IDF)     │  │           │
          └──────┬───────┘ └──────┬───────┘ └──────┬───────┘  └─────┬─────┘
                 │                │                 │                │
                 └────────────────┴────────────────-┘                │
                                  │                                   │
                                  ▼                                   │
                     ┌────────────────────────┐                       │
                     │   confidence_check     │                       │
                     └───────────┬────────────┘                       │
                                 │                                    │
               ┌─────────────────┤                                    │
               │                 │                                    │
    conf < 0.6 ▼                 ▼ conf >= 0.6                        │
  ┌────────────────────┐  ┌──────────────┐                            │
  │ escalation_handler │◄─┘              │                            │
  │  (HITL interrupt)  │  │  responder   │                            │
  └────────┬───────────┘  └──────┬───────┘                           │
           │                     │                                    │
           │ (human reviews)     ▼                                    ▼
           │              ┌─────────────────────────────────────────────┐
           └─────────────►│                  END                         │
                          └─────────────────────────────────────────────┘
                               hitl_resume (after human input)
```

**Architecture Pattern**: Hub-and-Spoke
- **Hub**: Orchestrator (intent_classifier + router)
- **Spokes**: BillingAgent, TechAgent, GeneralAgent
- **Benefit**: Add new specialists by adding one node and one edge — no existing agents change.

---

## Features

- **Intent classification**: Groq llama-3.3-70b classifies tickets as billing / technical / general / escalate
- **Specialist agents**: Each agent has its own knowledge base and system prompt
- **TF-IDF knowledge base**: Offline-capable retrieval (FAISS upgrade path documented)
- **Confidence scoring**: Derived from KB retrieval scores (auditable, deterministic)
- **HITL escalation**: Low-confidence tickets pause for human review
- **Session memory**: Multi-turn conversation history with rolling context window
- **FastAPI**: RESTful API with CORS, Pydantic validation, OpenAPI docs
- **Streamlit UI**: Interactive chat with intent badges and KB source display
- **Thread-based state**: LangGraph MemorySaver enables pause/resume per ticket

---

## Quick Start

### 1. Clone and install dependencies

```bash
cd 04_agentic_systems/projects/02_customer_support_system
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 3. Run the standalone demo

```bash
python core_logic.py
```

### 4. Start the FastAPI server

```bash
uvicorn api.routes:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 5. Start the Streamlit chat UI

```bash
streamlit run ui/app.py
```

UI available at: http://localhost:8501

### 6. Run tests

```bash
pytest tests/ -v
```

---

## Environment Variables

| Variable               | Required | Default                        | Description                                               |
|------------------------|----------|--------------------------------|-----------------------------------------------------------|
| `GROQ_API_KEY`         | Yes      | —                              | Groq API key (starts with `gsk_`)                         |
| `GROQ_MODEL`           | No       | `llama-3.3-70b-versatile`      | Groq model ID                                             |
| `LLM_PROVIDER`         | No       | `groq`                         | LLM provider (currently only groq supported)              |
| `KB_DIR`               | No       | `./data/knowledge_base`        | Directory containing KB markdown files                    |
| `CONFIDENCE_THRESHOLD` | No       | `0.6`                          | Min confidence score before HITL escalation (0.0–1.0)    |
| `MAX_HISTORY_MESSAGES` | No       | `20`                           | Max messages to include in session context                |

---

## API Reference

### POST /ticket
Submit a new support ticket.

**Request:**
```json
{
  "message": "I need a refund for my last invoice",
  "session_id": "SES-OPTIONAL",
  "user_id": "user_123",
  "channel": "api"
}
```

**Response:**
```json
{
  "ticket_id": "TKT-A1B2C3D4",
  "session_id": "SES-12345678",
  "response": "Refunds are available within 30 days...",
  "intent": "billing",
  "agent": "BillingAgent",
  "confidence_score": 0.742,
  "escalated": false,
  "resolved": true,
  "priority": "medium",
  "kb_sources": ["billing_kb.md"]
}
```

---

### POST /chat/{session_id}
Continue a multi-turn conversation.

**Request:**
```json
{ "message": "And how do I upgrade to the Professional plan?" }
```

**Response:**
```json
{
  "ticket_id": "TKT-E5F6G7H8",
  "session_id": "SES-12345678",
  "response": "To upgrade, go to Settings > Billing > Plan...",
  "agent": "BillingAgent",
  "confidence_score": 0.681,
  "escalated": false,
  "intent": "billing"
}
```

---

### POST /escalation/resolve/{ticket_id}
Human agent resolves an escalated ticket.

**Request:**
```json
{
  "notes": "Verified the customer was charged twice. Approved full refund of $99.",
  "resolution": "resolved"
}
```

**Response:**
```json
{
  "ticket_id": "TKT-A1B2C3D4",
  "response": "Our team has reviewed your case...",
  "resolved": true,
  "human_notes": "Verified..."
}
```

---

### GET /ticket/{ticket_id}
Get full ticket details.

---

### GET /session/{session_id}/history
Get conversation history for a session.

---

### GET /health
Health check with KB status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "kb_status": {
    "billing": {"ready": true, "chunks": 42},
    "technical": {"ready": true, "chunks": 58},
    "general": {"ready": true, "chunks": 35}
  },
  "active_sessions": 3
}
```

---

## Sample Ticket Walkthrough

**User submits**: "I was charged twice this month and need a refund."

1. **intake**: Assigns `ticket_id=TKT-A1B2C3D4`, records timestamp, adds message to session memory.
2. **intent_classifier**: Groq classifies → `{"intent": "billing", "priority": "medium"}`.
3. **router**: Maps billing → BillingAgent.
4. **billing_agent**:
   - Calls `lookup_billing_kb("charged twice refund")`.
   - TF-IDF retrieves 2 chunks: "Refund Policy" and "Common Billing Issues - double charge".
   - Computes confidence: `(0.32 * 0.6 + 0.21 * 0.3) * 2.5 = 0.636`.
   - Calls Groq to generate a KB-grounded response.
5. **confidence_check**: `0.636 > 0.6` → route to responder.
6. **responder**: Marks ticket resolved, appends ticket reference footer.
7. **Result returned**: `confidence=0.636, escalated=false, resolved=true`.

**If confidence had been 0.05** (no KB match):
5. **confidence_check**: `0.05 < 0.6` → route to escalation_handler.
6. **escalation_handler**: Creates escalation record, sets `escalated=true`.
7. **Human agent**: Reviews via `POST /escalation/resolve/TKT-A1B2C3D4`.
8. **hitl_resume**: Incorporates human notes, generates final response.

---

## Project Structure

```
02_customer_support_system/
├── agent/
│   ├── state.py          # TicketState, SessionContext, KBResult TypedDicts
│   ├── memory.py         # KnowledgeBaseMemory (TF-IDF), SessionMemory
│   ├── tools.py          # @tool functions for KB lookup, ticketing, escalation
│   ├── nodes.py          # LangGraph node implementations
│   └── graph.py          # StateGraph construction and helper functions
├── api/
│   └── routes.py         # FastAPI endpoints
├── ui/
│   └── app.py            # Streamlit chat interface
├── data/
│   └── knowledge_base/
│       ├── billing_kb.md     # Pricing, refunds, invoices, payments
│       ├── technical_kb.md   # API docs, errors, integrations
│       └── general_kb.md     # Company info, SLA, privacy, contacts
├── tests/
│   ├── test_routing.py   # Intent classification and routing tests
│   └── test_memory.py    # KB search and session memory tests
├── core_logic.py         # Standalone demo script
├── interview_questions.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# API: http://localhost:8000
# Streamlit: http://localhost:8501
```

---

## Running Tests

```bash
# All tests (no API key needed — LLM calls are mocked)
pytest tests/ -v

# Individual test files
pytest tests/test_memory.py -v       # KB and session memory tests (fully offline)
pytest tests/test_routing.py -v      # Routing logic tests (LLM mocked)

# With coverage
pytest tests/ --cov=agent --cov-report=term-missing
```

---

## Design Patterns Used

| Pattern | Implementation |
|---------|---------------|
| Hub-and-Spoke | Orchestrator routes to 3 specialist agents |
| Reactive Agent | intent_classifier: observe → classify → act |
| Vector Memory | TF-IDF KnowledgeBaseMemory (FAISS-upgradeable) |
| Buffer Memory | SessionMemory: rolling window per session |
| HITL Escalation | LangGraph interrupt_before + resume_after |
| Hierarchical Orchestration | LangGraph StateGraph with conditional edges |
| Thread-based State | MemorySaver checkpoint per ticket_id |
