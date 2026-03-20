# AI Data Analysis Pipeline

An agentic data analysis system that autonomously profiles CSV datasets, plans and executes statistical analyses, generates visualisations, critiques its own work, and produces written insights reports. Supports multi-turn follow-up questions via session memory.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MAIN ANALYSIS GRAPH                         │
│                                                                 │
│   CSV Upload                                                    │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────┐                                                │
│  │ data_profiler│  → shape, dtypes, nulls, sample rows          │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │   planner   │  → LLM generates 5-7 analysis steps            │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐◄───────────────────────┐                      │
│  │   analyzer  │  → calls pandas tools  │ (if score < 7        │
│  └──────┬──────┘    per plan step       │  AND iter < max)     │
│         │                               │                       │
│         ▼                               │                       │
│  ┌─────────────┐                        │                       │
│  │ chart_maker │  → histogram, bar,     │                       │
│  └──────┬──────┘    scatter, heatmap,   │                       │
│         │           line charts         │                       │
│         ▼                               │                       │
│  ┌─────────────┐                        │                       │
│  │  reflector  │  → DataCritic scores   │                       │
│  │ (DataCritic)│    analysis 0-10       │                       │
│  └──────┬──────┘                        │                       │
│         │ approved=False ───────────────┘                       │
│         │ approved=True                                         │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │report_writer│  → full markdown report                        │
│  └──────┬──────┘                                                │
│         │                                                       │
│        END                                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FOLLOW-UP Q&A GRAPH                          │
│                                                                 │
│  User Question                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────┐                                           │
│  │ question_router  │  → pass-through (routing via edge)        │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │context_retriever │  → keyword-scored retrieval from          │
│  └────────┬─────────┘    DatasetContextMemory                   │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │    answerer      │  → grounded answer using context          │
│  └────────┬─────────┘                                           │
│           │                                                     │
│          END                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     TOOL LAYER                                  │
│                                                                 │
│  pandas_executor    - sandboxed pandas code execution           │
│  chart_generator    - matplotlib PNG generation                 │
│  stats_calculator   - descriptive stats + correlations          │
│  outlier_detector   - IQR-based anomaly detection               │
│  pattern_finder     - correlations, trends, top categories      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     MEMORY LAYER                                │
│                                                                 │
│  ConversationMemory    - rolling message window (50 messages)   │
│  DatasetContextMemory  - analysis artefacts per session         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.com/download) (for local LLM, recommended)
- Docker + Docker Compose (optional, for containerised deployment)

### 1. Clone / navigate to the project

```bash
cd "D:/Jay Rathod/Tutorials/Applied AI/gen-ai-course/04_agentic_systems/projects/03_data_analysis_pipeline"
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull the Ollama model

```bash
ollama pull llama3.2
```

### 5. Configure environment variables

```bash
cp .env.example .env
# Edit .env as needed
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama` or `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `OPENAI_API_KEY` | *(required if openai)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `OUTPUT_DIR` | `./output` | Directory for charts and reports |
| `MAX_REFLECTION_ITERATIONS` | `2` | Max reflector→analyser loops |
| `REFLECTION_QUALITY_THRESHOLD` | `7.0` | Min score to approve analysis |
| `API_BASE_URL` | `http://localhost:8000` | Streamlit → API base URL |

---

## How to Run

### Option A: Standalone demo (no server needed)

```bash
python core_logic.py
```

This creates a synthetic sales dataset, runs the full pipeline, saves charts to `./output/`, and demonstrates follow-up Q&A — all in a single script.

### Option B: API server

```bash
uvicorn api.routes:app --host 0.0.0.0 --port 8000 --reload
```

Visit http://localhost:8000/docs for interactive Swagger UI.

### Option C: Streamlit UI (requires API server running)

In a second terminal:

```bash
streamlit run ui/app.py
```

Visit http://localhost:8501

### Option D: Docker Compose (all services)

```bash
docker-compose up --build
```

- API: http://localhost:8000
- Streamlit: http://localhost:8501

### Run tests

