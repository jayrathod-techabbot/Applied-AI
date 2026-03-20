"""
agent/tools.py

LangChain @tool-decorated functions used by LangGraph nodes in the
AI DevOps Incident Responder.

Design Decisions:
- All tools are pure functions annotated with @tool so they can be bound to
  an LLM via .bind_tools() or called directly by node logic.
- `execute_fix` defaults to dry_run=True so that the system cannot cause
  unintended changes unless the human explicitly approves (HITL pattern).
- `fetch_metrics` uses seeded random values for reproducibility in tests;
  in production this would call Prometheus/Datadog APIs.
- `search_runbook` uses TF-IDF instead of FAISS to keep the dependency
  surface small; the docstring explains how to swap to FAISS.
"""

from __future__ import annotations

import json
import os
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# 1. parse_logs
# ---------------------------------------------------------------------------

@tool
def parse_logs(raw_logs: str) -> Dict[str, Any]:
    """
    Parse raw log text and extract structured information.

    Uses regex patterns to identify ERROR/WARN/CRITICAL lines, extract
    timestamps, service names, HTTP error codes, and compute frequency
    counts.  This gives downstream nodes a structured view of the log
    without requiring an LLM call (cheap & fast).

    Args:
        raw_logs: Multi-line log text as a single string.

    Returns:
        Dict with keys:
          - total_lines        (int)
          - error_lines        (List[str])
          - warn_lines         (List[str])
          - critical_lines     (List[str])
          - timestamps         (List[str])
          - services           (List[str])  unique service/host names
          - error_codes        (List[str])  HTTP/system error codes
          - frequency          (Dict)       level → count
          - http_5xx_count     (int)
          - first_event        (str)        earliest timestamp found
          - last_event         (str)        latest timestamp found
    """
    lines = raw_logs.strip().splitlines()
    total_lines = len(lines)

    # Regex patterns
    ts_pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)"
    )
    level_pattern = re.compile(r"\b(ERROR|WARN(?:ING)?|CRITICAL|INFO|DEBUG|FATAL)\b", re.IGNORECASE)
    service_pattern = re.compile(
        r"(?:service[:\s]+|host[:\s]+|server[:\s]+|node[:\s]+)?([a-z][a-z0-9_-]*(?:-\d+)?)\s+"
        r"(?:ERROR|WARN|CRITICAL|INFO|DEBUG|FATAL)\b",
        re.IGNORECASE,
    )
    # Match service/host tokens that look like hostnames (e.g. app-server-01, nginx, payment-service)
    hostname_pattern = re.compile(r"\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b", re.IGNORECASE)
    http_code_pattern = re.compile(r"\bHTTP[/ ]?([45]\d{2})\b|(?:^|\s)([45]\d{2})\s+(?:error|status)", re.IGNORECASE)
    error_code_pattern = re.compile(r"\b(E\d{4,}|ERR[-_]\d+|SIGKILL|SIGTERM|OOMKill(?:ed)?|ENOSPC|ENOMEM)\b", re.IGNORECASE)

    error_lines: List[str] = []
    warn_lines: List[str] = []
    critical_lines: List[str] = []
    timestamps: List[str] = []
    services: set = set()
    error_codes: List[str] = []
    frequency: Dict[str, int] = defaultdict(int)
    http_5xx_count = 0

    for line in lines:
        # Timestamps
        ts_match = ts_pattern.search(line)
        if ts_match:
            timestamps.append(ts_match.group(1))

        # Log levels
        level_match = level_pattern.search(line)
        if level_match:
            level = level_match.group(1).upper()
            frequency[level] += 1
            if level in ("ERROR", "FATAL"):
                error_lines.append(line)
            elif level in ("WARN", "WARNING"):
                warn_lines.append(line)
            elif level == "CRITICAL":
                critical_lines.append(line)
                error_lines.append(line)  # critical also counted as errors

        # HTTP 5xx
        http_match = http_code_pattern.search(line)
        if http_match:
            code_str = http_match.group(1) or http_match.group(2)
            if code_str and code_str.startswith("5"):
                http_5xx_count += 1
                error_codes.append(f"HTTP-{code_str}")

        # System error codes
        sys_codes = error_code_pattern.findall(line)
        error_codes.extend(sys_codes)

        # Service/host names — simple heuristic: hostname-like tokens near log levels
        svc_match = service_pattern.search(line)
        if svc_match:
            services.add(svc_match.group(1).lower())
        else:
            # Fallback: pick hyphenated tokens that look like service names
            for m in hostname_pattern.finditer(line):
                token = m.group(1).lower()
                # Filter out common words
                if token not in {"service", "error", "warn", "critical", "info", "debug"}:
                    services.add(token)

    # Deduplicate error codes
    seen_codes: set = set()
    unique_codes: List[str] = []
    for c in error_codes:
        if c not in seen_codes:
            seen_codes.add(c)
            unique_codes.append(c)

    first_event = timestamps[0] if timestamps else ""
    last_event = timestamps[-1] if timestamps else ""

    return {
        "total_lines": total_lines,
        "error_lines": error_lines,
        "warn_lines": warn_lines,
        "critical_lines": critical_lines,
        "timestamps": timestamps,
        "services": sorted(services),
        "error_codes": unique_codes,
        "frequency": dict(frequency),
        "http_5xx_count": http_5xx_count,
        "first_event": first_event,
        "last_event": last_event,
    }


