"""
agent/nodes.py

All LangGraph node functions for the AI DevOps Incident Responder.

Node execution order:
    detector → severity_router → planner / auto_responder
             → diagnoser → runbook_searcher → fix_proposer
             → hitl_checkpoint [INTERRUPT] → executor
             → outcome_logger → END

Design Decisions:
- Each node is a pure function (state: IncidentState) -> Dict that returns
  only the keys it changed. LangGraph merges these partial updates.
- The diagnoser uses a ReAct loop capped at MAX_REACT_ITERATIONS (default 3)
  to prevent infinite loops — a common failure mode in agentic systems.
- GPT-4o is used only where natural language reasoning adds value (planner,
  diagnoser reasoning, fix_proposer). Deterministic rule-based logic is used
  for detection and routing to keep costs low and outputs predictable.
- Audit entries are created by every node to provide a complete tamper-
  evident timeline for post-incident review.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.memory import IncidentHistoryMemory, RunbookMemory
from agent.state import Anomaly, AuditEntry, FixStep, IncidentState
from agent.tools import execute_fix, fetch_metrics, parse_logs, search_runbook

load_dotenv()

# ---------------------------------------------------------------------------
# Shared LLM instance
# Design Decision: A single shared ChatOpenAI instance avoids re-creating
# the HTTP client on every node call (expensive). temperature=0 is used for
# all LLM calls to maximize determinism and auditability.
# ---------------------------------------------------------------------------
_llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

# Shared memory instances (loaded once at module import)
_runbook_memory = RunbookMemory(
    runbook_dir=os.getenv("RUNBOOK_DIR", "./data/runbooks")
)
_history_memory = IncidentHistoryMemory(
    history_dir=os.getenv("INCIDENT_HISTORY_DIR", "./data/incident_history")
)

MAX_REACT_ITERATIONS = int(os.getenv("MAX_REACT_ITERATIONS", "3"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Helper: audit entry factory
# ---------------------------------------------------------------------------

def _audit(incident_id: str, agent: str, action: str, result: str) -> Dict[str, Any]:
    """Create an AuditEntry dict with the current UTC timestamp."""
    return AuditEntry(
        agent=agent,
        action=action,
        result=result[:500],  # Truncate to keep audit log manageable
        incident_id=incident_id,
    ).to_dict()


def _extend_audit(state: IncidentState, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a new audit log list with entry appended (immutable update)."""
    return list(state.get("audit_log", [])) + [entry]


# ---------------------------------------------------------------------------
# Anomaly detection thresholds
# ---------------------------------------------------------------------------

THRESHOLDS = {
    "cpu_percent":    {"medium": 75.0, "high": 85.0, "critical": 90.0},
    "memory_percent": {"medium": 70.0, "high": 80.0, "critical": 85.0},
    "disk_percent":   {"medium": 80.0, "high": 90.0, "critical": 95.0},
    "error_rate":     {"medium": 2.0,  "high": 4.0,  "critical": 5.0},
    "http_5xx":       {"medium": 5,    "high": 10,   "critical": 20},
}


def _derive_severity(anomalies: List[Dict[str, Any]]) -> str:
    """
    Derive overall incident severity from the list of detected anomalies.

    Rules:
    - Any 'critical' anomaly → severity = 'critical'
    - 2+ 'high' anomalies → severity = 'critical'
    - Any 'high' anomaly → severity = 'high'
    - 2+ 'medium' anomalies → severity = 'high'
    - Otherwise → severity = 'medium' or 'low'
    """
    if not anomalies:
        return "low"

    severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for a in anomalies:
        sev = a.get("severity", "low")
        counts[sev] = counts.get(sev, 0) + 1

    if counts["critical"] >= 1:
        return "critical"
    if counts["high"] >= 2:
        return "critical"
    if counts["high"] >= 1:
        return "high"
    if counts["medium"] >= 2:
        return "high"
    if counts["medium"] >= 1:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Node 1: detector
# ---------------------------------------------------------------------------

