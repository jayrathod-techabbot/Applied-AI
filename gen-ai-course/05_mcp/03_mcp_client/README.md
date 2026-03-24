# MCP Clients - Building AI Applications

This module covers building MCP clients from basics to enterprise-level implementation with hands-on examples.

---

## Table of Contents

1. [Introduction to MCP Clients](#introduction-to-mcp-clients)
2. [Client Architecture](#client-architecture)
3. [Basic Client Implementation](#basic-client-implementation)
4. [Advanced Client Features](#advanced-client-features)
5. [Hands-On Labs](#hands-on-labs)
6. [Integration Patterns](#integration-patterns)

---

## Introduction to MCP Clients

### What is an MCP Client?

An MCP Client is an application that connects to one or more MCP servers to access tools, resources, and prompts. It serves as the bridge between AI applications and MCP servers.

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Client Role                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐         ┌────────────┐                   │
│   │  AI Application │────────►│   MCP      │                   │
│   │  (Your App)     │         │   Client   │                   │
│   └─────────────────┘         └──────┬─────┘                   │
│                                       │                          │
│                              ┌────────▼────────┐                │
│                              │  MCP Servers    │                │
│                              │  • Weather      │                │
│                              │  • Database     │                │
│                              │  • Filesystem   │                │
│                              └──────────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Client Capabilities

| Capability | Description | Use Case |
|------------|-------------|----------|
| **Connection Management** | Connect to multiple servers | Multi-service integration |
| **Tool Discovery** | List available tools | Dynamic capability finding |
| **Tool Execution** | Call tools on servers | Execute actions |
| **Resource Access** | Read data from servers | Fetch information |
| **Session Management** | Maintain state | Long-running operations |

---

## Client Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   MCP Client Components                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Connection Manager                     │  │
│  │   • Server registry                                      │  │
│  │   • Connection pooling                                   │  │
│  │   • Reconnection logic                                   │  │
│  │   • Transport selection (stdio/HTTP)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Protocol Handler                       │  │
│  │   • JSON-RPC message building                            │  │
│  │   • Request/response handling                            │  │
│  │   • Error parsing                                        │  │
│  │   • Protocol version negotiation                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Tool Registry                          │  │
│  │   • Discovered tools cache                               │  │
│  │   • Tool schema management                               │  │
│  │   • Type checking                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Application Interface                  │  │
│  │   • High-level API                                       │  │
│  │   • Async interface                                      │  │
│  │   • Error abstraction                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Client-Server Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Client-Server Communication                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    CLIENT                                                        │
│       │                                                          │
│       │ 1. Connect to server                                    │
│       ▼                                                          │
│       │ 2. Send initialize                                      │
│       ├────────────────────────────────────────────────────────►
│       │                                    SERVER               │
│       │                                          │              │
│       │ 3. Receive capabilities                               │
│       │◄─────────────────────────────────────────┤              │
│       │                                          │              │
│       │ 4. List available tools                                │
│       ├────────────────────────────────────────────────────────►
│       │                                          │              │
│       │ 5. Return tool list                                    │
│       │◄─────────────────────────────────────────┤              │
│       │                                          │              │
│       │ 6. (AI decides to call tool)                           │
│       │                                                          │
│       │ 7. Call tool with arguments                            │
│       ├────────────────────────────────────────────────────────►
│       │                                          │              │
│       │ 8. Execute tool                                       │
│       │                                          │              │
│       │ 9. Return result                                      │
│       │◄─────────────────────────────────────────┤              │
│       │                                          │              │
│       ▼ (10. Process result for AI)                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Basic Client Implementation

### Step 1: Install MCP SDK

```bash
pip install mcp
```

### Step 2: Create Basic Client

```python
"""Basic MCP Client Example"""
import asyncio
from mcp import Client

async def main():
    # Connect to server
    async with Client("weather-server") as client:
        
        # List available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Call a tool
        result = await client.call_tool(
            "get_weather",
            {"city": "London", "country": "UK"}
        )
        
        print(f"\nWeather: {result[0].text}")

asyncio.run(main())
```

### Step 3: Multiple Servers

```python
"""Multiple Server Connections"""
import asyncio
from mcp import Client
from mcp.client import StdioConnection

async def main():
    # Connect to multiple servers
    async with Client("weather-server") as weather_client, \
               Client("database-server") as db_client:
        
        # Use weather server
        weather = await weather_client.call_tool(
            "get_weather",
            {"city": "Paris"}
        )
        
        # Use database server
        users = await db_client.call_tool(
            "execute_query",
            {"query": "SELECT * FROM users LIMIT 5"}
        )
        
        print(f"Weather: {weather[0].text}")
        print(f"Users: {users[0].text}")

asyncio.run(main())
```

---

## Advanced Client Features

### 1. Tool Schema Inspection

```python
"""Inspect tool schemas for dynamic handling"""
import asyncio
from mcp import Client
from typing import Any

async def main():
    async with Client("my-server") as client:
        # Get all tools with full schema
        tools = await client.list_tools()
        
        for tool in tools:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Input Schema: {tool.inputSchema}")
            
            # Check if a parameter exists
            if "properties" in tool.inputSchema:
                print(f"Parameters: {list(tool.inputSchema['properties'].keys())}")

asyncio.run(main())
```

### 2. Resource Access

```python
"""Access resources from server"""
import asyncio
from mcp import Client

async def main():
    async with Client("data-server") as client:
        # List available resources
        resources = await client.list_resources()
        print("Available resources:")
        for resource in resources:
            print(f"  - {resource.name}: {resource.uri}")
        
        # Read a specific resource
        if resources:
            content = await client.read_resource(resources[0].uri)
            print(f"\nResource content: {content}")

asyncio.run(main())
```

### 3. Error Handling

```python
"""Comprehensive error handling"""
import asyncio
from mcp import Client
from mcp.types import Error

async def main():
    try:
        async with Client("my-server") as client:
            try:
                result = await client.call_tool(
                    "get_data",
                    {"invalid_param": "value"}
                )
            except Error as e:
                print(f"MCP Error: {e.message}")
                if e.data:
                    print(f"Error data: {e.data}")
            except Exception as e:
                print(f"Unexpected error: {e}")
                
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(main())
```

### 4. Connection Management

```python
"""Advanced connection management"""
import asyncio
from mcp.client import StdioConnection, SseConnection
from mcp import Client

class ConnectionManager:
    def __init__(self):
        self.connections = {}
    
    async def connect_stdio(self, server_name: str, command: list):
        """Connect via stdio"""
        connection = StdioConnection(command)
        client = Client(server_name, connection)
        await client.connect()
        self.connections[server_name] = client
        return client
    
    async def connect_sse(self, server_name: str, url: str):
        """Connect via SSE"""
        connection = SseConnection(url)
        client = Client(server_name, connection)
        await client.connect()
        self.connections[server_name] = client
        return client
    
    async def disconnect(self, server_name: str):
        """Disconnect from server"""
        if server_name in self.connections:
            await self.connections[server_name].close()
            del self.connections[server_name]
    
    async def disconnect_all(self):
        """Disconnect from all servers"""
        for client in self.connections.values():
            await client.close()
        self.connections.clear()

# Usage
async def main():
    manager = ConnectionManager()
    
    try:
        # Connect to multiple servers
        weather = await manager.connect_stdio(
            "weather",
            ["python", "weather_server.py"]
        )
        db = await manager.connect_sse(
            "database",
            "http://localhost:8000/mcp"
        )
        
        # Use servers
        result = await weather.call_tool("get_weather", {"city": "NYC"})
        print(result)
        
    finally:
        await manager.disconnect_all()

asyncio.run(main())
```

---

## Hands-On Labs

### Lab 1: Build a Weather Client

**Objective**: Create a client that queries a weather MCP server

```python
"""Weather Client - Lab 1 Solution"""
import asyncio
from mcp import Client

class WeatherClient:
    """Client for weather MCP server"""
    
    def __init__(self):
        self.client = None
    
    async def connect(self):
        """Connect to weather server"""
        self.client = Client("weather-server")
        await self.client.connect()
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.client:
            await self.client.close()
    
    async def get_current_weather(self, city: str, country: str = "US") -> str:
        """Get current weather for a city"""
        result = await self.client.call_tool(
            "get_current_weather",
            {"city": city, "country": country}
        )
        return result[0].text if result else "No result"
    
    async def get_forecast(self, city: str, days: int = 3) -> str:
        """Get weather forecast"""
        result = await self.client.call_tool(
            "get_forecast",
            {"city": city, "days": days}
        )
        return result[0].text if result else "No result"

async def main():
    client = WeatherClient()
    
    try:
        await client.connect()
        
        # Get current weather
        weather = await client.get_current_weather("London", "UK")
        print(f"Current weather: {weather}")
        
        # Get forecast
        forecast = await client.get_forecast("London", 5)
        print(f"\nForecast: {forecast}")
        
    finally:
        await client.disconnect()

asyncio.run(main())
```

### Lab 2: Build a Database Client

**Objective**: Create a client that executes queries via MCP

```python
"""Database Client - Lab 2 Solution"""
import asyncio
from mcp import Client
from typing import List, Dict, Any

class DatabaseClient:
    """Client for database MCP server"""
    
    def __init__(self):
        self.client = None
    
    async def connect(self):
        """Connect to database server"""
        self.client = Client("database-server")
        await self.client.connect()
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.client:
            await self.client.close()
    
    async def list_tables(self) -> List[str]:
        """List all tables in database"""
        result = await self.client.call_tool("list_tables", {})
        if result:
            return result[0].text.split(", ")
        return []
    
    async def execute_query(self, query: str, limit: int = 10) -> str:
        """Execute a SELECT query"""
        result = await self.client.call_tool(
            "execute_query",
            {"query": query, "limit": limit}
        )
        return result[0].text if result else "No results"
    
    async def get_table_schema(self, table_name: str) -> str:
        """Get table schema"""
        query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        return await self.execute_query(query)

async def main():
    client = DatabaseClient()
    
    try:
        await client.connect()
        
        # List tables
        tables = await client.list_tables()
        print(f"Tables: {tables}")
        
        # Execute query
        if tables:
            query = f"SELECT * FROM {tables[0]} LIMIT 5"
            result = await client.execute_query(query)
            print(f"\nQuery result:\n{result}")
        
    finally:
        await client.disconnect()

asyncio.run(main())
```

### Lab 3: Build an Enterprise Client

**Objective**: Create a client with authentication, retry, and monitoring

```python
"""Enterprise Client - Lab 3 Solution"""
import asyncio
import time
import logging
from typing import Any, Dict
from mcp import Client
from mcp.client import StdioConnection
from dataclasses import dataclass
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClientConfig:
    """Client configuration"""
    server_name: str
    command: list
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

class EnterpriseClient:
    """Enterprise-grade MCP client"""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.client: Client | None = None
        self.connected = False
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "total_latency": 0.0
        }
    
    async def connect(self) -> bool:
        """Connect to server with retries"""
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Connecting to {self.config.server_name}...")
                
                connection = StdioConnection(self.config.command)
                self.client = Client(self.config.server_name, connection)
                await self.client.connect()
                
                # Verify connection by listing tools
                await self.client.list_tools()
                
                self.connected = True
                logger.info(f"Connected to {self.config.server_name}")
                return True
                
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        logger.error(f"Failed to connect to {self.config.server_name}")
        return False
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.client:
            await self.client.close()
            self.connected = False
            logger.info(f"Disconnected from {self.config.server_name}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> list:
        """Call tool with metrics and retry"""
        if not self.connected:
            raise ConnectionError("Not connected to server")
        
        start_time = time.time()
        self.metrics["requests"] += 1
        
        for attempt in range(self.config.max_retries):
            try:
                result = await asyncio.wait_for(
                    self.client.call_tool(tool_name, arguments),
                    timeout=self.config.timeout
                )
                
                # Record success metrics
                self.metrics["successes"] += 1
                latency = time.time() - start_time
                self.metrics["total_latency"] += latency
                
                logger.info(f"Tool call {tool_name} succeeded in {latency:.2f}s")
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on {tool_name} (attempt {attempt + 1})")
                if attempt == self.config.max_retries - 1:
                    self.metrics["failures"] += 1
                    raise
                    
            except Exception as e:
                logger.error(f"Error calling {tool_name}: {e}")
                if attempt == self.config.max_retries - 1:
                    self.metrics["failures"] += 1
                    raise
                
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["requests"]
            if self.metrics["requests"] > 0 else 0
        )
        
        return {
            "requests": self.metrics["requests"],
            "successes": self.metrics["successes"],
            "failures": self.metrics["failures"],
            "success_rate": self.metrics["successes"] / max(1, self.metrics["requests"]),
            "avg_latency": avg_latency
        }

# Usage
async def main():
    config = ClientConfig(
        server_name="enterprise-server",
        command=["python", "server.py"],
        timeout=30,
        max_retries=3
    )
    
    client = EnterpriseClient(config)
    
    try:
        # Connect
        if not await client.connect():
            print("Failed to connect")
            return
        
        # Call tools
        result = await client.call_tool("get_data", {"type": "users"})
        print(f"Result: {result}")
        
        # Get metrics
        metrics = client.get_metrics()
        print(f"\nMetrics: {metrics}")
        
    finally:
        await client.disconnect()

asyncio.run(main())
```

---

## Integration Patterns

### 1. LLM Integration

```python
"""Integration with LLM providers"""
import asyncio
from mcp import Client

async def get_tools_for_llm(client: Client) -> list:
    """Get tools in LLM-compatible format"""
    tools = await client.list_tools()
    
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        }
        for tool in tools
    ]

async def main():
    async with Client("my-server") as client:
        # Get tools for LLM
        tools = await get_tools_for_llm(client)
        
        # Use with OpenAI
        # response = openai.chat.completions.create(
        #     model="gpt-4",
        #     messages=[...],
        #     tools=tools
        # )
        
        # Or with Anthropic
        # response = anthropic.messages.create(
        #     model="claude-3",
        #     messages=[...],
        #     tools=tools
        # )

asyncio.run(main())
```

### 2. LangChain Integration

```python
"""LangChain MCP Tool Integration"""
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from mcp import Client
from langchain.tools import Tool

async def create_langchain_tools(client: Client) -> list:
    """Create LangChain tools from MCP server"""
    mcp_tools = await client.list_tools()
    
    return [
        Tool(
            name=tool.name,
            description=tool.description,
            func=lambda args, t=tool.name: client.call_tool(t, args)
        )
        for tool in mcp_tools
    ]

async def main():
    async with Client("my-server") as client:
        # Create LangChain tools
        tools = await create_langchain_tools(client)
        
        # Create agent
        llm = ChatOpenAI(model="gpt-4")
        agent = create_openai_functions_agent(llm, tools)
        
        executor = AgentExecutor(agent=agent, tools=tools)
        
        # Run agent
        result = await executor.ainvoke({
            "input": "What's the weather in London?"
        })
        print(result)

asyncio.run(main())
```

### 3. AutoGen Integration

```python
"""AutoGen MCP Integration"""
import asyncio
from autogen import ConversableAgent
from mcp import Client

async def create_autogen_tools(client: Client) -> list:
    """Create AutoGen tools from MCP server"""
    mcp_tools = await client.list_tools()
    
    def create_tool_func(tool):
        async def func(arguments: dict):
            result = await client.call_tool(tool.name, arguments)
            return result[0].text if result else "No result"
        return func
    
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
            "function": create_tool_func(tool)
        }
        for tool in mcp_tools
    ]

async def main():
    async with Client("my-server") as client:
        tools = await create_autogen_tools(client)
        
        agent = ConversableAgent(
            name="assistant",
            llm_config={"tools": tools}
        )
        
        # Use agent
        result = await agent.a_generate_reply(
            messages=[{"role": "user", "content": "Get weather for NYC"}]
        )

asyncio.run(main())
```

---

## Summary

In this module, you learned:

- ✅ MCP Client architecture and components
- ✅ Basic client implementation
- ✅ Advanced features: schemas, resources, error handling
- ✅ Hands-on labs: Weather, Database, Enterprise clients
- ✅ Integration patterns: LLM, LangChain, AutoGen

---

## Next Steps

Review [interview.md](../interview.md) for interview preparation and review the architecture diagrams in [01_mcp_overview/architecture.md](../01_mcp_overview/architecture.md).

---

## References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [LangChain MCP](https://python.langchain.com/docs/modules/agents/)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)