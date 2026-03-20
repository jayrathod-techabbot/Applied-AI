"""
app.py - Streamlit user interface for the AI Data Analysis Pipeline.

Design decisions:
- st.session_state stores the session_id and all API responses so that
  Streamlit reruns (triggered by any widget interaction) don't lose data.
- Polling for analysis completion is done via a spinner + st.rerun() loop
  with a configurable sleep interval, avoiding websocket complexity.
- Charts are displayed with st.image() since they are PNG files on disk
  (or served by the API as base64 — here we read them directly via file path).
- The follow-up Q&A section uses a chat-style display with st.chat_message()
  for a modern look.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
POLL_INTERVAL = 3  # seconds between status polls


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_analyze(file_bytes: bytes, filename: str, question: Optional[str] = None) -> Dict:
    """POST /analyze — upload CSV and start analysis."""
    files = {"file": (filename, file_bytes, "text/csv")}
    data = {"question": question} if question else {}
    resp = requests.post(f"{API_BASE}/analyze", files=files, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_get_report(session_id: str) -> Dict:
    """GET /report/{session_id} — poll for analysis status and report."""
    resp = requests.get(f"{API_BASE}/report/{session_id}", timeout=15)
    resp.raise_for_status()
    return resp.json()


def api_get_charts(session_id: str) -> List[str]:
    """GET /charts/{session_id} — retrieve chart file paths."""
    resp = requests.get(f"{API_BASE}/charts/{session_id}", timeout=15)
    resp.raise_for_status()
    return resp.json().get("charts", [])


def api_followup(session_id: str, question: str) -> Dict:
    """POST /followup/{session_id} — ask a follow-up question."""
    resp = requests.post(
        f"{API_BASE}/followup/{session_id}",
        json={"question": question},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def api_delete_session(session_id: str) -> None:
    """DELETE /session/{session_id} — clean up session resources."""
    try:
        requests.delete(f"{API_BASE}/session/{session_id}", timeout=10)
    except Exception:
        pass  # Non-critical


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Data Analysis Pipeline",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    """Initialise all st.session_state keys on first run."""
    defaults = {
        "session_id": None,
        "status": "idle",          # idle | queued | running | complete | error
        "report": None,
        "charts": [],
        "analysis_plan": [],
        "dataset_summary": {},
        "reflection": {},
        "error": None,
        "chat_history": [],        # list of {"role": "human"|"ai", "text": "..."}
        "llm_provider": "ollama",
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


_init_session_state()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ Settings")

    # LLM provider selector
    provider = st.selectbox(
        "LLM Provider",
        options=["ollama", "openai"],
        index=0 if st.session_state.llm_provider == "ollama" else 1,
        help="ollama uses local Llama 3.2 (free). openai uses GPT-4o (requires API key).",
    )
    st.session_state.llm_provider = provider
    os.environ["LLM_PROVIDER"] = provider

    st.divider()

    # Session info
    st.subheader("Session Info")
    if st.session_state.session_id:
        st.code(f"ID: {st.session_state.session_id[:8]}...", language=None)
        st.write(f"**Status:** {st.session_state.status}")
        if st.session_state.reflection:
            score = st.session_state.reflection.get("quality_score", "N/A")
            st.write(f"**Quality Score:** {score}/10")
    else:
        st.write("No active session.")

    st.divider()

    if st.button("🗑️ Reset Session", use_container_width=True):
        if st.session_state.session_id:
            api_delete_session(st.session_state.session_id)
        for key in ["session_id", "status", "report", "charts",
                    "analysis_plan", "dataset_summary", "reflection",
                    "error", "chat_history"]:
            st.session_state[key] = (
                [] if isinstance(st.session_state.get(key), list)
                else {} if isinstance(st.session_state.get(key), dict)
                else None
            )
        st.session_state.status = "idle"
        st.rerun()

    st.divider()
    st.caption("AI Data Analysis Pipeline v1.0")
    st.caption(f"API: {API_BASE}")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("📊 AI Data Analysis Pipeline")
st.write(
    "Upload a CSV file and let the AI autonomously plan, execute, "
    "and reflect on a data analysis — then ask follow-up questions."
)

# ---------------------------------------------------------------------------
# Upload section
# ---------------------------------------------------------------------------

st.header("1. Upload Dataset")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv", "tsv"],
    help="Maximum recommended size: 50 MB. Larger files may time out.",
)

col1, col2 = st.columns([2, 1])
with col1:
    initial_question = st.text_input(
        "Optional: Initial question about the dataset",
        placeholder="e.g. Which product has the highest revenue?",
    )
with col2:
    analyze_button = st.button(
        "🚀 Analyze",
        use_container_width=True,
        disabled=(uploaded_file is None or st.session_state.status in ["queued", "running"]),
    )

# ---------------------------------------------------------------------------
# Start analysis
# ---------------------------------------------------------------------------

if analyze_button and uploaded_file is not None:
    with st.spinner("Uploading file and starting analysis..."):
        try:
            response = api_analyze(
                file_bytes=uploaded_file.getvalue(),
                filename=uploaded_file.name,
                question=initial_question or None,
            )
            st.session_state.session_id = response["session_id"]
            st.session_state.status = "queued"
            st.session_state.report = None
            st.session_state.charts = []
            st.session_state.chat_history = []
            st.success(f"Analysis queued! Session ID: {response['session_id'][:8]}...")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to start analysis: {exc}")

# ---------------------------------------------------------------------------
# Polling loop while running
# ---------------------------------------------------------------------------

if st.session_state.status in ["queued", "running"] and st.session_state.session_id:
    with st.spinner("Analysis in progress... This may take 30-120 seconds."):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Poll until complete or error
        attempt = 0
        max_attempts = 60  # 60 × 3s = 3 minutes max
        while attempt < max_attempts:
            try:
                report_data = api_get_report(st.session_state.session_id)
                current_status = report_data.get("status", "unknown")
                st.session_state.status = current_status

                # Update progress bar (heuristic: 10% per 3s up to 90%)
                progress = min(0.9, (attempt + 1) / max_attempts * 3)
                progress_bar.progress(progress)
                status_text.text(f"Status: {current_status} (attempt {attempt + 1}/{max_attempts})")

                if current_status == "complete":
                    st.session_state.report = report_data.get("report")
                    st.session_state.analysis_plan = report_data.get("analysis_plan", [])
                    st.session_state.dataset_summary = report_data.get("dataset_summary", {})
                    st.session_state.reflection = report_data.get("reflection", {})
                    st.session_state.charts = api_get_charts(st.session_state.session_id)
                    progress_bar.progress(1.0)
                    status_text.text("Analysis complete!")
                    time.sleep(0.5)
                    st.rerun()
                    break

                elif current_status == "error":
                    st.session_state.error = report_data.get("error", "Unknown error")
                    progress_bar.empty()
                    st.rerun()
                    break

            except Exception as exc:
                status_text.text(f"Polling error: {exc} — retrying...")

            time.sleep(POLL_INTERVAL)
            attempt += 1

        if attempt >= max_attempts:
            st.session_state.status = "error"
            st.session_state.error = "Analysis timed out after 3 minutes."
            st.rerun()

# ---------------------------------------------------------------------------
# Error display
# ---------------------------------------------------------------------------

if st.session_state.status == "error" and st.session_state.error:
    st.error(f"Analysis failed: {st.session_state.error}")

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

if st.session_state.status == "complete":

    st.divider()

    # --- Dataset summary ---
    st.header("2. Dataset Summary")
    ds = st.session_state.dataset_summary or {}
    shape = ds.get("shape", [0, 0])

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{shape[0]:,}" if shape else "N/A")
    col2.metric("Columns", f"{shape[1]}" if len(shape) > 1 else "N/A")
    col3.metric("Session ID", (st.session_state.session_id or "")[:8] + "...")

    with st.expander("Column Details", expanded=False):
        dtypes = ds.get("dtypes", {})
        null_counts = ds.get("null_counts", {})
        unique_counts = ds.get("unique_counts", {})
        if dtypes:
            col_data = [
                {
                    "Column": col,
                    "Type": dtype,
                    "Null Count": null_counts.get(col, 0),
                    "Unique Values": unique_counts.get(col, "N/A"),
                }
                for col, dtype in dtypes.items()
            ]
            st.table(col_data)
        else:
            st.write("No column details available.")

    # --- Analysis plan ---
    st.header("3. Analysis Plan")
    plan = st.session_state.analysis_plan or []
    if plan:
        for i, step in enumerate(plan, 1):
            st.write(f"**{i}.** {step}")
    else:
        st.write("No analysis plan available.")

    # --- Reflection score ---
    st.header("4. Analysis Quality")
    reflection = st.session_state.reflection or {}
    score = reflection.get("quality_score")

    if score is not None:
        score_float = float(score)
        if score_float >= 7:
            color = "green"
            label = "High Quality"
        elif score_float >= 5:
            color = "orange"
            label = "Medium Quality"
        else:
            color = "red"
            label = "Low Quality"

        st.markdown(
            f"**Quality Score:** "
            f"<span style='color:{color}; font-size:1.4em; font-weight:bold;'>"
            f"{score_float:.1f}/10 — {label}"
            f"</span>",
            unsafe_allow_html=True,
        )

        shallow = reflection.get("shallow_areas", [])
        suggestions = reflection.get("suggestions", [])
        if shallow:
            with st.expander("Areas Needing Deeper Analysis"):
                for item in shallow:
                    st.write(f"- {item}")
        if suggestions:
            with st.expander("DataCritic Suggestions"):
                for sug in suggestions:
                    st.write(f"- {sug}")
    else:
        st.write("Reflection data not available.")

    # --- Charts ---
    st.header("5. Visualisations")
    charts = st.session_state.charts or []
    if charts:
        num_cols = min(2, len(charts))
        cols = st.columns(num_cols)
        for idx, chart_path in enumerate(charts):
            chart_path = Path(chart_path)
            if chart_path.exists():
                with cols[idx % num_cols]:
                    st.image(str(chart_path), caption=chart_path.stem.replace("_", " "), use_container_width=True)
            else:
                cols[idx % num_cols].warning(f"Chart file not found: {chart_path.name}")
    else:
        st.write("No charts were generated.")

    # --- Report ---
    st.header("6. Analysis Report")
    report = st.session_state.report or ""
    if report:
        # Download button
        st.download_button(
            label="📥 Download Report (Markdown)",
            data=report,
            file_name="analysis_report.md",
            mime="text/markdown",
        )
        st.markdown(report, unsafe_allow_html=False)
    else:
        st.write("Report not yet available.")

    # --- Follow-up Q&A ---
    st.divider()
    st.header("7. Follow-up Questions")
    st.write("Ask questions about the analysis. The AI uses the cached results — no re-analysis needed.")

    # Display conversation history
    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.write(turn["text"])

    # Input
    followup_question = st.chat_input("Ask a follow-up question...")
    if followup_question:
        # Add human turn immediately
        st.session_state.chat_history.append({"role": "user", "text": followup_question})
        with st.chat_message("user"):
            st.write(followup_question)

        # Call API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = api_followup(st.session_state.session_id, followup_question)
                    answer = result.get("answer", "No answer generated.")
                except Exception as exc:
                    answer = f"Error: {exc}"

            st.write(answer)
            st.session_state.chat_history.append({"role": "assistant", "text": answer})

# ---------------------------------------------------------------------------
# Idle state — show instructions
# ---------------------------------------------------------------------------

if st.session_state.status == "idle":
    st.info(
        "Upload a CSV file above and click **Analyze** to start. "
        "The AI will autonomously:\n"
        "1. Profile your dataset\n"
        "2. Create an analysis plan\n"
        "3. Execute pandas computations\n"
        "4. Generate charts\n"
        "5. Reflect on quality and iterate if needed\n"
        "6. Write a comprehensive insights report\n\n"
        "Then you can ask follow-up questions in natural language."
    )