def detector(state: IncidentState) -> Dict[str, Any]:
    """
    Parse raw logs and detect anomalies using rule-based thresholds.

    Design Decision:
        Rule-based detection is cheaper and more predictable than LLM-based
        detection. False negatives can be tuned by adjusting THRESHOLDS without
        re-deploying the model.

    Detects:
    - CPU > 90% (critical), > 85% (high), > 75% (medium)
    - Memory > 85% (critical), > 80% (high), > 70% (medium)
    - Disk > 95% (critical), > 90% (high), > 80% (medium)
    - Error rate > 5/s (critical), > 4/s (high), > 2/s (medium)
    - HTTP 5xx count > 20 (critical), > 10 (high), > 5 (medium)
    - Repeated CRITICAL log lines
    """
    incident_id = state.get("incident_id", "unknown")
    raw_logs = state.get("raw_logs", "")

    # Parse logs using the tool (no LLM call needed)
    parsed = parse_logs.invoke({"raw_logs": raw_logs})

    anomalies: List[Dict[str, Any]] = []

    # --- 1. Detect from parsed log text via regex ---
    # CPU anomaly from log text
    cpu_pattern = re.compile(r"CPU\s+usage[:\s]+(\d+\.?\d*)%", re.IGNORECASE)
    for match in cpu_pattern.finditer(raw_logs):
        cpu_val = float(match.group(1))
        for sev_level in ["critical", "high", "medium"]:
            if cpu_val >= THRESHOLDS["cpu_percent"][sev_level]:
                # Find the service in the nearby log line
                line_start = raw_logs.rfind("\n", 0, match.start()) + 1
                line_end = raw_logs.find("\n", match.end())
                line = raw_logs[line_start: line_end if line_end != -1 else len(raw_logs)]
                svc_match = re.search(r"([a-z][a-z0-9-]+(?:-\d+)?)\s+(?:CPU|CRITICAL|ERROR)", line, re.IGNORECASE)
                service = svc_match.group(1) if svc_match else parsed.get("services", ["unknown"])[0] if parsed.get("services") else "unknown"

                anomalies.append(Anomaly(
                    type="cpu_high",
                    value=cpu_val,
                    threshold=THRESHOLDS["cpu_percent"][sev_level],
                    severity=sev_level,
                    service=service,
                    description=f"CPU usage at {cpu_val}% exceeds {sev_level} threshold of {THRESHOLDS['cpu_percent'][sev_level]}%",
                ).to_dict())
                break  # Only record the highest severity breach

    # Memory anomaly from log text
    mem_pattern = re.compile(r"[Mm]emory\s+(?:pressure\s+detected|usage)[:\s]+(\d+\.?\d*)%", re.IGNORECASE)
    for match in mem_pattern.finditer(raw_logs):
        mem_val = float(match.group(1))
        for sev_level in ["critical", "high", "medium"]:
            if mem_val >= THRESHOLDS["memory_percent"][sev_level]:
                anomalies.append(Anomaly(
                    type="memory_high",
                    value=mem_val,
                    threshold=THRESHOLDS["memory_percent"][sev_level],
                    severity=sev_level,
                    service=parsed.get("services", ["unknown"])[0] if parsed.get("services") else "unknown",
                    description=f"Memory at {mem_val}% exceeds {sev_level} threshold of {THRESHOLDS['memory_percent'][sev_level]}%",
                ).to_dict())
                break

    # Disk anomaly from log text
    disk_pattern = re.compile(r"(?:filesystem|disk)[:\s]+(\d+\.?\d*)%\s+capacity|(\d+\.?\d*)%\s+(?:used|full)", re.IGNORECASE)
    for match in disk_pattern.finditer(raw_logs):
        disk_val = float(match.group(1) or match.group(2))
        for sev_level in ["critical", "high", "medium"]:
            if disk_val >= THRESHOLDS["disk_percent"][sev_level]:
                anomalies.append(Anomaly(
                    type="disk_full",
                    value=disk_val,
                    threshold=THRESHOLDS["disk_percent"][sev_level],
                    severity=sev_level,
                    service="filesystem",
                    description=f"Disk usage at {disk_val}% exceeds {sev_level} threshold of {THRESHOLDS['disk_percent'][sev_level]}%",
                ).to_dict())
                break

    # HTTP 5xx spike from parsed log
    http_5xx_count = parsed.get("http_5xx_count", 0)
    if http_5xx_count > 0:
        for sev_level in ["critical", "high", "medium"]:
            if http_5xx_count >= THRESHOLDS["http_5xx"][sev_level]:
                anomalies.append(Anomaly(
                    type="error_spike",
                    value=float(http_5xx_count),
                    threshold=float(THRESHOLDS["http_5xx"][sev_level]),
                    severity=sev_level,
                    service=",".join(parsed.get("services", ["unknown"])[:3]),
                    description=f"HTTP 5xx error count: {http_5xx_count} (threshold: {THRESHOLDS['http_5xx'][sev_level]})",
                ).to_dict())
                break

    # CRITICAL log lines as anomaly indicator
    critical_lines = parsed.get("critical_lines", [])
    if len(critical_lines) > 0 and not any(a["type"] in ["cpu_high", "memory_high", "disk_full"] for a in anomalies):
        anomalies.append(Anomaly(
            type="critical_log_event",
            value=float(len(critical_lines)),
            threshold=1.0,
            severity="high",
            service=parsed.get("services", ["unknown"])[0] if parsed.get("services") else "unknown",
            description=f"Detected {len(critical_lines)} CRITICAL log line(s): {critical_lines[0][:100]}",
        ).to_dict())

    # No space left on device
    if "no space left on device" in raw_logs.lower():
        if not any(a["type"] == "disk_full" for a in anomalies):
            anomalies.append(Anomaly(
                type="disk_full",
                value=100.0,
                threshold=95.0,
                severity="critical",
                service="filesystem",
                description="Kernel reported 'No space left on device' — filesystem 100% full",
            ).to_dict())

    # OOM / memory exhaustion
    if re.search(r"out of memory|oomkill|oom killer", raw_logs, re.IGNORECASE):
        if not any(a["type"] == "memory_high" for a in anomalies):
            anomalies.append(Anomaly(
                type="memory_high",
                value=100.0,
                threshold=85.0,
                severity="critical",
                service="kernel",
                description="OOM Killer activated — process killed due to memory exhaustion",
            ).to_dict())

    # De-duplicate anomalies by type (keep highest severity)
    seen_types: Dict[str, Dict[str, Any]] = {}
    for a in anomalies:
        t = a["type"]
        sev_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if t not in seen_types or sev_rank.get(a["severity"], 0) > sev_rank.get(seen_types[t]["severity"], 0):
            seen_types[t] = a
    anomalies = list(seen_types.values())

    severity = _derive_severity(anomalies)

    audit_entry = _audit(
        incident_id, "detector",
        action=f"Parsed {parsed.get('total_lines', 0)} log lines, detected {len(anomalies)} anomaly/anomalies",
        result=f"Severity={severity}, types={[a['type'] for a in anomalies]}",
    )

    return {
        "detected_anomalies": anomalies,
        "severity": severity,
        "status": "planning" if severity in ("medium", "high", "critical") else "auto_responding",
        "audit_log": _extend_audit(state, audit_entry),
    }


