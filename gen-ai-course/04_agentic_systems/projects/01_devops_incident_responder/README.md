# AI DevOps Incident Responder

An agentic system that monitors system logs, detects anomalies, proposes remediation steps, and executes fixes with human-in-the-loop approval.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AI DevOps Incident Responder                          │
│                                                                           │
│  Raw Logs ──► DETECTOR ──► SEVERITY ROUTER                              │
│                                │                                          │
│                    ┌───────────┴────────────┐                           │
│                    │ LOW                    │ MEDIUM/HIGH/CRITICAL       │
│                    ▼                        ▼                            │
│             AUTO RESPONDER           PLANNER (GPT-4o)                   │
│                    │                        │                            │
│                    │                  DIAGNOSER (ReAct ×3)              │
│                    │                        │                            │
│                    │                 RUNBOOK SEARCHER                   │
│                    │                  (TF-IDF / FAISS)                  │
│                    │                        │                            │
│                    │                 FIX PROPOSER (GPT-4o)              │
│                    │                        │                            │
│                    │              ┌──────────────────┐                  │
│                    │              │  HITL CHECKPOINT │ ◄── Human        │
│                    │              │  interrupt_before│     Approves     │
│                    │              └──────────────────┘                  │
│                    │                        │                            │
│                    │                   EXECUTOR                         │
│                    │              (dry_run=True default)                │
│                    │                        │                            │
│                    └──────────┬─────────────┘                           │
│                               ▼                                          │
│                        OUTCOME LOGGER                                   │
│                     (saves to history)                                  │
│                               │                                          │
│                              END                                         │
└─────────────────────────────────────────────────────────────────────────┘

