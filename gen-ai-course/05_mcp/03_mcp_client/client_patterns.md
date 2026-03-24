# MCP Client Implementation Patterns

This document provides implementation patterns and code examples for building robust MCP clients.

---

## 1. Client Patterns

### 1.1 Simple Client Pattern

```python
"""Simple client - Quick start"""
import asyncio
from mcp import Client

async def main():
    async with Client("my-server") as client:
        # List tools
        tools = await client.list_tools()
        
        # Call tool
        result = await client.call_tool("hello", {"name": "World"})
        print(result[0].text)

asyncio.run(main())
```

### 1.2 Manager Pattern

```python
"""Client manager for multiple servers"""
import asyncio
from mcp import Client
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ServerConfig:
    name: str
    command: list
    timeout: int = 30

class ClientManager:
    """Manage multiple MCP server connections"""
    
    def __init__(self):
        self.clients: Dict[str, Client] = {}
    
    async def add_server(self, config: ServerConfig) -> Client:
        """Add and connect to a server"""
        client = Client(config.name)
        await client.connect()
        self.clients[config.name] = client
        return client
    
    async def remove_server(self, name: str):
        """Remove and disconnect a server"""
        if name in self.clients:
            await self.clients[name].close()
            del self.clients[name]
    
    def get_client(self, name: str) -> Optional[Client]:
        """Get client by name"""
        return self.clients.get(name)
    
    async def close_all(self):
        """Close all connections"""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()

# Usage
async def main():
    manager = ClientManager()
    
    try:
        await manager.add_server(ServerConfig(
            name="weather",
            command=["python", "weather_server.py"]
        ))
        
        weather = manager.get_client("weather")
        result = await weather.call_tool("get_weather", {"city": "NYC"})
        
    finally:
        await manager.close_all()

asyncio.run(main())
```

---

## 2. Error Handling Patterns

### 2.1 Retry Pattern

```python
"""Retry pattern for transient failures"""
import asyncio
from typing import TypeVar, Callable, Any
from functools import wraps

T = TypeVar('T')

async def with_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> T:
    """Retry async function with exponential backoff"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = delay * (backoff ** attempt)
                await asyncio.sleep(wait_time)
    
    raise last_exception

# Usage
async def call_with_retry(client: Client, tool: str, args: dict):
    return await with_retry(
        lambda: client.call_tool(tool, args),
        max_retries=3,
        delay=1.0
    )
```

### 2.2 Circuit Breaker Pattern

```python
"""Circuit breaker for fault tolerance"""
import asyncio
import time
from enum import Enum
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

class CircuitBreaker:
    """Circuit breaker for MCP client"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        
        # Half-open state
        return self.success_count < self.config.half_open_max_calls
    
    def record_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.half_open_max_calls:
                self.state = CircuitState.CLOSED
        elif self.state == CircuitState.CLOSED:
            pass
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
class ResilientClient:
    def __init__(self, server_name: str, command: list):
        self.client = Client(server_name)
        self.breaker = CircuitBreaker(CircuitBreakerConfig())
    
    async def call_tool(self, name: str, args: dict):
        if not self.breaker.can_execute():
            raise Exception("Circuit breaker is open")
        
        try:
            result = await self.client.call_tool(name, args)
            self.breaker.record_success()
            return result
        except Exception as e:
            self.breaker.record_failure()
            raise
```

### 2.3 Fallback Pattern

```python
"""Fallback pattern for graceful degradation"""
import asyncio
from typing import Optional, Callable, Any

class FallbackClient:
    """Client with fallback capabilities"""
    
    def __init__(self, primary_client: Client, fallback_fn: Callable):
        self.primary = primary_client
        self.fallback = fallback_fn
    
    async def call_tool(self, name: str, args: dict) -> list:
        """Try primary, fallback on failure"""
        try:
            return await self.primary.call_tool(name, args)
        except Exception as e:
            # Try fallback
            if callable(self.fallback):
                return await self.fallback(name, args)
            raise
```

---

## 3. Caching Patterns

### 3.1 Tool Result Caching

```python
"""Cache tool results"""
import asyncio
import time
import hashlib
import json
from typing import Any, Optional

class ToolCache:
    """Cache for tool results"""
    
    def __init__(self, ttl: int = 300):
        self.cache: dict = {}
        self.ttl = ttl
    
    def _make_key(self, tool_name: str, args: dict) -> str:
        """Create cache key"""
        data = json.dumps({"tool": tool_name, "args": args}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def get_or_call(self, client: Client, tool: str, args: dict) -> list:
        """Get cached result or call tool"""
        key = self._make_key(tool, args)
        
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
        
        # Call tool
        result = await client.call_tool(tool, args)
        
        # Cache result
        self.cache[key] = (result, time.time())
        
        return result
    
    def invalidate(self, tool_name: Optional[str] = None):
        """Invalidate cache"""
        if tool_name:
            # Remove specific tool entries
            keys_to_remove = [
                k for k in self.cache 
                if tool_name in k
            ]
            for k in keys_to_remove:
                del self.cache[k]
        else:
            self.cache.clear()

# Usage
async def main():
    cache = ToolCache(ttl=300)
    async with Client("my-server") as client:
        result = await cache.get_or_call(client, "get_data", {"id": 1})
```

---

## 4. Testing Patterns

### 4.1 Mock Server Testing