# ---------------------------------------------------------------------------
# Node 2: severity_router (used as a conditional edge function)
# ---------------------------------------------------------------------------

def severity_router(state: IncidentState) -> str:
    """
    Route based on incident severity.

    Returns:
        'low'      → auto_responder (no human needed)
        'medium'   → planner (LLM-driven analysis)
        'high'     → planner
        'critical' → planner (fastest path to human review)
    """
    severity = state.get("severity", "low")
    if severity == "low":
        return "low"
    return "medium_high_critical"


# ---------------------------------------------------------------------------
# Node 3: planner
# ---------------------------------------------------------------------------

def planner(state: IncidentState) -> Dict[str, Any]:
    """
    Use GPT-4o to create a structured investigation plan.

    Design Decision:
        The planner runs ONCE at the start of the investigation so that all
        subsequent nodes (diagnoser, fix_proposer) have a shared mental model
        of what needs to be checked. This prevents the diagnoser from running
        redundant checks.
    """
    incident_id = state.get("incident_id", "unknown")
    anomalies = state.get("detected_anomalies", [])
    severity = state.get("severity", "unknown")

    anomaly_summary = json.dumps(anomalies, indent=2)

    system_prompt = """You are a senior DevOps engineer. Your task is to create a
structured investigation plan for a production incident. Be specific, actionable,
and prioritize steps by impact. Output ONLY a JSON array of strings (investigation steps).
Example output: ["Check CPU-consuming processes with top", "Review application logs for errors"]"""

    user_prompt = f"""Incident Severity: {severity}
Detected Anomalies:
{anomaly_summary}

Create a 4-6 step investigation plan. Each step should be a specific, actionable task.
Return ONLY a JSON array of strings. No explanations outside the JSON."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = _llm.invoke(messages)
        content = response.content.strip()

        # Extract JSON array from response
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group())
        else:
            # Fallback: split by newlines and use as plan
            plan = [line.strip().lstrip("0123456789.-) ") for line in content.split("\n") if line.strip()]
            plan = [p for p in plan if len(p) > 5][:6]

        if not plan:
            plan = [
                f"Identify root cause of {anomalies[0]['type'] if anomalies else 'anomaly'}",
                "Check system resource utilization (CPU, memory, disk)",
                "Review recent deployments and configuration changes",
                "Analyze application and system logs for error patterns",
                "Identify affected services and dependencies",
                "Prepare and validate remediation steps",
            ]
    except Exception as exc:
        plan = [
            f"[Fallback plan due to LLM error: {str(exc)[:50]}]",
            "Check system metrics and resource utilization",
            "Review application logs for errors and exceptions",
            "Identify affected services",
            "Prepare remediation steps",
        ]

    audit_entry = _audit(
        incident_id, "planner",
        action=f"Created {len(plan)}-step investigation plan for {severity} incident",
        result=str(plan[:2]),
    )

    return {
        "investigation_plan": plan,
        "status": "diagnosing",
        "audit_log": _extend_audit(state, audit_entry),
        "messages": list(state.get("messages", [])) + messages + [AIMessage(content=str(plan))],
    }


# ---------------------------------------------------------------------------
# Node 4: diagnoser (ReAct loop)
# ---------------------------------------------------------------------------

def diagnoser(state: IncidentState) -> Dict[str, Any]:
    """
    ReAct loop: observe → think → act → repeat (max MAX_REACT_ITERATIONS).

    Each iteration:
    1. Observe: call fetch_metrics and parse_logs for each affected service
    2. Think: use GPT-4o to reason about the evidence
    3. Act: record reasoning as the running diagnosis

    Design Decision:
        The iteration cap (default 3) is critical. Without it, a confused LLM
        could loop indefinitely. After MAX_REACT_ITERATIONS we write whatever
        diagnosis has been accumulated and move on.
    """
    incident_id = state.get("incident_id", "unknown")
    anomalies = state.get("detected_anomalies", [])
    plan = state.get("investigation_plan", [])
    iteration_count = state.get("iteration_count", 0)
    existing_diagnosis = state.get("diagnosis", "")
    messages = list(state.get("messages", []))

    # Extract unique services from anomalies
    services = list({
        a.get("service", "unknown")
        for a in anomalies
        if a.get("service") and a.get("service") != "unknown"
    })
    if not services:
        services = ["app-server"]

    # --- ReAct iterations ---
    running_thoughts = [existing_diagnosis] if existing_diagnosis else []

    for i in range(MAX_REACT_ITERATIONS):
        iteration_count += 1

        # OBSERVE: Fetch fresh metrics for each service
        metrics_evidence = []
        for svc in services[:3]:  # Cap at 3 services to control token budget
            try:
                metrics = fetch_metrics.invoke({"metric_name": svc})
                metrics_evidence.append(f"Service '{svc}': CPU={metrics['cpu_percent']}%, "
                                        f"Mem={metrics['memory_percent']}%, "
                                        f"Disk={metrics['disk_percent']}%, "
                                        f"ErrorRate={metrics['error_rate']}/s, "
                                        f"Status={metrics['status']}")
            except Exception as exc:
                metrics_evidence.append(f"Service '{svc}': metrics unavailable ({exc})")

        # OBSERVE: Re-parse logs for this iteration
        raw_logs = state.get("raw_logs", "")
        try:
            parsed = parse_logs.invoke({"raw_logs": raw_logs})
            log_evidence = (
                f"Logs: {len(parsed.get('error_lines', []))} errors, "
                f"{len(parsed.get('critical_lines', []))} criticals, "
                f"{parsed.get('http_5xx_count', 0)} HTTP 5xx, "
                f"timespan: {parsed.get('first_event', 'N/A')} to {parsed.get('last_event', 'N/A')}"
            )
        except Exception:
            log_evidence = "Log parsing unavailable."

        # THINK: Ask LLM to reason about the evidence
        evidence_block = "\n".join(metrics_evidence) + "\n" + log_evidence

        think_prompt = f"""You are diagnosing a production incident.

