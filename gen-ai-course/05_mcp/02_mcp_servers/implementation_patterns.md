# MCP Server Implementation Patterns

This document provides implementation patterns and code examples for building robust MCP servers.

---

## 1. Server Patterns

### 1.1 Minimal Server Pattern

```python
"""Minimal MCP Server - Quick Start"""
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import asyncio

# Create server
server = Server("minimal-server")

# Define tools
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="echo",
            description="Echo back the input",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name, arguments):
    return [TextContent(type="text", text=arguments["message"])]

# Run server
async def main():
    async with stdio_server() as streams:
        await server.run(
            streams[0], 
            streams[1], 
            server.create_initialization_options()
        )

asyncio.run(main())
```

### 1.2 Factory Pattern

```python
"""Server Factory - Create servers with configuration"""
from mcp.server import Server
from mcp.types import Tool, TextContent
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ServerConfig:
    name: str
    tools: List[Dict[str, Any]]
    description: str = ""

class ServerFactory:
    @staticmethod
    def create(config: ServerConfig) -> Server:
        server = Server(config.name)
        
        # Create tool definitions
        tools = [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t.get("schema", {})
            )
            for t in config.tools
        ]
        
        @server.list_tools()
        async def list_tools():
            return tools
        
        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            # Route to appropriate handler
            for tool in config.tools:
                if tool["name"] == name:
                    return await tool["handler"](arguments)
            raise ValueError(f"Unknown tool: {name}")
        
        return server

# Usage
config = ServerConfig(
    name="my-server",
    tools=[
        {
            "name": "add",
            "description": "Add two numbers",
            "schema": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            }
        }
    ]
)

server = ServerFactory.create(config)
```

---

## 2. Tool Patterns

### 2.1 Tool with Validation

```python
"""Tool with input validation"""
from pydantic import BaseModel, Field
from typing import Optional

class WeatherInput(BaseModel):
    city: str = Field(..., min_length=1, max_length=100)
    country: Optional[str] = Field(default="US", max_length=2)
    units: str = Field(default="metric", pattern="^(metric|imperial)$")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_weather":
        try:
            # Validate input
            validated = WeatherInput(**arguments)
            
            # Process
            result = await get_weather_data(
                city=validated.city,
                country=validated.country,
                units=validated.units
            )
            return [TextContent(type="text", text=result)]
            
        except ValidationError as e:
            return [TextContent(type="text", text=f"Validation error: {e}")]
```

### 2.2 Async Tool Pattern

```python
"""Async tool implementation"""
import aiohttp
import asyncio

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "fetch_data":
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.example.com/data",
                params=arguments
            ) as response:
                data = await response.json()
                return [TextContent(type="text", text=str(data))]
```

### 2.3 Cached Tool Pattern

```python
"""Tool with caching"""
from functools import lru_cache
import time

cache = {}
CACHE_TTL = 300  # 5 minutes

def cache_result(func):
    """Decorator for caching tool results"""
    async def wrapper(name, arguments):
        # Create cache key
        key = f"{name}:{str(arguments)}"
        
        # Check cache
        if key in cache:
            result, timestamp = cache[key]
            if time.time() - timestamp < CACHE_TTL:
                return result
        
        # Execute and cache
        result = await func(name, arguments)
        cache[key] = (result, time.time())
        return result
    
    return wrapper

@app.call_tool()
@cache_result
async def call_tool(name: str, arguments: dict):
    # Original implementation
    pass
```

---

## 3. Error Handling Patterns

### 3.1 Graceful Error Handling

```python
"""Comprehensive error handling"""
from mcp.types import TextContent
import logging
import traceback

logger = logging.getLogger(__name__)

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "risky_operation":
            # Validate inputs
            if not arguments.get("required_param"):
                raise ValueError("Missing required parameter")
            
            # Execute
            result = await process_operation(arguments)
            return [TextContent(type="text", text=result)]
    
    except ValueError as e:
        # Client error - return clear message
        logger.warning(f"Invalid input for {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}"
        )]
    
    except TimeoutError as e:
        # Timeout - explain and suggest retry
        logger.error(f"Timeout in {name}")
        return [TextContent(
            type="text",
            text="Operation timed out. Please try again."
        )]
    
    except Exception as e:
        # Unexpected error - log but hide details
        logger.exception(f"Unexpected error in {name}")
        return [TextContent(
            type="text",
            text="An internal error occurred. Please contact support."
        )]
```

### 3.2 Retry Pattern

```python
"""Retry pattern for transient failures"""
import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

async def retry_async(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
) -> T:
    """Retry async function with exponential backoff"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = delay * (backoff ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
    
    raise last_exception

# Usage
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "fetch_external":
        async def fetch():
            return await external_api_call(arguments)
        
        result = await retry_async(fetch)
        return [TextContent(type="text", text=str(result))]
```

---

## 4. Resource Patterns

### 4.1 Dynamic Resources

