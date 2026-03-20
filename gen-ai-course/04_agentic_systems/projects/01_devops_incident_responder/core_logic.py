"""
core_logic.py

Standalone demonstration script for the AI DevOps Incident Responder.

This script walks through every stage of the incident response pipeline
sequentially, printing detailed output at each step.  It is designed to:
1. Work without a running API server or Streamlit UI
2. Be runnable with just OPENAI_API_KEY set in the environment or .env file
3. Demonstrate the full HITL pattern by auto-approving for the demo

Usage:
    python core_logic.py

Environment:
    OPENAI_API_KEY  - Required for LLM-powered nodes (planner, diagnoser, fix_proposer)
    DRY_RUN=true    - Default: no actual system commands are executed
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any other imports so OPENAI_API_KEY is available
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    """Print a formatted section header."""
    width = 72
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def print_anomalies(anomalies: list) -> None:
    """Print anomalies with severity indicators."""
    severity_icons = {
        "critical": "[CRITICAL]",
        "high": "[HIGH    ]",
        "medium": "[MEDIUM  ]",
        "low": "[LOW     ]",
    }
    for a in anomalies:
        icon = severity_icons.get(a.get("severity", "low"), "[?]")
        print(f"  {icon} {a.get('type', '?').replace('_', ' ').upper()}")
        print(f"           Value: {a.get('value')}  |  Threshold: {a.get('threshold')}")
        print(f"           Service: {a.get('service', 'unknown')}")
        print(f"           {a.get('description', '')}")


def print_audit_trail(audit_log: list) -> None:
    """Print the audit log as a timeline."""
    for entry in audit_log:
        ts = entry.get("timestamp", "")[:19].replace("T", " ")
        agent = entry.get("agent", "?").ljust(18)
        action = entry.get("action", "")
        result = entry.get("result", "")[:80]
        print(f"  {ts}  [{agent}]  {action}")
        if result:
            print(f"               → {result}")


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full incident response pipeline as a standalone demo."""

    print("\n" + "=" * 72)
    print("  AI DEVOPS INCIDENT RESPONDER — STANDALONE DEMO")
    print("  Powered by LangGraph + GPT-4o")
    print("=" * 72)

    # -----------------------------------------------------------------------
    # Step 0: Load sample log
    # -----------------------------------------------------------------------
    section("STEP 0: Loading Sample Log")

    log_path = Path(__file__).parent / "data" / "sample_logs" / "high_cpu_incident.log"
    if log_path.exists():
        raw_logs = log_path.read_text(encoding="utf-8")
        print(f"  Loaded: {log_path}")
        print(f"  Lines: {len(raw_logs.splitlines())}")
    else:
        # Fallback if file not found
        raw_logs = """2024-01-15 14:23:01 ERROR app-server-01 CPU usage: 94.5% (threshold: 90%)
2024-01-15 14:23:05 CRITICAL app-server-01 Memory pressure detected: 87% used
2024-01-15 14:23:10 ERROR nginx HTTP 503 Service Unavailable - upstream timeout
2024-01-15 14:23:15 ERROR nginx HTTP 500 Internal Server Error
2024-01-15 14:23:20 ERROR nginx HTTP 503 Service Unavailable
2024-01-15 14:23:25 CRITICAL app-server-01 CPU usage: 97.2% — approaching hard limit"""
        print("  Using fallback sample log (file not found at expected path)")

    print("\n  Preview (first 3 lines):")
    for line in raw_logs.strip().splitlines()[:3]:
        print(f"  | {line}")
    print("  ...")

    # -----------------------------------------------------------------------
    # Step 1: Detector node
    # -----------------------------------------------------------------------
    section("STEP 1: DETECTOR — Parsing Logs & Detecting Anomalies")
    print("  Design: Rule-based detection is cheaper/faster than LLM detection.")
    print("          Thresholds are tunable without redeploying the model.")

    from agent.state import make_initial_state
    incident_id = str(uuid.uuid4())
    state = make_initial_state(raw_logs=raw_logs, incident_id=incident_id)
    print(f"\n  Incident ID: {incident_id}")

    from agent.nodes import detector
    start = time.time()
    detector_result = detector(state)
    elapsed = time.time() - start
    state.update(detector_result)

    print(f"\n  Detection completed in {elapsed:.2f}s")
    print(f"  Overall Severity: {state['severity'].upper()}")
    print(f"  Anomalies Detected: {len(state['detected_anomalies'])}")

    print_anomalies(state["detected_anomalies"])

    # -----------------------------------------------------------------------
    # Step 2: Planner node
    # -----------------------------------------------------------------------
    section("STEP 2: PLANNER — Generating Investigation Plan")
    print("  Design: GPT-4o creates a structured plan so all subsequent nodes")
    print("          share a mental model of what needs to be investigated.")

    if not os.getenv("OPENAI_API_KEY"):
        print("\n  [SKIP] OPENAI_API_KEY not set. Using mock plan.")
        state["investigation_plan"] = [
            "Identify top CPU-consuming processes with 'top -b -n 1'",
            "Check for runaway processes: 'ps aux --sort=-%cpu | head -10'",
            "Review recent deployments and configuration changes",
            "Analyze application logs for error patterns and exceptions",
            "Check Kubernetes HPA and auto-scaling status",
            "Prepare and validate remediation steps",
        ]
    else:
        from agent.nodes import planner
        start = time.time()
        planner_result = planner(state)
        elapsed = time.time() - start
        state.update(planner_result)
        print(f"\n  Planning completed in {elapsed:.2f}s")

    print("\n  Investigation Plan:")
    for i, step in enumerate(state["investigation_plan"], 1):
        print(f"    {i}. {step}")

    # -----------------------------------------------------------------------
    # Step 3: Diagnoser node (ReAct loop)
    # -----------------------------------------------------------------------
    section("STEP 3: DIAGNOSER — ReAct Loop (3 Iterations)")
    print("  Design: Observe → Think → Act loop. Capped at MAX_REACT_ITERATIONS=3")
    print("          to prevent infinite loops — a critical failure mode in agents.")
    print("  Each iteration: fetch_metrics() + parse_logs() → LLM reasoning")

    if not os.getenv("OPENAI_API_KEY"):
        print("\n  [SKIP] OPENAI_API_KEY not set. Using mock diagnosis.")
        state["diagnosis"] = (
            "[Iteration 1] Initial observation: CPU at 94.5%, memory at 87%. "
            "Java process PID 18423 consuming 68% CPU sustained for 8+ minutes.\n\n"
            "[Iteration 2] Evidence: Thread pool exhausted (128/128), GC pause 8.4s, "
            "DB connections 100/100. Pattern suggests a blocking operation causing thread accumulation.\n\n"
            "[Iteration 3] Root cause hypothesis: Infinite retry loop in order-processing-service "
            "is creating new threads faster than they complete. Each thread holds a DB connection, "
            "causing connection exhaustion and cascading timeouts."
        )
        state["iteration_count"] = 3
    else:
        from agent.nodes import diagnoser
        start = time.time()
        diagnoser_result = diagnoser(state)
        elapsed = time.time() - start
        state.update(diagnoser_result)
        print(f"\n  Diagnosis completed in {elapsed:.2f}s ({state['iteration_count']} iterations)")

    print("\n  Root Cause Diagnosis:")
    for paragraph in state["diagnosis"].split("\n\n"):
        if paragraph.strip():
            print(f"\n  {paragraph.strip()}")

    # -----------------------------------------------------------------------
    # Step 4: Runbook searcher
    # -----------------------------------------------------------------------
    section("STEP 4: RUNBOOK SEARCHER — Finding Relevant Procedures")
    print("  Design: TF-IDF search runs AFTER diagnosis so the query includes")
    print("          the root-cause hypothesis, improving result relevance.")

    from agent.nodes import runbook_searcher
    start = time.time()
    runbook_result = runbook_searcher(state)
    elapsed = time.time() - start
    state.update(runbook_result)

    print(f"\n  Search completed in {elapsed:.2f}s")
    print(f"  Runbook matches found: {len(state['runbook_matches'])}")

    for i, match in enumerate(state["runbook_matches"], 1):
        print(f"\n  Match #{i}:")
        # Print just the first 150 chars of each match
        preview = match[:150].replace("\n", " ")
        print(f"    {preview}...")

    # -----------------------------------------------------------------------
    # Step 5: Fix proposer
    # -----------------------------------------------------------------------
    section("STEP 5: FIX PROPOSER — Proposing Remediation Steps")
    print("  Design: RAG pattern — runbook excerpts injected as context so GPT-4o")
    print("          proposes known-good commands rather than hallucinating new ones.")

    if not os.getenv("OPENAI_API_KEY"):
        print("\n  [SKIP] OPENAI_API_KEY not set. Using fallback fixes.")
        from agent.nodes import _fallback_fixes
        state["proposed_fixes"] = _fallback_fixes(state["detected_anomalies"], "mock")
        state["status"] = "awaiting_approval"
    else:
        from agent.nodes import fix_proposer
        start = time.time()
        fix_result = fix_proposer(state)
        elapsed = time.time() - start
        state.update(fix_result)
        print(f"\n  Fix proposal completed in {elapsed:.2f}s")

    print("\n  Proposed Fixes:")
    risk_icons = {"low": "[LOW RISK]   ", "medium": "[MED RISK]   ", "high": "[HIGH RISK]  "}
    for fix in state["proposed_fixes"]:
        risk = fix.get("risk_level", "medium")
        icon = risk_icons.get(risk, "[RISK ?]     ")
        print(f"\n  Step {fix.get('step', '?')}: {icon}{fix.get('command', '')}")
        print(f"           What: {fix.get('description', '')}")
        if fix.get("rollback"):
            print(f"           Rollback: {fix.get('rollback')}")

    # -----------------------------------------------------------------------
    # Step 6: HITL checkpoint
    # -----------------------------------------------------------------------
    section("STEP 6: HITL CHECKPOINT — Human Approval Required")
    print("  Design: HITL prevents automated execution of potentially dangerous")
    print("          commands. The graph PAUSES here in production until a human")
    print("          explicitly approves via the API (POST /approve/{incident_id}).")
    print()
    print("  ┌─────────────────────────────────────────────────────────────────┐")
    print("  │                  ⚠️  HUMAN APPROVAL REQUIRED  ⚠️                │")
    print("  │                                                                   │")
    print(f"  │  Incident: {incident_id[:8]}...                                    │")
    print(f"  │  Severity: {state['severity'].upper():<10}                                   │")
    print(f"  │  Fixes proposed: {len(state['proposed_fixes'])}                                         │")
    print("  │                                                                   │")
    print("  │  In production: POST /approve/{incident_id} {\"approved\": true}  │")
    print("  └─────────────────────────────────────────────────────────────────┘")

    from agent.nodes import hitl_checkpoint
    hitl_result = hitl_checkpoint(state)
    state.update(hitl_result)

    print(f"\n  Status set to: {state['status']}")

    # Auto-approve for demo purposes
    print("\n  [DEMO] Auto-approving for demonstration (DRY_RUN=true)...")
    time.sleep(1)  # Simulate human review time

    state["human_approved"] = True
    state["human_notes"] = "Auto-approved for demo purposes. DRY_RUN=true — no actual commands executed."

    # -----------------------------------------------------------------------
    # Step 7: Executor
    # -----------------------------------------------------------------------
    section("STEP 7: EXECUTOR — Applying Fixes (DRY RUN)")
    print("  Design: DRY_RUN=true by default means no actual system changes occur.")
    print("          Set DRY_RUN=false to execute real commands (requires whitelist).")
    print("  Defense-in-depth: executor checks human_approved AGAIN even if HITL ran.")

    from agent.nodes import executor
    start = time.time()
    exec_result = executor(state)
    elapsed = time.time() - start
    state.update(exec_result)

    print(f"\n  Execution completed in {elapsed:.2f}s")
    print(f"\n  Execution Results:")
    for fix_result in state.get("executed_fixes", []):
        icon = "✓" if ("OK" in fix_result or "DRY-RUN" in fix_result) else "✗"
        print(f"    [{icon}] {fix_result}")

    # -----------------------------------------------------------------------
    # Step 8: Outcome logger
    # -----------------------------------------------------------------------
    section("STEP 8: OUTCOME LOGGER — Resolution Summary & History")
    print("  Design: Saves incident to IncidentHistoryMemory (file-based) for")
    print("          future retrieval. Future incidents with similar symptoms")
    print("          will surface this resolution as a 'past incident' match.")

    from agent.nodes import outcome_logger
    start = time.time()
    outcome_result = outcome_logger(state)
    elapsed = time.time() - start
    state.update(outcome_result)

    print(f"\n  Outcome logger completed in {elapsed:.2f}s")
    print(f"  Status: {state['status'].upper()}")
    print("\n  Resolution Summary:")
    print("  " + "-" * 68)
    for line in state["outcome"].splitlines():
        print(f"  {line}")

    # -----------------------------------------------------------------------
    # Step 9: Audit trail
    # -----------------------------------------------------------------------
    section("STEP 9: AUDIT TRAIL — Complete Action Timeline")
    print("  Design: Every agent action is recorded with timestamp, agent name,")
    print("          action description, and result. This provides a tamper-")
    print("          evident timeline for post-incident review and compliance.")
    print()

    audit_log = state.get("audit_log", [])
    print(f"  Total audit entries: {len(audit_log)}")
    print()
    print_audit_trail(audit_log)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    section("DEMO COMPLETE")
    print(f"  Incident ID: {incident_id}")
    print(f"  Final Status: {state['status'].upper()}")
    print(f"  Severity: {state['severity'].upper()}")
    print(f"  Anomalies detected: {len(state['detected_anomalies'])}")
    print(f"  Plan steps: {len(state['investigation_plan'])}")
    print(f"  ReAct iterations: {state['iteration_count']}")
    print(f"  Runbook matches: {len(state['runbook_matches'])}")
    print(f"  Fixes proposed: {len(state['proposed_fixes'])}")
    print(f"  Fixes executed: {len(state['executed_fixes'])}")
    print(f"  Audit entries: {len(state.get('audit_log', []))}")
    print(f"  Human approved: {state.get('human_approved', False)}")
    print()
    print("  To run the full API + UI:")
    print("    1. uvicorn api.routes:app --reload --port 8000")
    print("    2. streamlit run ui/app.py")
    print()
    print("  To run tests:")
    print("    pytest tests/ -v")
    print()


if __name__ == "__main__":
    main()