Iteration {i + 1}/{MAX_REACT_ITERATIONS}

Anomalies detected:
{json.dumps(anomalies, indent=2)}

Investigation plan:
{json.dumps(plan, indent=2)}

Current evidence:
{evidence_block}

Previous reasoning:
{chr(10).join(running_thoughts) if running_thoughts else 'None yet'}

Provide your root cause hypothesis for this iteration. Be specific and reference the evidence.
Focus on the most likely cause and what additional evidence would confirm it.
Keep response under 200 words."""

        try:
            think_messages = [
                SystemMessage(content="You are an expert DevOps SRE diagnosing a production incident."),
                HumanMessage(content=think_prompt),
            ]
            response = _llm.invoke(think_messages)
            thought = f"[Iteration {i + 1}] {response.content.strip()}"
            messages.extend(think_messages + [AIMessage(content=response.content)])
        except Exception as exc:
            thought = f"[Iteration {i + 1}] LLM reasoning unavailable: {exc}. Evidence: {evidence_block}"

        running_thoughts.append(thought)

    # ACT: Compile final diagnosis
    diagnosis = "\n\n".join(running_thoughts)

    audit_entry = _audit(
        incident_id, "diagnoser",
        action=f"Completed ReAct diagnosis over {iteration_count} iterations",
        result=diagnosis[:200],
    )

    return {
        "diagnosis": diagnosis,
        "iteration_count": iteration_count,
        "status": "diagnosing",
        "audit_log": _extend_audit(state, audit_entry),
        "messages": messages,
    }


# ---------------------------------------------------------------------------
# Node 5: runbook_searcher
# ---------------------------------------------------------------------------

def runbook_searcher(state: IncidentState) -> Dict[str, Any]:
    """
    Query RunbookMemory with the diagnosis and anomaly types.

    Design Decision:
        Runbook retrieval happens AFTER diagnosis (not before) so that the
        search query is enriched with the root-cause hypothesis, giving more
        relevant results than searching on raw anomaly names alone.
    """
    incident_id = state.get("incident_id", "unknown")
    diagnosis = state.get("diagnosis", "")
    anomalies = state.get("detected_anomalies", [])

    # Build a rich query combining anomaly types and diagnosis summary
    anomaly_types = " ".join(a.get("type", "") for a in anomalies)
    query = f"{anomaly_types} {diagnosis[:300]}"

    try:
        matches = _runbook_memory.search(query, top_k=3)
        runbook_texts = [
            f"[{m['name']} | relevance: {m['score']}]\n{m['excerpt']}"
            for m in matches
        ]
    except Exception as exc:
        runbook_texts = [f"Runbook search failed: {exc}"]

    # Also check incident history for similar past incidents
    try:
        similar = _history_memory.find_similar(query, top_k=2)
        for sim in similar:
            runbook_texts.append(
                f"[Past Incident: {sim['incident_id'][:8]}... | score: {sim['score']}]\n"
                f"Diagnosis: {sim['diagnosis']}\nResolution: {sim['outcome']}"
            )
    except Exception:
        pass  # History search is best-effort

    audit_entry = _audit(
        incident_id, "runbook_searcher",
        action=f"Searched runbooks with query: '{query[:80]}'",
        result=f"Found {len(runbook_texts)} relevant runbooks/past incidents",
    )

    return {
        "runbook_matches": runbook_texts,
        "audit_log": _extend_audit(state, audit_entry),
    }


# ---------------------------------------------------------------------------
# Node 6: fix_proposer
# ---------------------------------------------------------------------------

def fix_proposer(state: IncidentState) -> Dict[str, Any]:
    """
    Use GPT-4o to propose concrete FixSteps grounded in runbook knowledge.

    Design Decision:
        Runbook matches are injected as context (RAG pattern) so the LLM
        proposes commands that are known-good from operational experience,
        rather than hallucinating untested commands.
    """
    incident_id = state.get("incident_id", "unknown")
    diagnosis = state.get("diagnosis", "")
    runbook_matches = state.get("runbook_matches", [])
    anomalies = state.get("detected_anomalies", [])
    severity = state.get("severity", "unknown")

    runbook_context = "\n\n---\n\n".join(runbook_matches[:3]) if runbook_matches else "No runbooks available."

    system_prompt = """You are a senior SRE proposing specific remediation steps for a production incident.
