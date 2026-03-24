# MCP Servers - Building Production-Ready Servers

This module covers building MCP servers from basics to enterprise-level implementation with hands-on examples.

---

## Table of Contents

1. [Introduction to MCP Servers](#introduction-to-mcp-servers)
2. [Server Architecture](#server-architecture)
3. [Basic Server Implementation](#basic-server-implementation)
4. [Advanced Server Features](#advanced-server-features)
5. [Hands-On Labs](#hands-on-labs)
6. [Best Practices](#best-practices)

---

## Introduction to MCP Servers

### What is an MCP Server?

An MCP Server is a service that exposes tools, resources, and prompts to MCP clients. It acts as a bridge between AI applications and external systems.

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Server Role                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌────────────┐         ┌─────────────────┐                  │
│   │   MCP      │────────►│   MCP Server    │                  │
│   │   Client   │         │                 │                  │
│   └────────────┘         │  • Tools        │                  │
│                          │  • Resources    │                  │
│                          │  • Prompts      │                  │
│                          └────────┬────────┘                  │
│                                   │                             │
│                                   ▼                             │
│                          ┌─────────────────┐                  │
│                          │ External Systems│                  │
│                          │ • APIs          │                  │
│                          │ • Databases     │                  │
│                          │ • Filesystems   │                  │
│                          └─────────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Server Capabilities

| Capability | Description | Example |
|------------|-------------|---------|
| **Tools** | Executable functions AI can call | `get_weather()`, `query_db()` |
| **Resources** | Data sources AI can read | Files, API responses |
| **Prompts** | Reusable prompt templates | System instructions |

---

## Server Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   MCP Server Components                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Request Router                         │  │
│  │   • Route requests to handlers                           │  │
│  │   • Validate message format                              │  │
│  │   • Handle protocol version negotiation                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Handler Registry                       │  │
│  │   • list_tools()  - Return available tools              │  │
│  │   • call_tool()   - Execute tool logic                  │  │
│  │   • list_resources() - Return available resources       │  │
│  │   • read_resource() - Read resource content             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Tool Implementations                  │  │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │  │
│  │   │Tool 1  │ │Tool 2  │ │Tool 3  │ │Tool N  │       │  │
│  │   └─────────┘ └─────────┘ └─────────┘ └─────────┘       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    External Integrations                 │  │
│  │   • HTTP Clients    • Database Connections                │  │
│  │   • File System    • Authentication                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Server Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Server Lifecycle                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. STARTUP                                                      │
│     • Load configuration                                        │
│     • Initialize connections                                     │
│     • Register tools                                            │
│                                                                  │
│  2. INITIALIZATION (MCP Protocol)                              │
│     • Client sends initialize request                           │
│     • Server responds with capabilities                         │
│     • Protocol version agreed                                    │
│                                                                  │
│  3. OPERATION                                                    │
│     • Handle tool discovery                                     │
│     • Execute tool calls                                        │
│     • Manage resources                                          │
│                                                                  │
│  4. SHUTDOWN                                                     │
│     • Close connections                                         │
│     • Cleanup resources                                         │
│     • Log statistics                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Basic Server Implementation

### Step-by-Step Guide

#### Step 1: Install MCP SDK

```bash
pip install mcp
```

#### Step 2: Create Basic Server

```python
"""Basic MCP Server Example"""
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import asyncio

# Create server instance with name
app = Server("basic-weather-server")

# Define tool listing handler
@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools"""
    return [
        Tool(
            name="get_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name"
                    },
                    "country": {
                        "type": "string",
                        "description": "Country code (e.g., US, UK)",
                        "default": "US"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_forecast",
            description="Get weather forecast for next days",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "days": {
                        "type": "integer",
                        "description": "Number of days (1-7)",
                        "minimum": 1,
                        "maximum": 7,
                        "default": 3
                    }
                },
                "required": ["city"]
            }
        )
    ]

# Define tool execution handler
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    if name == "get_weather":
        # Mock weather data - replace with real API call
        weather_data = {
            "city": arguments["city"],
            "temperature": 22,
            "condition": "Partly Cloudy",
            "humidity": 65
        }
        return [TextContent(
            type="text",
            text=f"Weather in {weather_data['city']}: "
                 f"{weather_data['temperature']}°C, "
                 f"{weather_data['condition']}, "
                 f"Humidity: {weather_data['humidity']}%"
        )]
    
    elif name == "get_forecast":
        days = arguments.get("days", 3)
        forecast = [f"Day {i+1}: Sunny, 25°C" for i in range(days)]
        return [TextContent(type="text", text="\n".join(forecast))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

# Run server
async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 3: Run the Server

```bash
python basic_server.py
```

---

## Advanced Server Features

### 1. Resources

```python
"""MCP Server with Resources"""
from mcp.server import Server
from mcp.types import Resource, TextContent
from mcp.server.stdio import stdio_server
import asyncio

app = Server("resource-server")

# Define resources
@app.list_resources()
async def list_resources():
    """Return available resources"""
    return [
        Resource(
            uri="config://server/status",
            name="Server Status",
            description="Current server status and health metrics",
            mimeType="application/json"
        ),
        Resource(
            uri="file:///data/users.json",
            name="User Data",
            description="User data file",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "config://server/status":
        return '{"status": "healthy", "uptime": "24h", "requests": 1234}'
    elif uri == "file:///data/users.json":
        return '[{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]'
    else:
        raise ValueError(f"Unknown resource: {uri}")
```

### 2. Prompts

```python
"""MCP Server with Prompts"""
from mcp.server import Server
from mcp.types import Prompt, PromptMessage
from mcp.server.stdio import stdio_server
import asyncio

app = Server("prompt-server")

@app.list_prompts()
async def list_prompts():
    """Return available prompts"""
    return [
        Prompt(
            name="analyze_data",
            description="Analyze data with specific parameters",
            arguments=[
                {"name": "data_type", "description": "Type of data to analyze"},
                {"name": "format", "description": "Output format"}
            ]
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict):
    """Generate prompt content"""
    if name == "analyze_data":
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Analyze {arguments['data_type']} data "
                         f"and present in {arguments['format']} format."
                )
            )
        ]
```

### 3. Error Handling

```python
"""MCP Server with Error Handling"""
from mcp.server import Server
from mcp.types import Tool, TextContent, ErrorResult
from mcp.server.stdio import stdio_server
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Server("error-handling-server")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution with error handling"""
    try:
        # Validate arguments
        if name == "risky_operation":
            if "value" not in arguments:
                raise ValueError("Missing required parameter: value")
            
            # Simulate operation
            if arguments["value"] < 0:
                raise ValueError("Value must be positive")
            
            return [TextContent(type="text", text=f"Result: {arguments['value'] * 2}")]
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    except Exception as e:
        logger.exception(f"Unexpected error in {name}")
        return [TextContent(type="text", text=f"Internal error: {str(e)}")]
```

---

## Hands-On Labs

### Lab 1: Build a Weather MCP Server

**Objective**: Create a production-ready weather server

```python
"""Weather MCP Server - Lab 1 Solution"""
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, Resource
from mcp.server.stdio import stdio_server
import asyncio
import aiohttp
from typing import Any

app = Server("weather-server")

# Configuration
API_KEY = "your-api-key"  # Set via environment variable
BASE_URL = "https://api.openweathermap.org/data/2.5"

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_current_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "default": "metric"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_forecast",
            description="Get weather forecast",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "days": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 3
                    }
                },
                "required": ["city"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    city = arguments.get("city", "")
    
    if name == "get_current_weather":
        # In production, replace with real API call
        mock_data = {
            "temp": 20,
            "feels_like": 19,
            "humidity": 70,
            "description": "clear sky"
        }
        return [TextContent(
            type="text",
            text=f"🌤️ Weather in {city}: "
                 f"{mock_data['temp']}°C, {mock_data['description']}, "
                 f"Feels like {mock_data['feels_like']}°C, "
                 f"Humidity: {mock_data['humidity']}%"
        )]
    
    elif name == "get_forecast":
        days = arguments.get("days", 3)
        forecast = "\n".join([
            f"Day {i+1}: ☀️ 22°C - 28°C, Partly Cloudy"
            for i in range(days)
        ])
        return [TextContent(type="text", text=f"📅 Forecast for {city}:\n{forecast}")]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### Lab 2: Build a Database MCP Server

**Objective**: Create a server that executes SQL queries

```python
"""Database MCP Server - Lab 2"""
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import asyncio
import asyncpg
from typing import Any

app = Server("database-server")

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "user": "user",
    "password": "password"
}

# Connection pool
pool: asyncpg.Pool | None = None

async def init_db():
    """Initialize database connection pool"""
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="execute_query",
            description="Execute a SELECT query (read-only)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum rows to return"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if not pool:
        return [TextContent(type="text", text="Database not connected")]
    
    if name == "execute_query":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        
        # Safety check - only SELECT
        if not query.strip().upper().startswith("SELECT"):
            return [TextContent(type="text", text="Only SELECT queries allowed")]
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(f"{query} LIMIT {limit}")
                
            if not rows:
                return [TextContent(type="text", text="No results found")]
            
            # Format results
            headers = list(rows[0].keys())
            result = " | ".join(headers) + "\n"
            result += "-" * len(result) + "\n"
            
            for row in rows:
                result += " | ".join(str(v) for v in row.values()) + "\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Query error: {str(e)}")]
    
    elif name == "list_tables":
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            
            tables = [row['table_name'] for row in rows]
            return [TextContent(type="text", text="Tables: " + ", ".join(tables))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    await init_db()
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### Lab 3: Build an Enterprise MCP Server

**Objective**: Create a server with authentication, rate limiting, and logging

```python
"""Enterprise MCP Server - Lab 3"""
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import asyncio
import logging
import time
from functools import wraps
from typing import Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Server("enterprise-server")

# Rate limiting
class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = {}
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.calls:
            self.calls[client_id] = []
        
        # Clean old calls
        self.calls[client_id] = [
            t for t in self.calls[client_id] 
            if now - t < self.period
        ]
        
        if len(self.calls[client_id]) >= self.max_calls:
            return False
        
        self.calls[client_id].append(now)
        return True

rate_limiter = RateLimiter(max_calls=100, period=60)

# Authentication
API_KEYS = {
    "key1": "client1",
    "key2": "client2"
}

def authenticate(func: Callable):
    """Authentication decorator"""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        # In stdio mode, we assume local execution
        # In production, implement proper auth
        return await func(request, *args, **kwargs)
    return wrapper

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="secure_data_access",
            description="Access secure enterprise data",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "enum": ["users", "reports", "analytics"],
                        "description": "Type of data to access"
                    }
                },
                "required": ["data_type"]
            }
        ),
        Tool(
            name="execute_action",
            description="Execute an enterprise action",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "parameters": {"type": "object"}
                },
                "required": ["action"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Rate limiting check
    client_id = "default"  # In production, extract from request
    if not rate_limiter.is_allowed(client_id):
        logger.warning(f"Rate limit exceeded for {client_id}")
        return [TextContent(
            type="text", 
            text="Rate limit exceeded. Please try again later."
        )]
    
    logger.info(f"Tool call: {name} with args: {arguments}")
    
    try:
        if name == "secure_data_access":
            data_type = arguments.get("data_type")
            
            # Simulate secure data access
            data_store = {
                "users": [{"id": 1, "name": "User A"}, {"id": 2, "name": "User B"}],
                "reports": ["Q1 Report", "Q2 Report"],
                "analytics": {"views": 1000, "clicks": 500}
            }
            
            return [TextContent(
                type="text",
                text=f"Data ({data_type}): {data_store.get(data_type, 'Not found')}"
            )]
        
        elif name == "execute_action":
            action = arguments.get("action")
            params = arguments.get("parameters", {})
            
            logger.info(f"Executing action: {action} with params: {params}")
            
            return [TextContent(
                type="text",
                text=f"Action '{action}' completed successfully"
            ])
    
    except Exception as e:
        logger.exception(f"Error in tool execution")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    logger.info("Starting Enterprise MCP Server")
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

### 1. Tool Design

| Practice | Description | Example |
|----------|-------------|---------|
| **Clear Names** | Use descriptive, consistent naming | `get_user_by_id` not `getUser` |
| **Helpful Descriptions** | Explain when to use the tool | "Use when you need current weather" |
| **Proper Schema** | Define clear input parameters | Use enums for fixed values |
| **Idempotency** | Same input produces same output | Cache results |

### 2. Error Handling

```python
# Good error handling
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        # Execute tool
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=str(result))]
    
    except ValidationError as e:
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}"
        )]
    
    except ExternalServiceError as e:
        logger.error(f"External service error: {e}")
        return [TextContent(
            type="text",
            text="Service temporarily unavailable. Please try again."
        )]
    
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text="An unexpected error occurred"
        )]
```

### 3. Logging and Monitoring

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Structured logging
logger.info(
    "tool_executed",
    extra={
        "tool_name": name,
        "arguments": arguments,
        "timestamp": datetime.utcnow().isoformat(),
        "duration_ms": duration
    }
)
```

### 4. Configuration Management

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 8000
    api_key: Optional[str] = None
    max_connections: int = 10
    timeout: int = 30

# Load from environment
config = ServerConfig(
    api_key=os.getenv("MCP_API_KEY")
)
```

---

## Summary

In this module, you learned:

- ✅ MCP Server architecture and components
- ✅ Basic server implementation with tools
- ✅ Resources and prompts
- ✅ Error handling strategies
- ✅ Hands-on labs: Weather, Database, Enterprise servers
- ✅ Best practices for production

---

## Next Steps

Proceed to [03_mcp_client](../03_mcp_client/README.md) to learn how to build MCP clients.

---

## References

- [MCP SDK Python](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Best Practices Guide](https://modelcontextprotocol.io/docs)