# ---------------------------------------------------------------------------
# 2. fetch_metrics
# ---------------------------------------------------------------------------

# Realistic baseline ranges per metric (min, max)
_METRIC_RANGES: Dict[str, tuple] = {
    "cpu_percent":     (10.0, 99.9),
    "memory_percent":  (20.0, 98.0),
    "disk_percent":    (30.0, 99.5),
    "error_rate":      (0.0, 25.0),     # errors per second
    "response_time_ms": (50.0, 5000.0),
    "network_in_mbps": (1.0, 1000.0),
    "network_out_mbps": (1.0, 500.0),
    "active_connections": (0.0, 10000.0),
}

# Services that are "known sick" in our simulation so tests are deterministic
_SICK_SERVICES = {"app-server-01", "payment-service", "app-server"}


@tool
def fetch_metrics(metric_name: str) -> Dict[str, Any]:
    """
    Fetch current system/service metrics (simulated).

    In production this tool would call Prometheus, Datadog, or CloudWatch.
    For simulation, it returns seeded random values within realistic ranges.
    Services in _SICK_SERVICES return elevated values to match sample logs.

    Args:
        metric_name: Service name to fetch metrics for (e.g. 'app-server-01').

    Returns:
        Dict with keys: service, cpu_percent, memory_percent, disk_percent,
        error_rate, response_time_ms, network_in_mbps, network_out_mbps,
        active_connections, status ('healthy'|'degraded'|'critical'), timestamp.
    """
    # Use a deterministic seed based on the service name so repeated calls
    # return stable values within a test run — important for diagnoser ReAct loop
    rng = random.Random(hash(metric_name) % (2**31))

    is_sick = metric_name.lower() in _SICK_SERVICES

    def jitter(base_min: float, base_max: float, sick_floor: float = None) -> float:
        """Return a value in range; skew high if service is 'sick'."""
        if is_sick and sick_floor is not None:
            # Sick services return values above the sick_floor
            return round(rng.uniform(sick_floor, base_max), 2)
        return round(rng.uniform(base_min, base_max), 2)

    cpu = jitter(10.0, 99.9, sick_floor=88.0)
    memory = jitter(20.0, 98.0, sick_floor=80.0)
    disk = jitter(30.0, 99.5, sick_floor=91.0)
    error_rate = jitter(0.0, 25.0, sick_floor=5.5) if is_sick else jitter(0.0, 2.0)
    response_time = jitter(50.0, 5000.0, sick_floor=2000.0) if is_sick else jitter(50.0, 500.0)
    net_in = round(rng.uniform(1.0, 1000.0), 2)
    net_out = round(rng.uniform(1.0, 500.0), 2)
    connections = int(rng.uniform(0, 10000))

    # Determine status
    if cpu > 90 or memory > 85 or disk > 95 or error_rate > 5:
        status = "critical"
    elif cpu > 75 or memory > 70 or disk > 80 or error_rate > 2:
        status = "degraded"
    else:
        status = "healthy"

    from datetime import datetime
    return {
        "service": metric_name,
        "cpu_percent": cpu,
        "memory_percent": memory,
        "disk_percent": disk,
        "error_rate": error_rate,
        "response_time_ms": response_time,
        "network_in_mbps": net_in,
        "network_out_mbps": net_out,
        "active_connections": connections,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# 3. search_runbook
# ---------------------------------------------------------------------------

@tool
def search_runbook(query: str, runbook_dir: str = "./data/runbooks") -> List[str]:
    """
    Search markdown runbooks using TF-IDF keyword matching.

    Design Decision:
        TF-IDF is used here for zero-infrastructure simplicity.  To replace
        with FAISS vector search:
          1. pip install faiss-cpu sentence-transformers
          2. Embed each runbook chunk with SentenceTransformer
          3. Store in a faiss.IndexFlatL2 index
          4. Query with the embedded query vector
        The interface (query in, List[str] out) stays identical.

    Args:
        query:       Natural language description of the incident or symptom.
        runbook_dir: Path to directory containing *.md runbook files.

    Returns:
        List of up to 3 runbook text excerpts most relevant to the query,
        prefixed with the source filename.
    """
    runbook_path = Path(runbook_dir)
    if not runbook_path.exists():
        # Try relative to the project root (common when running from different cwd)
        alt = Path(__file__).parent.parent / "data" / "runbooks"
        if alt.exists():
            runbook_path = alt

    md_files = list(runbook_path.glob("*.md"))
    if not md_files:
        return ["No runbooks found in directory: " + str(runbook_path)]

    # Read all runbooks
    docs: List[Dict[str, str]] = []
    for f in md_files:
        try:
            text = f.read_text(encoding="utf-8")
            docs.append({"name": f.name, "text": text})
        except Exception as exc:
            docs.append({"name": f.name, "text": f"[Error reading file: {exc}]"})

    # --- Simple TF-IDF scoring ---
    def tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    query_tokens = set(tokenize(query))

    # IDF: log(N / df) where df = number of docs containing term
    from math import log

    n = len(docs)
    df: Dict[str, int] = defaultdict(int)
    doc_tokens_list = []
    for doc in docs:
        toks = tokenize(doc["text"])
        tok_set = set(toks)
        doc_tokens_list.append(toks)
        for t in tok_set:
            df[t] += 1

    def score(doc_tokens: List[str]) -> float:
        tok_count = len(doc_tokens)
        if tok_count == 0:
            return 0.0
        freq: Dict[str, int] = defaultdict(int)
        for t in doc_tokens:
            freq[t] += 1
        total = 0.0
        for qt in query_tokens:
            tf = freq.get(qt, 0) / tok_count
            idf = log((n + 1) / (df.get(qt, 0) + 1)) + 1
            total += tf * idf
        return total

    scored = [
        (score(doc_tokens_list[i]), docs[i])
        for i in range(len(docs))
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    results: List[str] = []
    for sc, doc in scored[:3]:
        # Return first 800 chars of the runbook as the excerpt
        excerpt = doc["text"][:800].strip()
        results.append(f"[Runbook: {doc['name']} | Score: {sc:.4f}]\n{excerpt}")

    return results if results else ["No relevant runbooks found."]


# ---------------------------------------------------------------------------
# 4. execute_fix
# ---------------------------------------------------------------------------

# Whitelist of command prefixes that are considered safe for automated execution.
# Design Decision: Explicit whitelist prevents arbitrary code execution even if
# the LLM proposes a malicious command injected via log data (prompt injection
# defense). Every new command type requires a deliberate code change + review.
SAFE_COMMAND_PREFIXES = [
    "systemctl restart",
    "systemctl reload",
    "systemctl stop",
    "systemctl start",
    "kubectl rollout restart",
    "kubectl scale deployment",
    "kubectl delete pod",
    "service restart",
    "service reload",
    "nginx -s reload",
    "docker restart",
    "docker stop",
    "docker start",
    "clear_cache",          # internal pseudo-command
    "free_disk_space",      # internal pseudo-command
    "rotate_logs",          # internal pseudo-command
    "echo",                 # safe no-op for testing
    "ls",                   # safe read-only
]


@tool
def execute_fix(command: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Execute a remediation command in a sandboxed, whitelisted manner.

    Design Decision:
        `dry_run=True` by default is a critical safety guard: the graph
        only passes dry_run=False after explicit human approval at the
        HITL checkpoint. This ensures no automated command ever runs
        without human oversight in production.

    Args:
        command: Shell or pseudo-command to execute.
        dry_run: If True (default), log the command but do not execute.

    Returns:
        Dict with keys: success (bool), output (str), command (str),
        dry_run (bool), blocked (bool), reason (str if blocked).
    """
    from datetime import datetime

    command_stripped = command.strip()

    # --- Whitelist check ---
    is_allowed = any(
        command_stripped.lower().startswith(prefix.lower())
        for prefix in SAFE_COMMAND_PREFIXES
    )

    if not is_allowed:
        return {
            "success": False,
            "output": "",
            "command": command_stripped,
            "dry_run": dry_run,
            "blocked": True,
            "reason": (
                f"Command '{command_stripped[:60]}' is not in the safe-command whitelist. "
                "Add it explicitly to SAFE_COMMAND_PREFIXES after security review."
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    if dry_run:
        # Dry-run: simulate success without executing
        return {
            "success": True,
            "output": f"[DRY RUN] Would execute: {command_stripped}",
            "command": command_stripped,
            "dry_run": True,
            "blocked": False,
            "reason": "",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # --- Actual execution (production mode) ---
    # We use subprocess with a strict timeout and no shell=True to prevent
    # injection. Only whitelisted commands reach here.
    import subprocess
    import shlex

    try:
        # Handle pseudo-commands that don't map to real shell commands
        pseudo_commands = {"clear_cache", "free_disk_space", "rotate_logs"}
        if any(command_stripped.lower().startswith(pc) for pc in pseudo_commands):
            # Simulate execution of internal operations
            output = f"[PSEUDO-CMD] Executed: {command_stripped} — OK"
            return {
                "success": True,
                "output": output,
                "command": command_stripped,
                "dry_run": False,
                "blocked": False,
                "reason": "",
                "timestamp": datetime.utcnow().isoformat(),
            }

        args = shlex.split(command_stripped)
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,  # Never use shell=True — prevents injection
        )
        output = result.stdout or result.stderr or "(no output)"
        return {
            "success": result.returncode == 0,
            "output": output[:2000],  # Truncate large outputs
            "command": command_stripped,
            "dry_run": False,
            "blocked": False,
            "reason": "" if result.returncode == 0 else f"Exit code: {result.returncode}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "command": command_stripped,
            "dry_run": False,
            "blocked": False,
            "reason": "Command timed out after 30 seconds.",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        return {
            "success": False,
            "output": "",
            "command": command_stripped,
            "dry_run": False,
            "blocked": False,
            "reason": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# 5. get_system_status
# ---------------------------------------------------------------------------

@tool
def get_system_status(service: str) -> Dict[str, Any]:
    """
    Return the simulated health status of a service.

    In production this would query a service mesh (Istio), health-check
    endpoints, or a monitoring platform.  Here we return deterministic
    simulated data based on the service name.

    Args:
        service: Service name to check (e.g. 'nginx', 'payment-service').

    Returns:
        Dict with keys: service, status, uptime_hours, last_restart,
        health_checks (List[Dict]), replicas_running, replicas_desired,
        version, environment.
    """
    from datetime import datetime, timedelta

    rng = random.Random(hash(service) % (2**31))
    is_sick = service.lower() in _SICK_SERVICES

    # Health check results
    checks = [
        {"name": "liveness",  "passing": not is_sick or rng.random() > 0.3},
        {"name": "readiness", "passing": not is_sick or rng.random() > 0.5},
        {"name": "startup",   "passing": True},
    ]

    replicas_desired = rng.choice([1, 2, 3, 5])
    replicas_running = replicas_desired if not is_sick else max(1, replicas_desired - rng.randint(1, 2))

    uptime = rng.uniform(0.5, 720.0) if not is_sick else rng.uniform(0.1, 48.0)
    last_restart_dt = datetime.utcnow() - timedelta(hours=uptime)

    all_passing = all(c["passing"] for c in checks)
    status = "healthy" if all_passing and replicas_running == replicas_desired else (
        "critical" if is_sick else "degraded"
    )

    return {
        "service": service,
        "status": status,
        "uptime_hours": round(uptime, 2),
        "last_restart": last_restart_dt.isoformat(),
        "health_checks": checks,
        "replicas_running": replicas_running,
        "replicas_desired": replicas_desired,
        "version": f"v{rng.randint(1,5)}.{rng.randint(0,12)}.{rng.randint(0,20)}",
        "environment": "production",
        "timestamp": datetime.utcnow().isoformat(),
    }