Output ONLY a valid JSON array of fix step objects. Each object must have exactly these keys:
- "step": integer (1-based)
- "command": string (exact shell/kubectl/systemctl command)
- "risk_level": string ("low" | "medium" | "high")
- "description": string (what this does and why)
- "rollback": string (command to undo this step if it fails)

Only propose commands from the whitelisted set:
- systemctl restart/reload/stop/start <service>
- kubectl rollout restart deployment/<name>
- kubectl scale deployment <name> --replicas=<n>
- kubectl delete pod <name>
- docker restart/stop/start <container>
- nginx -s reload
- clear_cache <service>
- free_disk_space <path>
- rotate_logs <service>"""

    user_prompt = f"""Incident Severity: {severity}
Diagnosis: {diagnosis[:500]}

Relevant Runbooks:
{runbook_context[:1500]}

Detected Anomalies:
{json.dumps(anomalies, indent=2)}

Propose 3-5 specific remediation steps. Return ONLY the JSON array."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = _llm.invoke(messages)
        content = response.content.strip()

        # Extract JSON array
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            raw_steps = json.loads(json_match.group())
        else:
            raise ValueError("No JSON array found in LLM response")

        # Validate and normalize each step
        proposed_fixes = []
        for idx, step in enumerate(raw_steps):
            fix = FixStep(
                step=int(step.get("step", idx + 1)),
                command=str(step.get("command", "")),
                risk_level=str(step.get("risk_level", "medium")),
                description=str(step.get("description", "")),
                rollback=str(step.get("rollback", "")),
            ).to_dict()
            proposed_fixes.append(fix)

    except Exception as exc:
        # Fallback: generate conservative default fixes based on anomaly types
        proposed_fixes = _fallback_fixes(anomalies, str(exc))

    audit_entry = _audit(
        incident_id, "fix_proposer",
        action=f"Proposed {len(proposed_fixes)} remediation steps",
        result=str([f"{s['step']}. {s['command'][:40]}" for s in proposed_fixes]),
    )

    return {
        "proposed_fixes": proposed_fixes,
        "status": "awaiting_approval",
        "audit_log": _extend_audit(state, audit_entry),
        "messages": list(state.get("messages", [])) + messages + [AIMessage(content=str(proposed_fixes))],
    }


