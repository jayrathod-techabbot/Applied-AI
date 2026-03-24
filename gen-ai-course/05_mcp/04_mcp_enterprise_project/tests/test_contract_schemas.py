from __future__ import annotations

import asyncio

from enterprise_mcp.server import mcp


def test_mcp_tool_contract_schemas() -> None:
    tools = asyncio.run(mcp.list_tools())
    by_name = {tool.name: tool.model_dump() for tool in tools}

    assert "get_service_health" in by_name
    assert by_name["get_service_health"]["inputSchema"]["type"] == "object"
    assert by_name["get_service_health"]["inputSchema"]["properties"] == {}

    assert "classify_incident" in by_name
    classify_schema = by_name["classify_incident"]["inputSchema"]
    assert classify_schema["type"] == "object"
    assert sorted(classify_schema["required"]) == ["impact", "severity"]
    assert classify_schema["properties"]["severity"]["type"] == "string"
    assert classify_schema["properties"]["impact"]["type"] == "string"
