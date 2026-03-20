"""
ui/app.py

Streamlit dashboard for the AI DevOps Incident Responder.

Features:
- Log input with pre-filled sample logs
- Real-time status polling (detecting → planning → diagnosing...)
- Anomaly display with severity color coding
- Investigation plan as a checklist
- Diagnosis display
- Runbook matches as expandable sections
- Proposed fixes table
- HITL approval panel with Approve / Reject buttons
- Execution results display
- Audit log timeline
- Sidebar: incident metadata, severity badge

Design Decision:
    The UI calls the FastAPI backend (configured via API_BASE_URL env var).
    This keeps the UI stateless and allows the backend to be scaled independently.
    For single-machine demos, the UI and API run on different ports (8501, 8000).
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
POLL_INTERVAL_SEC = 2  # How often to refresh status while waiting
MAX_POLL_ATTEMPTS = 60  # Stop polling after 2 minutes

# Severity color mapping (Streamlit markdown colors)
SEVERITY_COLORS = {
    "critical": "#FF0000",
    "high":     "#FF6600",
    "medium":   "#FFB800",
    "low":      "#00AA00",
    "unknown":  "#888888",
}

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🟢",
    "unknown":  "⚪",
}

STATUS_EMOJI = {
    "queued":             "⏳",
    "detecting":          "🔍",
    "planning":           "📋",
    "diagnosing":         "🔬",
    "awaiting_approval":  "⚠️",
    "executing":          "⚙️",
    "resolved":           "✅",
    "failed":             "❌",
    "rejected":           "🚫",
}

# Sample log content pre-filled in the text area
SAMPLE_LOG_CPU = open(
    os.path.join(os.path.dirname(__file__), "..", "data", "sample_logs", "high_cpu_incident.log"),
    "r", encoding="utf-8"
).read() if os.path.exists(
    os.path.join(os.path.dirname(__file__), "..", "data", "sample_logs", "high_cpu_incident.log")
) else "2024-01-15 14:23:01 ERROR app-server-01 CPU usage: 94.5% (threshold: 90%)\n2024-01-15 14:23:05 CRITICAL app-server-01 Memory pressure detected: 87% used"

SAMPLE_LOG_DISK = open(
    os.path.join(os.path.dirname(__file__), "..", "data", "sample_logs", "disk_full_incident.log"),
    "r", encoding="utf-8"
).read() if os.path.exists(
    os.path.join(os.path.dirname(__file__), "..", "data", "sample_logs", "disk_full_incident.log")
) else "2024-01-15 16:45:01 ERROR disk-monitor /var/log filesystem: 96% capacity used"

SAMPLE_LOG_ERROR = open(
    os.path.join(os.path.dirname(__file__), "..", "data", "sample_logs", "error_spike_incident.log"),
    "r", encoding="utf-8"
).read() if os.path.exists(
    os.path.join(os.path.dirname(__file__), "..", "data", "sample_logs", "error_spike_incident.log")
) else "2024-01-15 18:00:01 ERROR payment-service HTTP 500 Internal Server Error"

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def api_post(endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """POST to the backend API and return the JSON response."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {API_BASE_URL}. Is the API server running?")
        return None
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text[:200]}")
        return None
    except Exception as exc:
        st.error(f"Request failed: {str(exc)}")
        return None