def _fallback_fixes(anomalies: List[Dict[str, Any]], error: str) -> List[Dict[str, Any]]:
    """Generate safe fallback fixes when LLM call fails."""
    fixes = []
    step = 1
    for anomaly in anomalies:
        atype = anomaly.get("type", "")
        service = anomaly.get("service", "app-service")
        if atype == "cpu_high":
            fixes.append(FixStep(
                step=step, command=f"systemctl restart {service}",
                risk_level="medium", description=f"Restart {service} to clear CPU spike",
                rollback=f"systemctl start {service}",
            ).to_dict())
            step += 1
            fixes.append(FixStep(
                step=step, command=f"kubectl scale deployment {service} --replicas=3",
                risk_level="low", description="Scale horizontally to distribute load",
                rollback=f"kubectl scale deployment {service} --replicas=1",
            ).to_dict())
            step += 1
        elif atype == "disk_full":
            fixes.append(FixStep(
                step=step, command="rotate_logs app-service",
                risk_level="low", description="Rotate application logs to free disk space",
                rollback="",
            ).to_dict())
            step += 1
            fixes.append(FixStep(
                step=step, command="free_disk_space /var/log",
                risk_level="low", description="Remove old log files > 7 days",
                rollback="",
            ).to_dict())
            step += 1
        elif atype in ("error_spike", "critical_log_event"):
            fixes.append(FixStep(
                step=step, command=f"systemctl restart {service}",
                risk_level="medium", description=f"Restart {service} to clear error state",
                rollback=f"systemctl start {service}",
            ).to_dict())
            step += 1
        elif atype == "memory_high":
            fixes.append(FixStep(
                step=step, command=f"clear_cache {service}",
                risk_level="low", description="Drop application caches to free memory",
                rollback="",
            ).to_dict())
            step += 1
            fixes.append(FixStep(
                step=step, command=f"systemctl restart {service}",
                risk_level="medium", description=f"Restart {service} to reclaim leaked memory",
                rollback=f"systemctl start {service}",
            ).to_dict())
            step += 1

    if not fixes:
        fixes.append(FixStep(
            step=1, command="echo 'Manual investigation required'",
            risk_level="low", description=f"Fallback: LLM error ({error[:50]}). Manual intervention needed.",
            rollback="",
        ).to_dict())
    return fixes


# ---------------------------------------------------------------------------
# Node 7: hitl_checkpoint
# ---------------------------------------------------------------------------

