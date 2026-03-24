from __future__ import annotations

import os
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from enterprise_mcp.config import AppConfig

mcp = FastMCP("enterprise-mcp-server")


@mcp.tool()
def get_service_health() -> dict[str, str]:
    """Return a basic health snapshot for observability checks."""
    config = AppConfig.load()
    return {
        "service": "enterprise-mcp-server",
        "status": "ok",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": config.app_env,
        "transport": os.getenv("MCP_TRANSPORT", "stdio"),
    }


@mcp.tool()
def classify_incident(severity: str, impact: str) -> dict[str, str]:
    """A sample enterprise workflow tool to triage incidents."""
    priority = "P4"
    normalized_severity = severity.lower().strip()
    normalized_impact = impact.lower().strip()

    if normalized_severity in {"critical", "high"} or normalized_impact in {
        "company-wide",
        "production-down",
    }:
        priority = "P1"
    elif normalized_severity == "medium" or normalized_impact in {"multi-team", "customer-facing"}:
        priority = "P2"
    elif normalized_severity == "low":
        priority = "P3"

    return {
        "priority": priority,
        "severity": normalized_severity,
        "impact": normalized_impact,
        "owner_team": "platform-operations",
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