```bash
# All tests
pytest tests/ -v

# Tools tests only
pytest tests/test_tools.py -v

# Graph tests only
pytest tests/test_graph.py -v

# With coverage
pytest tests/ --cov=agent --cov-report=term-missing
```

---

## API Reference

### POST /analyze

Upload a CSV and start analysis.

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@sales_data.csv" \
  -F "question=Which product has the highest revenue?"
```

Response:
```json
{
  "session_id": "3f4a7b2c-...",
  "status": "queued",
  "message": "Analysis started. Poll GET /report/3f4a7b2c-... for results."
}
```

---

### GET /report/{session_id}

Poll for analysis status and retrieve the report.

```bash
curl http://localhost:8000/report/3f4a7b2c-...
```

Response when complete:
```json
{
  "session_id": "3f4a7b2c-...",
  "status": "complete",
  "report": "# Data Analysis Report\n\n## Executive Summary\n...",
  "analysis_plan": ["Step 1: ...", "Step 2: ..."],
  "reflection": {"quality_score": 8.5, "approved": true, ...},
  "dataset_summary": {"shape": [200, 7], "columns": [...], ...}
}
```

---

### POST /followup/{session_id}

Ask a follow-up question about a completed analysis.

```bash
curl -X POST http://localhost:8000/followup/3f4a7b2c-... \
  -H "Content-Type: application/json" \
  -d '{"question": "Which region had the most outliers in revenue?"}'
```

Response:
```json
{
  "session_id": "3f4a7b2c-...",
  "question": "Which region had the most outliers in revenue?",
  "answer": "Based on the analysis, the North region had the highest number of revenue outliers..."
}
```

---

### GET /charts/{session_id}

Get chart file paths for a session.

```bash
curl http://localhost:8000/charts/3f4a7b2c-...
```

Response:
```json
{
  "session_id": "3f4a7b2c-...",
  "charts": [
    "./output/3f4a7b2c-.../Revenue_Distribution.png",
    "./output/3f4a7b2c-.../Correlation_Heatmap.png"
  ]
}
```

---

### GET /health

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok", "version": "1.0.0", "sessions_active": 3}
```

---

## LLM Provider Switching

### Switch to Ollama (default, local, free)

```bash
# In .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Make sure Ollama is running:
```bash
ollama serve  # or start the Ollama desktop app
```

### Switch to OpenAI

```bash
# In .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

### Switch at runtime (Streamlit UI)

Use the **LLM Provider** dropdown in the sidebar of the Streamlit UI. This sets the `LLM_PROVIDER` environment variable for the current process. Note: if the API server is already running, you need to restart it to pick up the new provider.

---

## Project Structure

```
03_data_analysis_pipeline/
├── agent/
│   ├── __init__.py
│   ├── state.py          # AnalysisState TypedDict + dataclasses
│   ├── tools.py          # LangChain @tool functions
│   ├── memory.py         # ConversationMemory + DatasetContextMemory
│   ├── nodes.py          # LangGraph node implementations
│   └── graph.py          # StateGraph definitions + LLMProvider
├── api/
│   ├── __init__.py
│   └── routes.py         # FastAPI routes
├── ui/
│   ├── __init__.py
│   └── app.py            # Streamlit application
├── tests/
│   ├── __init__.py
│   ├── test_tools.py     # Tool unit tests
│   └── test_graph.py     # Node + graph integration tests
├── output/               # Charts + reports (gitignored)
├── core_logic.py         # Standalone demo script
├── interview_questions.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Patterns Demonstrated

| Pattern | Implementation |
|---|---|
| Planning Agent | `planner` node generates step list via LLM |
| ReAct Loop | `analyzer` reasons → calls tools → observes |
| Reflection / Self-Critique | `reflector` (DataCritic) scores and loops |
| Tool Use | `@tool` decorated pandas/matplotlib functions |
| Short-Term Memory | `ConversationMemory` rolling message window |
| Context Memory | `DatasetContextMemory` keyword retrieval |
| Conditional Graph Edges | `_should_reanlyze()` routing function |
| Multi-Turn Q&A | Follow-up graph with context injection |
| Code Sandboxing | Restricted `exec()` with whitelisted builtins |