def hitl_checkpoint(state: IncidentState) -> Dict[str, Any]:
    """
    HITL (Human-In-The-Loop) checkpoint node.

    Design Decision:
        This node sets status='awaiting_approval' and formats the fix proposal
        for human review. LangGraph's `interrupt_before=["executor"]` mechanism
        pauses the graph HERE so the human can inspect proposed_fixes before
        any command runs. The graph resumes only after approve_incident() injects
        human_approved=True into the state via the checkpointer.

        This prevents automated execution of potentially dangerous commands —
        a critical safety requirement for production DevOps automation.
    """
    incident_id = state.get("incident_id", "unknown")
    proposed_fixes = state.get("proposed_fixes", [])
    severity = state.get("severity", "unknown")
    diagnosis = state.get("diagnosis", "")

    # Format the fix proposal for human review (used by API and UI)
    fix_summary_lines = [
        f"=== INCIDENT {incident_id[:8]}... | Severity: {severity.upper()} ===",
        f"\nDiagnosis: {diagnosis[:200]}",
        "\nProposed Fixes:",
    ]
    for fix in proposed_fixes:
        risk_indicator = {"low": "[LOW RISK]", "medium": "[MEDIUM RISK]", "high": "[HIGH RISK]"}.get(
            fix.get("risk_level", "medium"), "[RISK UNKNOWN]"
        )
        fix_summary_lines.append(
            f"  Step {fix.get('step', '?')}: {risk_indicator} {fix.get('command', '')}\n"
            f"    Description: {fix.get('description', '')}\n"
            f"    Rollback: {fix.get('rollback', 'None')}"
        )
    fix_summary = "\n".join(fix_summary_lines)

    audit_entry = _audit(
        incident_id, "hitl_checkpoint",
        action="Paused for human approval — proposed fix commands presented to operator",
        result=f"{len(proposed_fixes)} fixes awaiting approval for {severity} incident",
    )

    return {
        "status": "awaiting_approval",
        "audit_log": _extend_audit(state, audit_entry),
        # Store formatted summary so UI can display it without re-constructing
        "diagnosis": state.get("diagnosis", "") + f"\n\n[HITL Summary]\n{fix_summary}",
    }


# ---------------------------------------------------------------------------
# Node 8: executor
# ---------------------------------------------------------------------------

def executor(state: IncidentState) -> Dict[str, Any]:
    """
    Execute approved fixes using the execute_fix tool.

    Design Decision:
        The executor checks human_approved AGAIN even though the graph should
        not reach this node without approval. This is a defense-in-depth
        check: if the checkpointer state is somehow corrupted or the graph is
        invoked programmatically, we fail safe by not executing.

        dry_run mode is controlled by the DRY_RUN environment variable:
        - DRY_RUN=true  (default): safe for demos and testing
        - DRY_RUN=false: actual execution (requires whitelisted commands)
    """
    incident_id = state.get("incident_id", "unknown")
    human_approved = state.get("human_approved", False)
    proposed_fixes = state.get("proposed_fixes", [])
    dry_run = DRY_RUN  # Read from environment; can be overridden

    audit_entries = list(state.get("audit_log", []))
    executed_fixes = list(state.get("executed_fixes", []))

    if not human_approved:
        # Safety check: should not reach here without approval
        rejection_entry = _audit(
            incident_id, "executor",
            action="Execution BLOCKED — human_approved is False",
            result="No commands executed. Manual review required.",
        )
        return {
            "executed_fixes": executed_fixes,
            "status": "awaiting_approval",
            "audit_log": audit_entries + [rejection_entry],
        }

    # Execute each approved fix step
    for fix in proposed_fixes:
        command = fix.get("command", "")
        step_num = fix.get("step", "?")

        if not command:
            continue

        try:
            result = execute_fix.invoke({"command": command, "dry_run": dry_run})
            success = result.get("success", False)
            output = result.get("output", "")
            blocked = result.get("blocked", False)
            reason = result.get("reason", "")

            if blocked:
                status_str = f"BLOCKED: {reason}"
            elif success:
                mode = "DRY-RUN" if dry_run else "EXECUTED"
                status_str = f"{mode} OK: {output[:150]}"
            else:
                status_str = f"FAILED: {reason}"

            executed_fixes.append(f"Step {step_num}: {command} → {status_str}")

            exec_audit = _audit(
                incident_id, "executor",
                action=f"Step {step_num}: {'dry-run' if dry_run else 'executed'} '{command}'",
                result=status_str,
            )
            audit_entries.append(exec_audit)

        except Exception as exc:
            error_msg = f"Step {step_num}: {command} → ERROR: {str(exc)}"
            executed_fixes.append(error_msg)
            audit_entries.append(_audit(
                incident_id, "executor",
                action=f"Step {step_num}: execution error for '{command}'",
                result=str(exc)[:200],
            ))

    return {
        "executed_fixes": executed_fixes,
        "status": "executing",
        "audit_log": audit_entries,
    }