def api_get(endpoint: str) -> Optional[Dict[str, Any]]:
    """GET from the backend API and return the JSON response."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None


def poll_status(incident_id: str, max_attempts: int = MAX_POLL_ATTEMPTS) -> Optional[Dict[str, Any]]:
    """
    Poll /status/{incident_id} until status reaches a terminal or HITL state.

    Returns the final status dict when the graph pauses or completes.
    """
    terminal_statuses = {"awaiting_approval", "resolved", "failed", "rejected"}
    status_data = None

    progress_bar = st.progress(0, text="Starting analysis...")
    status_placeholder = st.empty()

    for attempt in range(max_attempts):
        status_data = api_get(f"/status/{incident_id}")
        if status_data is None:
            time.sleep(POLL_INTERVAL_SEC)
            continue

        current_status = status_data.get("status", "unknown")
        progress = min((attempt + 1) / max_attempts, 0.95)
        status_label = STATUS_EMOJI.get(current_status, "⏳") + f" {current_status.replace('_', ' ').title()}..."
        progress_bar.progress(progress, text=status_label)
        status_placeholder.info(f"Status: **{current_status}** | Severity: **{status_data.get('severity', 'unknown')}**")

        if current_status in terminal_statuses:
            progress_bar.progress(1.0, text="Analysis complete!")
            break

        time.sleep(POLL_INTERVAL_SEC)

    progress_bar.empty()
    status_placeholder.empty()
    return status_data


# ---------------------------------------------------------------------------
# UI rendering helpers
# ---------------------------------------------------------------------------


def render_severity_badge(severity: str) -> str:
    """Return an HTML-safe colored severity badge."""
    color = SEVERITY_COLORS.get(severity, "#888888")
    emoji = SEVERITY_EMOJI.get(severity, "⚪")
    return f'<span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-weight:bold;">{emoji} {severity.upper()}</span>'


def render_anomalies(anomalies: List[Dict[str, Any]]) -> None:
    """Render anomaly cards with color coding by severity."""
    if not anomalies:
        st.info("No anomalies detected yet.")
        return

    for anomaly in anomalies:
        severity = anomaly.get("severity", "unknown")
        color = SEVERITY_COLORS.get(severity, "#888888")
        atype = anomaly.get("type", "unknown").replace("_", " ").title()
        value = anomaly.get("value", "?")
        threshold = anomaly.get("threshold", "?")
        service = anomaly.get("service", "unknown")
        description = anomaly.get("description", "")

        st.markdown(
            f"""
            <div style="border-left: 5px solid {color}; padding: 10px; margin: 8px 0;
                        background: {color}15; border-radius: 4px;">
                <strong>{SEVERITY_EMOJI.get(severity, '')} {atype}</strong>
                &nbsp;|&nbsp;
                <span style="color:{color}; font-weight:bold;">{severity.upper()}</span>
                &nbsp;|&nbsp; Service: <code>{service}</code><br>
                <small>Value: <strong>{value}</strong> | Threshold: {threshold}</small><br>
                <small>{description}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_investigation_plan(plan: List[str]) -> None:
    """Render the investigation plan as an interactive checklist."""
    if not plan:
        st.info("Investigation plan not yet generated.")
        return

    for i, step in enumerate(plan, 1):
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            st.checkbox("", key=f"plan_step_{i}", label_visibility="collapsed")
        with col2:
            st.markdown(f"**Step {i}:** {step}")