```python
"""Test client with mock server"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from mcp import Client

@pytest.mark.asyncio
async def test_client_with_mock():
    """Test client using mock server"""
    # Create mock
    mock_client = AsyncMock()
    mock_client.list_tools = AsyncMock(return_value=[
        MagicMock(name="test_tool", description="Test tool")
    ])
    mock_client.call_tool = AsyncMock(return_value=[
        MagicMock(text="Test result")
    ])
    
    # Use mock
    tools = await mock_client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"
    
    result = await mock_client.call_tool("test_tool", {"arg": "value"})
    assert "Test result" in result[0].text

@pytest.mark.asyncio
async def test_client_integration():
    """Integration test with real server"""
    # This would need a test server running
    pass
```

### 4.2 Fixtures for Testing

```python
"""Pytest fixtures for MCP testing"""
import pytest
import asyncio
from mcp import Client
from mcp.client import StdioConnection

@pytest.fixture
def server_command():
    """Server command for testing"""
    return ["python", "tests/fixtures/server.py"]

@pytest.fixture
async def client(server_command):
    """Client fixture"""
    connection = StdioConnection(server_command)
    client = Client("test-server", connection)
    await client.connect()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_list_tools(client):
    """Test tool listing"""
    tools = await client.list_tools()
    assert len(tools) > 0

@pytest.mark.asyncio
async def test_call_tool(client):
    """Test tool calling"""
    result = await client.call_tool("echo", {"message": "hello"})
    assert "hello" in result[0].text
```

---

## 5. Monitoring Patterns

### 5.1 Metrics Collection

```python
"""Metrics collection for client"""
import time
from dataclasses import dataclass, field
from typing import Dict, List
import asyncio

@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    tool_name: str
    start_time: float
    end_time: float
    success: bool
    error: str = ""

class MetricsCollector:
    """Collect client metrics"""
    
    def __init__(self):
        self.requests: List[RequestMetrics] = []
        self.lock = asyncio.Lock()
    
    async def record_request(
        self,
        tool_name: str,
        start_time: float,
        end_time: float,
        success: bool,
        error: str = ""
    ):
        """Record a request"""
        async with self.lock:
            self.requests.append(RequestMetrics(
                tool_name=tool_name,
                start_time=start_time,
                end_time=end_time,
                success=success,
                error=error
            ))
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        if not self.requests:
            return {"total": 0, "success_rate": 0, "avg_latency": 0}
        
        total = len(self.requests)
        successes = sum(1 for r in self.requests if r.success)
        total_latency = sum(r.end_time - r.start_time for r in self.requests)
        
        return {
            "total_requests": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": successes / total if total > 0 else 0,
            "avg_latency": total_latency / total if total > 0 else 0
        }

# Usage
class MonitoredClient:
    def __init__(self, client: Client):
        self.client = client
        self.metrics = MetricsCollector()
    
    async def call_tool(self, name: str, args: dict) -> list:
        start = time.time()
        try:
            result = await self.client.call_tool(name, args)
            await self.metrics.record_request(name, start, time.time(), True)
            return result
        except Exception as e:
            await self.metrics.record_request(
                name, start, time.time(), False, str(e)
            )
            raise
```

### 5.2 Structured Logging

```python
"""Structured logging for client"""
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class StructuredLogger:
    """Structured logging for MCP client"""
    
    @staticmethod
    def log_request(tool: str, args: dict, result: Any):
        """Log tool request"""
        logger.info(json.dumps({
            "event": "tool_request",
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool,
            "args": args,
            "result_size": len(str(result))
        }))
    
    @staticmethod
    def log_error(tool: str, error: Exception):
        """Log error"""
        logger.error(json.dumps({
            "event": "tool_error",
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool,
            "error": str(error),
            "error_type": type(error).__name__
        }))

# Usage
async def main():
    async with Client("my-server") as client:
        try:
            result = await client.call_tool("get_data", {"id": 1})
            StructuredLogger.log_request("get_data", {"id": 1}, result)
        except Exception as e:
            StructuredLogger.log_error("get_data", e)
```

---

## 6. Authentication Patterns

### 6.1 API Key Authentication

```python
"""API key authentication"""
import asyncio
from mcp import Client

class AuthenticatedClient:
    """Client with API key authentication"""
    
    def __init__(self, server_name: str, command: list, api_key: str):
        self.api_key = api_key
        self.client = Client(server_name)
    
    async def call_tool(self, name: str, args: dict) -> list:
        # Add auth to arguments
        args["_auth"] = self.api_key
        return await self.client.call_tool(name, args)
```

### 6.2 OAuth Authentication

```python
"""OAuth authentication"""
import asyncio
from mcp import Client

class OAuthClient:
    """Client with OAuth authentication"""
    
    def __init__(self, server_name: str, command: list, token_url: str, client_id: str, client_secret: str):
        self.server_name = server_name
        self.command = command
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
    
    async def _get_token(self) -> str:
        """Get OAuth token"""
        if self._token:
            return self._token
        
        # In production, implement actual OAuth flow
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as resp:
                data = await resp.json()
                self._token = data["access_token"]
                return self._token
    
    async def call_tool(self, name: str, args: dict) -> list:
        token = await self._get_token()
        
        connection = StdioConnection(
            self.command,
            env={"MCP_AUTH_TOKEN": token}
        )
        client = Client(self.server_name, connection)
        
        return await client.call_tool(name, args)
```

---

## Summary

These patterns provide:

1. **Client Patterns** - Manager, simple client implementations
2. **Error Handling** - Retry, circuit breaker, fallback
3. **Caching** - Tool result caching
4. **Testing** - Mock testing, fixtures
5. **Monitoring** - Metrics, structured logging
6. **Authentication** - API key, OAuth

---

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Python Async Patterns](https://docs.python.org/3/library/asyncio.html)
- [Circuit Breaker Pattern](https://docs.microsoft.com/en-us/architecture/patterns/circuit-breaker)