# ---------------------------------------------------------------------------
# Node 9: auto_responder
# ---------------------------------------------------------------------------

def auto_responder(state: IncidentState) -> Dict[str, Any]:
    """
    Handle low-severity incidents automatically without human approval.

    Design Decision:
        Only truly low-risk actions (log rotation, cache clearing) are
        auto-executed. Even for 'low' severity, we use dry_run=True unless
        DRY_RUN=false is explicitly set, adding an extra safety layer.
        The auto_responder skips fix_proposer and goes directly to execution
        with pre-defined conservative fixes.
    """
    incident_id = state.get("incident_id", "unknown")
    anomalies = state.get("detected_anomalies", [])

    # Generate conservative auto-fixes for low-severity anomalies
    auto_fixes = _fallback_fixes(anomalies, "auto_responder")

    # Override risk — only execute low-risk fixes automatically
    safe_fixes = [f for f in auto_fixes if f.get("risk_level", "high") == "low"]

    executed = []
    audit_entries = list(state.get("audit_log", []))

    for fix in safe_fixes:
        command = fix.get("command", "")
        if not command:
            continue
        try:
            result = execute_fix.invoke({"command": command, "dry_run": DRY_RUN})
            mode = "DRY-RUN" if DRY_RUN else "AUTO-EXECUTED"
            output = result.get("output", "")
            executed.append(f"{mode}: {command} → {output[:100]}")
            audit_entries.append(_audit(
                incident_id, "auto_responder",
                action=f"Auto-executed low-risk fix: {command}",
                result=output[:150],
            ))
        except Exception as exc:
            executed.append(f"ERROR: {command} → {exc}")

    return {
        "proposed_fixes": auto_fixes,
        "executed_fixes": executed,
        "human_approved": True,  # Auto-approved for low severity
        "status": "executing",
        "audit_log": audit_entries,
        "diagnosis": f"Auto-response for low-severity incident. Anomalies: {[a['type'] for a in anomalies]}",
        "investigation_plan": ["Auto-responder: applied conservative fixes for low-severity anomalies"],
        "runbook_matches": [],
    }


# ---------------------------------------------------------------------------
# Node 10: outcome_logger
# ---------------------------------------------------------------------------

def outcome_logger(state: IncidentState) -> Dict[str, Any]:
    """
    Generate the resolution summary and persist the incident to history.

    Design Decision:
        Saving to IncidentHistoryMemory here (after execution, not at the
        start) ensures we only persist completed incidents with known
        outcomes. This makes the history useful for future retrieval:
        a "pending" incident record would have no resolution to learn from.
    """
    incident_id = state.get("incident_id", "unknown")
    severity = state.get("severity", "unknown")
    anomalies = state.get("detected_anomalies", [])
    executed_fixes = state.get("executed_fixes", [])
    diagnosis = state.get("diagnosis", "")
    human_approved = state.get("human_approved", False)

    # Build resolution summary
    executed_count = len(executed_fixes)
    anomaly_types = ", ".join(a.get("type", "unknown") for a in anomalies)
    approval_status = "human-approved" if human_approved else "auto-responded"

    outcome = (
        f"Incident {incident_id[:8]}... resolved.\n"
        f"Severity: {severity} | Anomalies: {anomaly_types}\n"
        f"Approval: {approval_status}\n"
        f"Fixes applied: {executed_count}\n"
        f"Root cause summary: {diagnosis[:300]}\n"
        f"Executed steps:\n" + "\n".join(f"  - {fix}" for fix in executed_fixes)
    )

    # Persist to incident history for future reference
    final_state = dict(state)
    final_state["outcome"] = outcome
    final_state["status"] = "resolved"

    try:
        saved_path = _history_memory.save_incident(final_state)
        save_note = f"Saved to {saved_path}"
    except Exception as exc:
        save_note = f"History save failed: {exc}"

    audit_entry = _audit(
        incident_id, "outcome_logger",
        action=f"Incident resolved — {executed_count} fix(es) applied. {save_note}",
        result=outcome[:200],
    )

    return {
        "outcome": outcome,
        "status": "resolved",
        "audit_log": _extend_audit(state, audit_entry),
    }