Components:
  FastAPI (port 8000) ──► LangGraph Agent ──► OpenAI GPT-4o
  Streamlit UI (port 8501) ──► FastAPI
  RunbookMemory (TF-IDF) ──► data/runbooks/*.md
  IncidentHistoryMemory ──► data/incident_history/*.json
  LangGraph MemorySaver ──► in-process checkpointer (HITL state)
```

## Agentic Patterns Used

| Pattern | Implementation |
|---|---|
| Reactive Agent | `detector` node — rule-based anomaly detection |
| ReAct Loop | `diagnoser` node — Observe → Think → Act × 3 |
| Planning Agent | `planner` node — GPT-4o generates investigation plan |
| HITL | `interrupt_before=["executor"]` — pause for human approval |
| Long-term Memory | `RunbookMemory` (TF-IDF) + `IncidentHistoryMemory` (JSON) |
| RAG | `fix_proposer` uses runbook excerpts as grounding context |
| Tool Integration | `parse_logs`, `fetch_metrics`, `execute_fix`, `search_runbook` |

## Project Structure

```
01_devops_incident_responder/
├── agent/
│   ├── state.py          # IncidentState TypedDict + helper dataclasses
│   ├── tools.py          # LangChain @tool functions
│   ├── memory.py         # RunbookMemory + IncidentHistoryMemory
│   ├── nodes.py          # All LangGraph node functions
│   └── graph.py          # StateGraph definition + run/approve helpers
├── api/
│   └── routes.py         # FastAPI endpoints
├── ui/
│   └── app.py            # Streamlit dashboard
├── data/
│   ├── runbooks/         # Markdown runbook files
│   ├── sample_logs/      # Sample incident log files
│   └── incident_history/ # Persisted resolved incidents (auto-created)
├── tests/
│   ├── test_tools.py     # Tool unit tests
│   └── test_graph.py     # Graph integration tests
├── core_logic.py         # Standalone demo script
├── interview_questions.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Setup Instructions

### 1. Prerequisites

- Python 3.12+
- OpenAI API key with GPT-4o access

### 2. Create Virtual Environment

```bash
cd 01_devops_incident_responder
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 5. Run the Standalone Demo

```bash
python core_logic.py
```

This runs all nodes sequentially without a server, auto-approving at the HITL step.

### 6. Run the API Server

```bash
uvicorn api.routes:app --reload --port 8000
# API docs available at: http://localhost:8000/docs
```

### 7. Run the Streamlit UI

```bash
streamlit run ui/app.py
# Opens at: http://localhost:8501
```

### 8. Run Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `LLM_PROVIDER` | `openai` | LLM provider (currently only openai) |
| `RUNBOOK_DIR` | `./data/runbooks` | Path to markdown runbook files |
| `INCIDENT_HISTORY_DIR` | `./data/incident_history` | Path for saved incident JSON files |
| `MAX_REACT_ITERATIONS` | `3` | Maximum ReAct loop iterations in diagnoser |
| `DRY_RUN` | `true` | If true, execute_fix logs but doesn't run commands |
| `API_BASE_URL` | `http://localhost:8000` | Streamlit → FastAPI URL |

## API Reference

### Start an Incident

```bash
curl -X POST http://localhost:8000/incident \
  -H "Content-Type: application/json" \
  -d '{
    "raw_logs": "2024-01-15 14:23:01 ERROR app-server-01 CPU usage: 94.5% (threshold: 90%)\n2024-01-15 14:23:05 CRITICAL app-server-01 Memory pressure detected: 87% used"
  }'
```

Response:
```json
{
  "incident_id": "3f7a9b2c-...",
  "thread_id": "3f7a9b2c-...",
  "status": "queued",
  "message": "Incident 3f7a9b2c... queued for analysis."
}
```

### Check Status

```bash
curl http://localhost:8000/status/3f7a9b2c-...
```

Response:
```json
{
  "incident_id": "3f7a9b2c-...",
  "status": "awaiting_approval",
  "severity": "critical",
  "detected_anomalies": [...],
  "investigation_plan": [...],
  "diagnosis": "Root cause: ...",
  "proposed_fixes": [...]
}
```

### Approve Fixes

```bash
curl -X POST http://localhost:8000/approve/3f7a9b2c-... \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "notes": "Verified — safe to proceed during low-traffic window"}'
```

Response:
```json
{
  "incident_id": "3f7a9b2c-...",
  "status": "resolved",
  "executed_fixes": ["Step 1: systemctl restart app-service → DRY-RUN OK"],
  "outcome": "Incident resolved. Severity: critical..."
}
```

### Reject Fixes

```bash
curl -X POST http://localhost:8000/approve/3f7a9b2c-... \
  -H "Content-Type: application/json" \
  -d '{"approved": false, "notes": "Cannot restart during peak traffic — schedule for 2am"}'
```

### Get Audit Log

```bash
curl http://localhost:8000/audit/3f7a9b2c-...
```

### List All Incidents

```bash
curl http://localhost:8000/incidents
curl "http://localhost:8000/incidents?limit=5&status_filter=awaiting_approval"
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Sample Incident Walkthrough

### Scenario: High CPU Incident

1. **Submit logs** from `data/sample_logs/high_cpu_incident.log`

2. **Detector** identifies:
   - `cpu_high`: CPU at 94.5% (threshold 90%) — CRITICAL
   - `memory_high`: Memory at 87% (threshold 85%) — CRITICAL
   - `error_spike`: HTTP 5xx count > 20 — CRITICAL

3. **Planner** generates:
   - "Identify top CPU-consuming processes with top -b -n 1"
   - "Check for runaway processes causing thread pool exhaustion"
   - "Review application logs for exception patterns"
   - "Verify auto-scaling HPA configuration and current state"

4. **Diagnoser** (3 ReAct iterations):
   - Iteration 1: Observes CPU metrics from `fetch_metrics("app-server-01")`
   - Iteration 2: Notes memory correlation and GC pause patterns
   - Iteration 3: Concludes "Java process PID 18423 in retry loop consuming 68% CPU"

5. **Runbook searcher** finds `cpu_high_runbook.md` (score 0.4231) as top match

6. **Fix proposer** proposes:
   - Step 1: `systemctl restart app-service` [MEDIUM RISK]
   - Step 2: `kubectl scale deployment app-server --replicas=3` [LOW RISK]

7. **HITL checkpoint**: Graph pauses, operator reviews proposed fixes

8. **Approval**: Operator approves via UI or API

9. **Executor**: Runs both fixes (DRY RUN unless DRY_RUN=false)

10. **Outcome logger**: Saves resolution to `data/incident_history/{incident_id}.json`

## Docker Setup

### Build and Run

```bash
docker-compose up --build
```

Services:
- FastAPI: http://localhost:8000 (docs at /docs)
- Streamlit: http://localhost:8501

### Run Individual Service

```bash
# API only
docker build -t devops-incident-responder .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8000:8000 devops-incident-responder

# Streamlit only
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8501:8501 devops-incident-responder \
  streamlit run ui/app.py
```

## Key Design Decisions

1. **DRY_RUN=true by default**: No production system should auto-execute shell commands. Operators must explicitly set `DRY_RUN=false` to enable real execution.

2. **Command whitelist in execute_fix**: Prevents prompt injection attacks from causing arbitrary command execution. All new permitted commands require explicit code changes.

3. **Rule-based detection, LLM-powered reasoning**: Anomaly detection uses deterministic rules (cheap, fast, auditable). Root-cause reasoning and fix proposal use GPT-4o (powerful, context-aware).

4. **ReAct iteration cap**: Every LLM loop must have a hard numeric cap. `MAX_REACT_ITERATIONS=3` prevents infinite loops while providing sufficient evidence gathering.

5. **HITL for medium/high/critical severity only**: Low-severity incidents use auto-responder to avoid alert fatigue. The threshold can be lowered by changing `severity_router` logic.

6. **incident_id == thread_id**: Using the same UUID for both avoids the N+1 lookup problem when resuming after HITL.