def render_proposed_fixes(fixes: List[Dict[str, Any]]) -> None:
    """Render proposed fixes as a colored table."""
    if not fixes:
        st.info("No fixes proposed yet.")
        return

    risk_colors = {"low": "🟢", "medium": "🟡", "high": "🔴"}

    for fix in fixes:
        risk = fix.get("risk_level", "medium")
        risk_icon = risk_colors.get(risk, "⚪")
        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid #ddd; padding: 12px; margin: 8px 0; border-radius: 6px;">
                    <strong>Step {fix.get('step', '?')}:</strong>
                    <code style="background:#f0f0f0; padding:2px 6px; border-radius:3px;">
                        {fix.get('command', '')}
                    </code>
                    &nbsp;&nbsp;{risk_icon} <em>{risk.upper()} RISK</em><br>
                    <small><strong>What:</strong> {fix.get('description', '')}</small><br>
                    <small><strong>Rollback:</strong>
                        <code>{fix.get('rollback', 'None')}</code>
                    </small>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_audit_timeline(audit_log: List[Dict[str, Any]]) -> None:
    """Render audit entries as a vertical timeline."""
    if not audit_log:
        st.info("Audit log is empty.")
        return

    for entry in audit_log:
        ts = entry.get("timestamp", "")[:19].replace("T", " ")
        agent = entry.get("agent", "unknown")
        action = entry.get("action", "")
        result = entry.get("result", "")

        agent_colors = {
            "detector":         "#2196F3",
            "planner":          "#9C27B0",
            "diagnoser":        "#FF9800",
            "runbook_searcher": "#009688",
            "fix_proposer":     "#E91E63",
            "hitl_checkpoint":  "#F44336",
            "executor":         "#607D8B",
            "auto_responder":   "#4CAF50",
            "outcome_logger":   "#795548",
        }
        color = agent_colors.get(agent, "#888888")

        st.markdown(
            f"""
            <div style="border-left: 4px solid {color}; padding: 8px 12px; margin: 6px 0; background: {color}10; border-radius: 0 4px 4px 0;">
                <small style="color: #888;">{ts}</small>
                <span style="background:{color};color:white;padding:1px 8px;border-radius:10px;font-size:0.8em;margin-left:8px;">
                    {agent}
                </span><br>
                <strong>{action}</strong><br>
                <small style="color:#555;">{result[:200]}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main Streamlit application
# ---------------------------------------------------------------------------


def main() -> None:
    """Main Streamlit app entry point."""
    st.set_page_config(
        page_title="AI DevOps Incident Responder",
        page_icon="🚨",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    if "incident_id" not in st.session_state:
        st.session_state.incident_id = None
    if "status_data" not in st.session_state:
        st.session_state.status_data = None
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "approval_submitted" not in st.session_state:
        st.session_state.approval_submitted = False

    # ---------------------------------------------------------------------------
    # Sidebar
    # ---------------------------------------------------------------------------
    with st.sidebar:
        st.title("🚨 Incident Responder")
        st.markdown("---")

        # API connection status
        health = api_get("/health")
        if health:
            st.success(f"API Connected ({API_BASE_URL})")
        else:
            st.error(f"API Unreachable ({API_BASE_URL})")

        st.markdown("---")

        # Current incident metadata
        if st.session_state.incident_id:
            st.markdown("### Current Incident")
            st.code(st.session_state.incident_id[:8] + "...", language=None)

            status_data = st.session_state.status_data
            if status_data:
                severity = status_data.get("severity", "unknown")
                status = status_data.get("status", "unknown")

                st.markdown(f"**Status:** {STATUS_EMOJI.get(status, '⏳')} {status}")
                st.markdown(
                    f"**Severity:** {render_severity_badge(severity)}",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Anomalies:** {len(status_data.get('detected_anomalies', []))}")
                st.markdown(f"**Diagnosis iterations:** {status_data.get('iteration_count', 0)}")

        st.markdown("---")

        # Recent incidents
        st.markdown("### Recent Incidents")
        incidents_data = api_get("/incidents?limit=5")
        if incidents_data:
            for inc in incidents_data.get("incidents", [])[:5]:
                inc_id = inc.get("incident_id", "")[:8]
                inc_status = inc.get("status", "unknown")
                inc_severity = inc.get("severity", "unknown")
                emoji = STATUS_EMOJI.get(inc_status, "⏳")
                sev_emoji = SEVERITY_EMOJI.get(inc_severity, "⚪")
                st.markdown(f"{emoji} {sev_emoji} `{inc_id}...` — {inc_status}")

    # ---------------------------------------------------------------------------
    # Main content
    # ---------------------------------------------------------------------------
    st.title("🚨 AI DevOps Incident Responder")
    st.markdown(
        "Paste system logs below to trigger automated incident analysis with "
        "human-in-the-loop approval before executing remediation."
    )

    # Log selection tabs
    tab_cpu, tab_disk, tab_error, tab_custom = st.tabs([
        "💻 High CPU Sample", "💾 Disk Full Sample", "⚡ Error Spike Sample", "✏️ Custom Logs"
    ])

    with tab_cpu:
        log_input_cpu = st.text_area(
            "High CPU Incident Logs",
            value=SAMPLE_LOG_CPU,
            height=200,
            key="log_cpu",
        )
        if st.button("🔍 Analyze CPU Incident", key="btn_cpu", type="primary"):
            _start_analysis(log_input_cpu)

    with tab_disk:
        log_input_disk = st.text_area(
            "Disk Full Incident Logs",
            value=SAMPLE_LOG_DISK,
            height=200,
            key="log_disk",
        )
        if st.button("🔍 Analyze Disk Incident", key="btn_disk", type="primary"):
            _start_analysis(log_input_disk)

    with tab_error:
        log_input_error = st.text_area(
            "Error Spike Incident Logs",
            value=SAMPLE_LOG_ERROR,
            height=200,
            key="log_error",
        )
        if st.button("🔍 Analyze Error Spike", key="btn_error", type="primary"):
            _start_analysis(log_input_error)

    with tab_custom:
        log_input_custom = st.text_area(
            "Paste your own log lines here:",
            placeholder="2024-01-15 14:23:01 ERROR my-service CPU usage: 94.5%...",
            height=250,
            key="log_custom",
        )
        if st.button("🔍 Analyze Custom Logs", key="btn_custom", type="primary"):
            if log_input_custom.strip():
                _start_analysis(log_input_custom)
            else:
                st.warning("Please paste some log content before analyzing.")

    # ---------------------------------------------------------------------------
    # Results section
    # ---------------------------------------------------------------------------
    if st.session_state.incident_id and st.session_state.status_data:
        st.markdown("---")
        _render_results()


def _start_analysis(raw_logs: str) -> None:
    """Start an incident analysis and poll for results."""
    with st.spinner("Submitting incident for analysis..."):
        result = api_post("/incident", {"raw_logs": raw_logs})
        if result:
            st.session_state.incident_id = result["incident_id"]
            st.session_state.analysis_complete = False
            st.session_state.approval_submitted = False
            st.success(f"Incident created: `{result['incident_id'][:8]}...`")

    if st.session_state.incident_id:
        with st.spinner("Running AI analysis (detector → planner → diagnoser → fix proposer)..."):
            status_data = poll_status(st.session_state.incident_id)
            if status_data:
                st.session_state.status_data = status_data
                st.session_state.analysis_complete = True
                st.rerun()


def _render_results() -> None:
    """Render the full analysis results panel."""
    status_data = st.session_state.status_data
    if not status_data:
        return

    status = status_data.get("status", "unknown")
    severity = status_data.get("severity", "unknown")

    # Status banner
    status_color = {"awaiting_approval": "#FF6600", "resolved": "#00AA00", "failed": "#FF0000"}.get(status, "#2196F3")
    st.markdown(
        f'<div style="background:{status_color}20; border:2px solid {status_color}; '
        f'padding:12px; border-radius:8px; margin-bottom:16px;">'
        f'<strong>{STATUS_EMOJI.get(status, "⏳")} Status: {status.replace("_"," ").upper()}</strong>'
        f' &nbsp;|&nbsp; {render_severity_badge(severity)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Tabbed results view
    (tab_anomalies, tab_plan, tab_diagnosis, tab_runbooks,
     tab_fixes, tab_hitl, tab_execution, tab_audit) = st.tabs([
        "🔍 Anomalies", "📋 Plan", "🔬 Diagnosis", "📚 Runbooks",
        "🔧 Proposed Fixes", "⚠️ HITL Approval", "⚙️ Execution", "📜 Audit Log"
    ])

    with tab_anomalies:
        st.subheader("Detected Anomalies")
        render_anomalies(status_data.get("detected_anomalies", []))

    with tab_plan:
        st.subheader("Investigation Plan")
        render_investigation_plan(status_data.get("investigation_plan", []))

    with tab_diagnosis:
        st.subheader("Root Cause Diagnosis")
        diagnosis = status_data.get("diagnosis", "")
        if diagnosis:
            st.markdown(diagnosis)
        else:
            st.info("Diagnosis not yet generated.")
        iterations = status_data.get("iteration_count", 0)
        if iterations > 0:
            st.caption(f"ReAct loop completed {iterations} iteration(s)")

    with tab_runbooks:
        st.subheader("Matching Runbooks")
        runbook_matches = status_data.get("runbook_matches", [])
        if runbook_matches:
            for i, match in enumerate(runbook_matches, 1):
                with st.expander(f"Runbook Match #{i}", expanded=(i == 1)):
                    st.markdown(f"```\n{match[:800]}\n```")
        else:
            st.info("No runbook matches yet.")

    with tab_fixes:
        st.subheader("Proposed Remediation Steps")
        render_proposed_fixes(status_data.get("proposed_fixes", []))

    with tab_hitl:
        st.subheader("Human-in-the-Loop Approval")
        _render_hitl_panel(status_data, status)

    with tab_execution:
        st.subheader("Execution Results")
        executed_fixes = status_data.get("executed_fixes", [])
        if executed_fixes:
            for fix in executed_fixes:
                icon = "✅" if ("OK" in fix or "DRY-RUN" in fix or "AUTO" in fix) else "❌"
                st.markdown(f"{icon} `{fix}`")
        else:
            st.info("No fixes executed yet.")

        outcome = status_data.get("outcome", "")
        if outcome:
            st.markdown("### Resolution Summary")
            st.markdown(outcome)

    with tab_audit:
        st.subheader("Audit Trail")
        # Fetch fresh audit log
        audit_data = api_get(f"/audit/{st.session_state.incident_id}")
        entries = audit_data.get("entries", []) if audit_data else status_data.get("audit_log", [])
        render_audit_timeline(entries)

    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh Status"):
        fresh = api_get(f"/status/{st.session_state.incident_id}")
        if fresh:
            st.session_state.status_data = fresh
            st.rerun()


def _render_hitl_panel(status_data: Dict[str, Any], status: str) -> None:
    """Render the HITL approval / rejection panel."""
    if status == "resolved":
        if status_data.get("human_approved", False):
            st.success("✅ Incident approved and resolved.")
        else:
            st.info("ℹ️ Incident resolved (auto-response or rejected).")
        return

    if status == "awaiting_approval":
        st.warning("⚠️ **HUMAN APPROVAL REQUIRED** — Review the proposed fixes before execution.")

        proposed_fixes = status_data.get("proposed_fixes", [])
        if not proposed_fixes:
            st.error("No proposed fixes to review.")
            return

        # Summary table
        st.markdown("### Fix Summary")
        fix_rows = []
        for fix in proposed_fixes:
            risk = fix.get("risk_level", "medium")
            risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk, "⚪")
            fix_rows.append({
                "Step": fix.get("step", "?"),
                "Command": fix.get("command", ""),
                "Risk": f"{risk_icon} {risk.upper()}",
                "Description": fix.get("description", "")[:80],
            })
        st.table(fix_rows)

        # Approval form
        st.markdown("### Your Decision")
        notes = st.text_area(
            "Approval notes (optional — add context or rejection reason):",
            placeholder="e.g., 'Approved after verifying no active transactions' or 'Rejected — staging test needed first'",
            key="approval_notes",
        )

        if not st.session_state.approval_submitted:
            col_approve, col_reject = st.columns(2)

            with col_approve:
                if st.button("✅ APPROVE & EXECUTE", type="primary", use_container_width=True):
                    _submit_approval(approved=True, notes=notes)

            with col_reject:
                if st.button("🚫 REJECT", type="secondary", use_container_width=True):
                    _submit_approval(approved=False, notes=notes or "Rejected by operator.")
        else:
            st.info("Approval decision submitted. Fetching results...")
    else:
        st.info(f"Current status: **{status}** — approval panel will appear when analysis completes.")


def _submit_approval(approved: bool, notes: str) -> None:
    """Submit the human approval decision to the API."""
    incident_id = st.session_state.incident_id
    with st.spinner("Processing decision..."):
        result = api_post(
            f"/approve/{incident_id}",
            {"approved": approved, "notes": notes},
        )
        if result:
            st.session_state.approval_submitted = True
            st.session_state.status_data = api_get(f"/status/{incident_id}")
            decision = "APPROVED" if approved else "REJECTED"
            st.success(f"Decision submitted: {decision}")
            st.rerun()


if __name__ == "__main__":
    main()
