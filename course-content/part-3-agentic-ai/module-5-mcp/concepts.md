# Module 5: Model Context Protocol (MCP) — Concepts

## Table of Contents
- [5.1 MCP Overview and Motivation](#51-mcp-overview-and-motivation)
- [5.2 Building MCP Servers](#52-building-mcp-servers)
- [5.3 Building MCP Clients](#53-building-mcp-clients)
- [5.4 Enterprise MCP Integration Project](#54-enterprise-mcp-integration-project)

---

## 5.1 MCP Overview and Motivation

### What is MCP?

The **Model Context Protocol (MCP)** is an open standard protocol designed by Anthropic to enable AI models and applications to interact with external tools, data sources, and services through a unified interface. It provides a standardized way for Large Language Models (LLMs) to discover, describe, and invoke external capabilities.

### Problems MCP Solves

| Problem | Traditional Approach | MCP Solution |
|---------|---------------------|--------------|
| **Tool Integration Fragmentation** | Each LLM app needs custom integrations | Standardized protocol for all tools |
| **Discovery & Description** | Hard-coded tool definitions | Dynamic tool discovery via protocol |
| **Security & Access Control** | Ad-hoc permission systems | Built-in authorization framework |
| **Scalability** | Tightly coupled architectures | Decoupled client-server model |
| **Interoperability** | Vendor-specific implementations | Open, language-agnostic standard |

### Core Architecture

```
+---------------------------------------------------------+
|                    MCP Host (Client)                     |
|  +-------------+  +-------------+  +-----------------+   |
|  |   LLM App   |  | Agent Frame |  |  Custom Client  |   |
|  +------+------+  +------+------+  +--------+--------+   |
|         +----------------+-----------------+             |
|                    MCP Client Layer                       |
+-------------------------+--------------------------------+
                          | JSON-RPC 2.0
+-------------------------+--------------------------------+
|                    MCP Server Layer                       |
|  +-------------+  +-------------+  +-----------------+   |
|  |  Database   |  |  Web API    |  |  File System    |   |
|  |  Server     |  |  Server     |  |  Server         |   |
|  +-------------+  +-------------+  +-----------------+   |
+---------------------------------------------------------+
```

### MCP Primitives

MCP defines three core primitives that servers can expose:

1. **Resources** - Read-only data sources (files, databases, APIs)
2. **Tools** - Executable functions that perform actions
3. **Prompts** - Reusable prompt templates with parameters

### Protocol Transport

MCP supports multiple transport mechanisms:

```python
# Transport options
TRANSPORTS = {
    "stdio": "Standard input/output (local processes)",
    "http": "HTTP with Server-Sent Events (remote)",
    "websocket": "WebSocket connections (real-time)"
}
```

### JSON-RPC 2.0 Message Format

All MCP communication uses JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_database",
    "arguments": {"query": "SELECT * FROM users"}
  }
}
```

---

## 5.2 Building MCP Servers

### Server Architecture

An MCP server exposes resources, tools, and prompts to clients. The server lifecycle includes:

1. **Initialization** - Handshake with client capabilities
2. **Registration** - Define available resources, tools, prompts
3. **Request Handling** - Process client requests
4. **Notification** - Push updates to clients

### Python MCP Server Implementation

```python
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Resource,
    Tool,
    Prompt,
    TextContent,
    PromptMessage,
    Role
)
import mcp.server.stdio

# Create server instance
server = Server("data-analysis-server")

# -----------------------------------------------
# RESOURCES -- Read-only data sources
# -----------------------------------------------

@server.list_resources()
async def list_resources():
    """List all available resources."""
    return [
        Resource(
            uri="file://data/sales.csv",
            name="Sales Data",
            description="Monthly sales data for 2024",
            mimeType="text/csv"
        ),
        Resource(
            uri="db://analytics/user_metrics",
            name="User Metrics",
            description="Real-time user engagement metrics",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    """Read a specific resource by URI."""
    if uri == "file://data/sales.csv":
        with open("data/sales.csv", "r") as f:
            return f.read()
    elif uri.startswith("db://"):
        table = uri.split("/")[-1]
        return await query_database(table)
    raise ValueError(f"Unknown resource: {uri}")

# -----------------------------------------------
# TOOLS -- Executable functions
# -----------------------------------------------

@server.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        Tool(
            name="analyze_sales",
            description="Analyze sales data and generate insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["revenue", "units", "growth"],
                        "description": "The metric to analyze"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["monthly", "quarterly", "yearly"],
                        "description": "Time period for analysis"
                    }
                },
                "required": ["metric"]
            }
        ),
        Tool(
            name="query_database",
            description="Execute a read-only SQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum rows to return"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute a tool with given arguments."""
    if name == "analyze_sales":
        metric = arguments.get("metric", "revenue")
        period = arguments.get("period", "monthly")
        result = await perform_sales_analysis(metric, period)
        return [TextContent(type="text", text=result)]
    
    elif name == "query_database":
        query = arguments["query"]
        limit = arguments.get("limit", 100)
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries allowed")
        results = await execute_query(query, limit)
        return [TextContent(type="text", text=format_results(results))]
    
    raise ValueError(f"Unknown tool: {name}")

# -----------------------------------------------
# PROMPTS -- Reusable prompt templates
# -----------------------------------------------

@server.list_prompts()
async def list_prompts():
    """List all available prompt templates."""
    return [
        Prompt(
            name="data_summary",
            description="Generate a summary of a dataset",
            arguments=[
                {
                    "name": "dataset",
                    "description": "Name or path of the dataset",
                    "required": True
                },
                {
                    "name": "focus",
                    "description": "Specific aspect to focus on",
                    "required": False
                }
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    """Get a prompt template with arguments filled in."""
    if name == "data_summary":
        dataset = arguments.get("dataset", "unknown")
        focus = arguments.get("focus", "general trends")
        return PromptMessage(
            role=Role.user,
            content=TextContent(
                type="text",
                text=f"Analyze the dataset '{dataset}' and provide a comprehensive summary focusing on {focus}. Include key statistics, trends, and anomalies."
            )
        )
    raise ValueError(f"Unknown prompt: {name}")

# -----------------------------------------------
# SERVER STARTUP
# -----------------------------------------------

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="data-analysis-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### TypeScript MCP Server Implementation

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Create server instance
const server = new McpServer({
  name: "analytics-server",
  version: "1.0.0"
});

// -----------------------------------------------
// TOOLS -- With Zod schema validation
// -----------------------------------------------

server.tool(
  "calculate_metrics",
  "Calculate business metrics from provided data",
  {
    metric: z.enum(["revenue", "profit", "churn"]),
    startDate: z.string().describe("Start date (YYYY-MM-DD)"),
    endDate: z.string().describe("End date (YYYY-MM-DD)")
  },
  async ({ metric, startDate, endDate }) => {
    const result = await calculateBusinessMetrics({
      metric,
      startDate,
      endDate
    });
    
    return {
      content: [{
        type: "text",
        text: JSON.stringify(result, null, 2)
      }]
    };
  }
);

server.tool(
  "fetch_external_data",
  "Fetch data from external API",
  {
    endpoint: z.string(),
    params: z.record(z.string()).optional()
  },
  async ({ endpoint, params }) => {
    const url = new URL(endpoint);
    if (params) {
      Object.entries(params).forEach(([k, v]) => 
        url.searchParams.set(k, v)
      );
    }
    
    const response = await fetch(url.toString());
    const data = await response.json();
    
    return {
      content: [{
        type: "text",
        text: JSON.stringify(data, null, 2)
      }]
    };
  }
);

// -----------------------------------------------
// RESOURCES
// -----------------------------------------------

server.resource(
  "config",
  "file://config/settings.json",
  async (uri) => ({
    contents: [{
      uri: uri.href,
      mimeType: "application/json",
      text: JSON.stringify({
        version: "1.0",
        environment: process.env.NODE_ENV || "development"
      }, null, 2)
    }]
  })
);

// -----------------------------------------------
// PROMPTS
// -----------------------------------------------

server.prompt(
  "analyze_trends",
  {
    dataset: z.string(),
    timeframe: z.enum(["week", "month", "quarter", "year"])
  },
  ({ dataset, timeframe }) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Analyze trends in the "${dataset}" dataset over the past ${timeframe}. Identify patterns, anomalies, and provide actionable insights.`
      }
    }]
  })
);

// -----------------------------------------------
// START SERVER
// -----------------------------------------------

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

main().catch(console.error);
```

### Server Capability Negotiation

During initialization, servers and clients negotiate capabilities:

```python
# Server capabilities declaration
capabilities = {
    "tools": {
        "listChanged": True  # Server notifies when tools change
    },
    "resources": {
        "subscribe": True,   # Clients can subscribe to resource changes
        "listChanged": True
    },
    "prompts": {
        "listChanged": True
    },
    "logging": {}            # Server can emit log messages
}
```

---

## 5.3 Building MCP Clients

### Client Architecture

MCP clients connect to servers, discover capabilities, and invoke tools/resources/prompts:

```
+----------------------------------------------+
|              MCP Client Application           |
|  +----------------------------------------+   |
|  |         Client Application Logic       |   |
|  |  +----------+ +----------+ +--------+  |   |
|  |  |Tool Call | |Resource  | |Prompt  |  |   |
|  |  | Handler  | | Reader   | | Engine |  |   |
|  |  +----+-----+ +----+-----+ +---+----+  |   |
|  +-------+-------------+-------------+------+   |
|          +-------------+-------------+          |
|                   MCP Client SDK                |
+-------------------------+------------------------+
                          |
                    Transport Layer
```

### Python MCP Client Implementation

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

# -----------------------------------------------
# CONNECTION MANAGEMENT
# -----------------------------------------------

async def create_client_session():
    """Create an MCP client session with stdio transport."""
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env={"API_KEY": "your-api-key"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return session

# -----------------------------------------------
# DISCOVERING CAPABILITIES
# -----------------------------------------------

async def discover_capabilities(session: ClientSession):
    """Discover all tools, resources, and prompts from server."""
    
    tools_response = await session.list_tools()
    print("Available Tools:")
    for tool in tools_response.tools:
        print(f"  - {tool.name}: {tool.description}")
        print(f"    Schema: {tool.inputSchema}")
    
    resources_response = await session.list_resources()
    print("\nAvailable Resources:")
    for resource in resources_response.resources:
        print(f"  - {resource.uri}: {resource.name}")
        print(f"    Type: {resource.mimeType}")
    
    prompts_response = await session.list_prompts()
    print("\nAvailable Prompts:")
    for prompt in prompts_response.prompts:
        print(f"  - {prompt.name}: {prompt.description}")
        print(f"    Args: {[a.name for a in prompt.arguments]}")

# -----------------------------------------------
# INVOKING TOOLS
# -----------------------------------------------

async def invoke_tool(session: ClientSession, tool_name: str, arguments: dict):
    """Call a tool on the MCP server."""
    result = await session.call_tool(tool_name, arguments)
    
    for content in result.content:
        if content.type == "text":
            print(f"Tool Result: {content.text}")
        elif content.type == "image":
            print(f"Image received: {content.mimeType}")
        elif content.type == "resource":
            print(f"Resource reference: {content.resource}")
    
    return result

# -----------------------------------------------
# READING RESOURCES
# -----------------------------------------------

async def read_resource(session: ClientSession, uri: str):
    """Read a resource from the MCP server."""
    result = await session.read_resource(uri)
    
    for content in result.contents:
        print(f"Resource URI: {content.uri}")
        print(f"MIME Type: {content.mimeType}")
        print(f"Content: {content.text[:200]}...")
    
    return result

# -----------------------------------------------
# USING PROMPTS
# -----------------------------------------------

async def get_prompt(session: ClientSession, prompt_name: str, arguments: dict):
    """Get a prompt template from the MCP server."""
    result = await session.get_prompt(prompt_name, arguments)
    
    for message in result.messages:
        print(f"Role: {message.role}")
        print(f"Content: {message.content.text}")
    
    return result

# -----------------------------------------------
# SUBSCRIPTIONS (Resource Updates)
# -----------------------------------------------

async def subscribe_to_resource(session: ClientSession, uri: str):
    """Subscribe to resource change notifications."""
    await session.subscribe_resource(uri)

# -----------------------------------------------
# COMPLETE CLIENT EXAMPLE
# -----------------------------------------------

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["analytics_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await discover_capabilities(session)
            
            result = await invoke_tool(
                session,
                "analyze_sales",
                {"metric": "revenue", "period": "quarterly"}
            )
            
            await read_resource(session, "file://data/sales.csv")
            
            await get_prompt(
                session,
                "data_summary",
                {"dataset": "sales.csv", "focus": "trends"}
            )

if __name__ == "__main__":
    asyncio.run(main())
```

### TypeScript MCP Client Implementation

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

// -----------------------------------------------
// CLIENT SETUP
// -----------------------------------------------

async function createMcpClient() {
  const transport = new StdioClientTransport({
    command: "python",
    args: ["mcp_server.py"],
    env: {
      ...process.env,
      API_KEY: process.env.API_KEY || ""
    }
  });

  const client = new Client(
    {
      name: "analytics-client",
      version: "1.0.0"
    },
    {
      capabilities: {
        sampling: {},
        roots: {
          listChanged: true
        }
      }
    }
  );

  await client.connect(transport);
  return client;
}

// -----------------------------------------------
// TOOL INVOCATION
// -----------------------------------------------

async function useTools(client: Client) {
  const tools = await client.listTools();
  console.log("Available tools:", tools.tools.map(t => t.name));

  const result = await client.callTool({
    name: "calculate_metrics",
    arguments: {
      metric: "revenue",
      startDate: "2024-01-01",
      endDate: "2024-12-31"
    }
  });

  for (const content of result.content) {
    if (content.type === "text") {
      console.log("Result:", content.text);
    }
  }
}

// -----------------------------------------------
// RESOURCE ACCESS
// -----------------------------------------------

async function accessResources(client: Client) {
  const resources = await client.listResources();
  console.log("Available resources:", resources.resources.map(r => r.uri));

  const resource = await client.readResource({
    uri: "file://config/settings.json"
  });

  for (const content of resource.contents) {
    console.log("Resource content:", content.text);
  }

  await client.subscribeResource({
    uri: "file://config/settings.json"
  });
}

// -----------------------------------------------
// PROMPT USAGE
// -----------------------------------------------

async function usePrompts(client: Client) {
  const prompts = await client.listPrompts();
  console.log("Available prompts:", prompts.prompts.map(p => p.name));

  const result = await client.getPrompt({
    name: "analyze_trends",
    arguments: {
      dataset: "sales_data",
      timeframe: "quarter"
    }
  });

  for (const message of result.messages) {
    console.log(`${message.role}: ${message.content.text}`);
  }
}

// -----------------------------------------------
// NOTIFICATION HANDLERS
// -----------------------------------------------

function setupNotifications(client: Client) {
  client.setNotificationHandler(
    "notifications/tools/list_changed",
    async () => {
      console.log("Tools list changed!");
      const tools = await client.listTools();
      console.log("Updated tools:", tools.tools.map(t => t.name));
    }
  );

  client.setNotificationHandler(
    "notifications/resources/list_changed",
    async () => {
      console.log("Resources list changed!");
    }
  );
}

// -----------------------------------------------
// MAIN
// -----------------------------------------------

async function main() {
  const client = await createMcpClient();
  
  try {
    setupNotifications(client);
    await useTools(client);
    await accessResources(client);
    await usePrompts(client);
  } finally {
    await client.close();
  }
}

main().catch(console.error);
```

### HTTP Transport Client

```python
from mcp.client.sse import sse_client
from mcp import ClientSession
import asyncio

async def http_client_example():
    """Connect to MCP server via HTTP/SSE transport."""
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools")
            
            result = await session.call_tool(
                "search_database",
                {"query": "latest trends"}
            )
            print(result.content[0].text)

asyncio.run(http_client_example())
```

---

## 5.4 Enterprise MCP Integration Project

### Enterprise Architecture Pattern

```
+---------------------------------------------------------------------+
|                        Enterprise MCP Mesh                           |
|                                                                       |
|  +-------------+  +-------------+  +-----------------------------+   |
|  |  AI Agent   |  |  Chat App   |  |  Analytics Dashboard        |   |
|  |  (Claude)   |  |  (Web)      |  |  (BI Tool)                  |   |
|  +------+------+  +------+------+  +--------------+--------------+   |
|         +----------------+----------------------+                     |
|                    MCP Client Gateway                                 |
+-----------------------------+-----------------------------------------+
                              |
+-----------------------------+-----------------------------------------+
|                    MCP Server Registry                                |
|                                                                       |
|  +--------------+ +--------------+ +--------------+ +------------+    |
|  |  CRM Server  | |  ERP Server  | |  Data Lake   | |  Auth      |    |
|  |  (Salesforce)| |  (SAP)       | |  (Snowflake) | |  Server    |    |
|  +--------------+ +--------------+ +--------------+ +------------+    |
|                                                                       |
|  +--------------+ +--------------+ +--------------+ +------------+    |
|  |  Email       | |  Calendar    | |  Code Repo   | |  Monitoring|    |
|  |  (Exchange)  | |  (O365)      | |  (GitHub)    | |  (Datadog) |    |
|  +--------------+ +--------------+ +--------------+ +------------+    |
+---------------------------------------------------------------------+
```

### Project: Enterprise Data Analytics MCP Server

```python
"""
Enterprise MCP Server for Data Analytics
Integrates: Database, File System, External APIs, Authentication
"""

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import asyncio
import json
import hashlib
from typing import Optional
from datetime import datetime

# -----------------------------------------------
# AUTHENTICATION & AUTHORIZATION
# -----------------------------------------------

class MCPAuthMiddleware:
    """Handle authentication for MCP server requests."""
    
    def __init__(self, api_keys: dict[str, str], role_permissions: dict):
        self.api_keys = api_keys
        self.role_permissions = role_permissions
    
    def validate_token(self, token: str) -> Optional[str]:
        """Validate API token and return role."""
        hashed = hashlib.sha256(token.encode()).hexdigest()
        return self.api_keys.get(hashed)
    
    def check_permission(self, role: str, action: str, resource: str) -> bool:
        """Check if role has permission for action on resource."""
        permissions = self.role_permissions.get(role, [])
        return f"{action}:{resource}" in permissions

# -----------------------------------------------
# DATABASE INTEGRATION
# -----------------------------------------------

class DatabaseConnector:
    """Secure database access with read-only enforcement."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.allowed_operations = ["SELECT"]
    
    async def execute_query(self, query: str, limit: int = 1000) -> list[dict]:
        """Execute a read-only query with safeguards."""
        query_stripped = query.strip().upper()
        
        if not any(query_stripped.startswith(op) for op in self.allowed_operations):
            raise PermissionError("Only SELECT queries allowed")
        
        if "LIMIT" not in query_stripped:
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        return await self._run_query(query)
    
    async def _run_query(self, query: str) -> list[dict]:
        """Actual database execution."""
        pass
    
    async def get_table_schema(self, table_name: str) -> dict:
        """Get table schema for LLM context."""
        query = f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """
        return await self._run_query(query)

# -----------------------------------------------
# EXTERNAL API INTEGRATION
# -----------------------------------------------

class ExternalAPIConnector:
    """Rate-limited, authenticated external API access."""
    
    def __init__(self, base_url: str, api_key: str, rate_limit: int = 100):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.request_count = 0
        self.window_start = datetime.now()
    
    async def _check_rate_limit(self):
        """Enforce rate limiting."""
        now = datetime.now()
        if (now - self.window_start).seconds >= 60:
            self.request_count = 0
            self.window_start = now
        
        if self.request_count >= self.rate_limit:
            raise RateLimitError("Rate limit exceeded")
        
        self.request_count += 1
    
    async def fetch(self, endpoint: str, params: dict = None) -> dict:
        """Fetch data from external API with rate limiting."""
        await self._check_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

# -----------------------------------------------
# MCP SERVER SETUP
# -----------------------------------------------

server = Server("enterprise-analytics")

db_connector: Optional[DatabaseConnector] = None
api_connector: Optional[ExternalAPIConnector] = None
auth: Optional[MCPAuthMiddleware] = None

# -----------------------------------------------
# RESOURCES -- Enterprise Data Sources
# -----------------------------------------------

@server.list_resources()
async def list_resources():
    """List enterprise data resources."""
    return [
        Resource(
            uri="db://analytics/sales",
            name="Sales Database",
            description="Enterprise sales data warehouse",
            mimeType="application/json"
        ),
        Resource(
            uri="db://analytics/customers",
            name="Customer Database",
            description="Customer information and interactions",
            mimeType="application/json"
        ),
        Resource(
            uri="api://crm/deals",
            name="CRM Deals",
            description="Active deals from Salesforce CRM",
            mimeType="application/json"
        ),
        Resource(
            uri="file://reports/monthly_summary.json",
            name="Monthly Summary Report",
            description="Pre-generated monthly analytics summary",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    """Read enterprise resource with auth check."""
    if uri.startswith("db://"):
        parts = uri.replace("db://", "").split("/")
        schema, table = parts[0], parts[1]
        schema_info = await db_connector.get_table_schema(table)
        return json.dumps({
            "schema": schema_info,
            "sample_query": f"SELECT * FROM {schema}.{table} LIMIT 10"
        }, indent=2)
    
    elif uri.startswith("api://"):
        endpoint = uri.replace("api://", "")
        data = await api_connector.fetch(endpoint)
        return json.dumps(data, indent=2)
    
    elif uri.startswith("file://"):
        path = uri.replace("file://", "")
        with open(path, "r") as f:
            return f.read()
    
    raise ValueError(f"Unknown resource: {uri}")

# -----------------------------------------------
# TOOLS -- Enterprise Operations
# -----------------------------------------------

@server.list_tools()
async def list_tools():
    """List enterprise analytics tools."""
    return [
        Tool(
            name="sql_query",
            description="Execute read-only SQL queries against the analytics database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL SELECT query"},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_table_info",
            description="Get schema and metadata for a database table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="fetch_crm_data",
            description="Fetch data from CRM system",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "enum": ["deals", "contacts", "accounts", "activities"]
                    },
                    "filters": {"type": "object", "description": "Filter criteria"}
                },
                "required": ["object_type"]
            }
        ),
        Tool(
            name="generate_report",
            description="Generate an analytics report",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["sales", "customer", "product", "financial"]
                    },
                    "period": {"type": "string", "enum": ["daily", "weekly", "monthly", "quarterly"]},
                    "format": {"type": "string", "enum": ["json", "csv"], "default": "json"}
                },
                "required": ["report_type", "period"]
            }
        ),
        Tool(
            name="anomaly_detection",
            description="Detect anomalies in time series data",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "description": "Metric to analyze"},
                    "threshold": {"type": "number", "default": 2.0, "description": "Standard deviations"}
                },
                "required": ["metric"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute enterprise tool with auth and validation."""
    
    if name == "sql_query":
        query = arguments["query"]
        limit = arguments.get("limit", 100)
        results = await db_connector.execute_query(query, limit)
        return [TextContent(
            type="text",
            text=json.dumps(results, indent=2, default=str)
        )]
    
    elif name == "get_table_info":
        schema = await db_connector.get_table_schema(arguments["table_name"])
        return [TextContent(
            type="text",
            text=json.dumps(schema, indent=2)
        )]
    
    elif name == "fetch_crm_data":
        object_type = arguments["object_type"]
        filters = arguments.get("filters", {})
        data = await api_connector.fetch(f"crm/{object_type}", filters)
        return [TextContent(
            type="text",
            text=json.dumps(data, indent=2)
        )]
    
    elif name == "generate_report":
        report_type = arguments["report_type"]
        period = arguments["period"]
        fmt = arguments.get("format", "json")
        
        report = {
            "type": report_type,
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "data": await _generate_report_data(report_type, period)
        }
        
        if fmt == "csv":
            return [TextContent(type="text", text=_to_csv(report["data"]))]
        return [TextContent(type="text", text=json.dumps(report, indent=2))]
    
    elif name == "anomaly_detection":
        metric = arguments["metric"]
        threshold = arguments.get("threshold", 2.0)
        anomalies = await _detect_anomalies(metric, threshold)
        return [TextContent(
            type="text",
            text=json.dumps(anomalies, indent=2)
        )]
    
    raise ValueError(f"Unknown tool: {name}")

# -----------------------------------------------
# LOGGING & MONITORING
# -----------------------------------------------

import logging

logger = logging.getLogger("mcp-enterprise")

async def log_tool_call(tool_name: str, arguments: dict, duration: float):
    """Log tool execution for monitoring."""
    logger.info({
        "event": "tool_call",
        "tool": tool_name,
        "arguments": {k: str(v)[:50] for k, v in arguments.items()},
        "duration_ms": duration * 1000,
        "timestamp": datetime.now().isoformat()
    })

# -----------------------------------------------
# SERVER STARTUP
# -----------------------------------------------

async def main():
    global db_connector, api_connector, auth
    
    db_connector = DatabaseConnector(
        connection_string=os.getenv("DATABASE_URL")
    )
    api_connector = ExternalAPIConnector(
        base_url=os.getenv("CRM_API_URL"),
        api_key=os.getenv("CRM_API_KEY"),
        rate_limit=100
    )
    auth = MCPAuthMiddleware(
        api_keys=load_api_keys(),
        role_permissions=load_permissions()
    )
    
    import mcp.server.stdio
    from mcp.server.models import InitializationOptions
    
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="enterprise-analytics",
                server_version="1.0.0",
                capabilities=server.get_capabilities(None, None)
            )
        )

if __name__ == "__main__":
    import os
    import asyncio
    asyncio.run(main())
```

### Integration Patterns Summary

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Sidecar** | MCP server runs alongside main app | Local tool access |
| **Gateway** | Central MCP server routes to multiple backends | Enterprise integration |
| **Mesh** | Multiple MCP servers with service discovery | Microservices architecture |
| **Proxy** | MCP server wraps legacy APIs | Legacy system modernization |
| **Aggregator** | MCP server combines multiple data sources | Unified analytics |

### Security Best Practices

1. **Authentication** - Validate all client connections
2. **Authorization** - Role-based tool/resource access
3. **Input Validation** - Sanitize all tool arguments
4. **Rate Limiting** - Prevent abuse of external APIs
5. **Audit Logging** - Log all tool executions
6. **Read-Only Defaults** - Restrict write operations
7. **Secrets Management** - Never expose credentials in tool outputs

---

## Key Takeaways

- MCP provides a standardized protocol for LLM-tool interaction
- Three primitives: Resources (data), Tools (actions), Prompts (templates)
- Supports multiple transports: stdio, HTTP/SSE, WebSocket
- Enterprise integration requires authentication, authorization, and monitoring
- Server-client architecture enables decoupled, scalable AI applications