```python
"""Dynamic resource listing"""
@app.list_resources()
async def list_resources():
    resources = []
    
    # File resources
    for file in os.listdir("/data"):
        resources.append(Resource(
            uri=f"file:///data/{file}",
            name=file,
            description=f"Data file: {file}",
            mimeType="application/json"
        ))
    
    # API resources
    resources.append(Resource(
        uri="api://status",
        name="API Status",
        description="Current API status",
        mimeType="application/json"
    ))
    
    return resources
```

### 4.2 Resource Caching

```python
"""Cached resource reading"""
from functools import lru_cache

resource_cache = {}
CACHE_TTL = 60  # 1 minute

@app.read_resource()
async def read_resource(uri: str) -> str:
    # Check cache
    if uri in resource_cache:
        data, timestamp = resource_cache[uri]
        if time.time() - timestamp < CACHE_TTL:
            return data
    
    # Fetch fresh data
    if uri.startswith("file://"):
        path = uri.replace("file://", "")
        with open(path) as f:
            data = f.read()
    elif uri.startswith("api://"):
        data = await fetch_from_api(uri)
    else:
        raise ValueError(f"Unknown resource type: {uri}")
    
    # Cache result
    resource_cache[uri] = (data, time.time())
    return data
```

---

## 5. Testing Patterns

### 5.1 Unit Testing Tools

```python
"""Test tool definitions and behavior"""
import pytest
from mcp.types import Tool

def test_list_tools_returns_expected_tools():
    """Test that tool listing returns correct tools"""
    # Create server
    server = create_test_server()
    
    # Get tools
    tools = asyncio.run(server.list_tools())
    
    # Verify
    assert len(tools) == 2
    assert any(t.name == "get_weather" for t in tools)
    assert any(t.name == "get_forecast" for t in tools)

def test_tool_schema_validation():
    """Test tool input schema"""
    server = create_test_server()
    
    tools = asyncio.run(server.list_tools())
    weather_tool = next(t for t in tools if t.name == "get_weather")
    
    # Verify schema
    assert "city" in weather_tool.inputSchema["properties"]
    assert "city" in weather_tool.inputSchema["required"]

@pytest.mark.asyncio
async def test_call_tool_with_valid_input():
    """Test tool execution with valid input"""
    server = create_test_server()
    
    result = await server.call_tool(
        "get_weather",
        {"city": "London"}
    )
    
    assert len(result) == 1
    assert "London" in result[0].text

@pytest.mark.asyncio
async def test_call_tool_with_invalid_input():
    """Test tool execution with invalid input"""
    server = create_test_server()
    
    with pytest.raises(ValueError):
        await server.call_tool("get_weather", {})
```

### 5.2 Integration Testing

```python
"""Integration test with MCP client"""
import pytest
from mcp import Client

@pytest.mark.asyncio
async def test_server_client_integration():
    """Test full server-client communication"""
    # Start server
    server_process = await start_server()
    
    try:
        # Connect client
        async with Client("test-server") as client:
            # List tools
            tools = await client.list_tools()
            assert len(tools) > 0
            
            # Call tool
            result = await client.call_tool(
                "get_weather",
                {"city": "Paris"}
            )
            assert "Paris" in result[0].text
    
    finally:
        # Cleanup
        server_process.terminate()
        await server_process.wait()
```

---

## 6. Configuration Patterns

### 6.1 Environment-Based Configuration

```python
"""Environment-based server configuration"""
import os
from dataclasses import dataclass

@dataclass
class Config:
    # Server settings
    server_name: str = os.getenv("MCP_SERVER_NAME", "default-server")
    log_level: str = os.getenv("MCP_LOG_LEVEL", "INFO")
    
    # External services
    api_url: str = os.getenv("API_URL", "http://localhost:8000")
    api_key: str = os.getenv("API_KEY", "")
    
    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "mcp")
    
    # Rate limiting
    rate_limit_calls: int = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

config = Config()
```

### 6.2 YAML Configuration

```python
"""YAML-based server configuration"""
import yaml
from pathlib import Path

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    path = Path(config_path)
    
    if not path.exists():
        # Return defaults
        return {
            "server": {"name": "default"},
            "tools": [],
            "logging": {"level": "INFO"}
        }
    
    with open(path) as f:
        return yaml.safe_load(f)

# Usage
config = load_config("server-config.yaml")
```

---

## Summary

These patterns provide:

1. **Server Patterns** - Minimal, factory-based implementations
2. **Tool Patterns** - Validation, async, cached tools
3. **Error Handling** - Graceful degradation, retry logic
4. **Resource Patterns** - Dynamic listing, caching
5. **Testing Patterns** - Unit and integration tests
6. **Configuration** - Environment and YAML-based config

---

## References

- [MCP SDK Documentation](https://modelcontextprotocol.io/docs)
- [Pydantic Validation](https://pydantic.dev/)
- [Python Async Patterns](https://docs.python.org/3/library/asyncio.html)