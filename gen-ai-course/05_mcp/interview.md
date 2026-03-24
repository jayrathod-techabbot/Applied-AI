# Model Context Protocol (MCP) - Interview Questions

This document contains interview questions and answers covering Module 5: Model Context Protocol (MCP).

---

## 1. MCP Overview

### Q1: What is the Model Context Protocol (MCP)?

**Answer:** MCP is a standardized protocol that enables LLMs to interact with external tools, services, and data sources. It provides:

- **Standard Interface:** Consistent way for AI models to access tools
- **Tool Discovery:** Models can discover available capabilities
- **Resource Management:** Access to data and files
- **State Management:** Maintain context across interactions

Think of it as a "USB-C for AI" - a universal port for connecting AI to anything.

---

### Q2: Why do we need a standard interface between LLMs and tools?

**Answer:** Need for standardization:

- **Current Problem:** Each tool requires custom integration
- **Scalability:** Hard to add new tools
- **Portability:** Locked into specific frameworks
- **Developer Experience:**重复 work for each integration

MCP solves this by providing a universal standard.

---

### Q3: What are the core components of MCP?

**Answer:** Core components:

- **MCP Server:** Provides tools, resources, prompts
- **MCP Client:** Connects to servers, makes requests
- **Transport Layer:** Communication (stdio, HTTP)
- **Message Protocol:** JSON-RPC based messages

---

## 2. MCP Servers

### Q4: What are MCP Servers?

**Answer:** MCP Servers are:

- **Expose Tools:** Functions the AI can call
- **Provide Resources:** Data the AI can read
- **Define Prompts:** Reusable prompt templates
- **Examples:**
  - Weather API server
  - Database server
  - Filesystem server
  - Finance API server

---

### Q5: How do you create an MCP Server?

**Answer:** Creation steps:

1. **Define Tools:** Create functions with descriptions
2. **Tool Registration:** Register with MCP server
3. **Run Server:** Start listening for requests

```python
from mcp.server import Server
from mcp.types import Tool

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_weather",
            description="Get weather for a location",
            inputSchema={"type": "object", "properties": {"location": {"type": "string"}}}
        )
    ]
```

---

### Q6: What are examples of MCP Servers?

**Answer:** Example servers:

- **Weather API:** Get weather data for locations
- **UK Carbon Intensity:** Carbon emissions data
- **Database Server:** SQL query execution
- **Filesystem:** Read/write files
- **Finance API:** Stock prices, company data
- **GitHub:** Repository management

---

### Q7: How do you run an MCP Server?

**Answer:** Running:

1. **Install Package:** `pip install mcp`
2. **Configure:** Set transport (stdio or SSE)
3. **Run Command:** Start the server process
4. **Connect Client:** Connect to use tools

```bash
python my_server.py
# or
mcp run my_server
```

---

## 3. MCP Client

### Q8: What is an MCP Client?

**Answer:** MCP Client:

- **Connects to Servers:** Initiates connections
- **Sends Requests:** Calls tools on servers
- **Receives Results:** Gets tool outputs
- **Manages Sessions:** Maintains connections

Used in AI applications to access external capabilities.

---

### Q9: How do you create an MCP Client?

**Answer:** Client creation:

```python
from mcp import Client

# Connect to server
client = Client("my-server")

# List available tools
tools = await client.list_tools()

# Call a tool
result = await client.call_tool("get_weather", {"location": "London"})
```

---

### Q10: How do you test an MCP Client?

**Answer:** Testing:

1. **Unit Tests:** Test tool definitions
2. **Integration Tests:** Test server-client communication
3. **Mock Server:** Use mock for testing
4. **Error Handling:** Test edge cases

---

## Technical Deep-Dive

### Q11: What transport layers does MCP support?

**Answer:** Transport types:

- **Stdio:** Local process communication (most common)
- **SSE (Server-Sent Events):** HTTP-based streaming
- **HTTP:** REST-like communication

Choice depends on deployment scenario.

---

### Q12: What is the MCP message format?

**Answer:** Message format:

- **JSON-RPC 2.0:** Standard JSON-RPC protocol
- **Methods:**
  - `initialize`: Start session
  - `tools/list`: Get available tools
  - `tools/call`: Execute a tool
  - `resources/list`: Get available resources

---

### Q13: How does tool definition work in MCP?

**Answer:** Tool definition:

```json
{
  "name": "get_weather",
  "description": "Get current weather",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name"
      }
    },
    "required": ["location"]
  }
}
```

---

## Architecture Questions

### Q14: How does MCP fit into an agent architecture?

**Answer:** Architecture integration:

```
┌─────────────┐
│    LLM     │
└──────┬──────┘
       │
┌──────▼──────┐
│  MCP Client │
└──────┬──────┘
       │
┌──────▼──────┐
│  MCP Server │ → Tools, Resources
└─────────────┘
```

MCP provides the bridge between AI and external capabilities.

---

### Q15: What is the difference between MCP and function calling?

**Answer:**

| Aspect | MCP | Function Calling |
|--------|-----|------------------|
| Standard | Universal | Provider-specific |
| Discovery | Dynamic | Static definitions |
| Resources | Yes | No |
| State | Session-based | Per-call |
| Use Case | General | LLM-specific |

---

### Q16: How do you secure MCP communications?

**Answer:** Security:

- **Authentication:** API keys or tokens
- **Authorization:** Limit tool access
- **Input Validation:** Sanitize all inputs
- **Audit Logging:** Track all tool calls
- **Encryption:** TLS for network transport

---

## Production Questions

### Q17: How do you debug MCP server issues?

**Answer:** Debugging:

1. **Check Server Logs:** Error messages
2. **Verify Tool Definitions:** Schema validation
3. **Test Transport:** Ensure communication works
4. **Client Tracing:** See what's being sent
5. **Mock Responses:** Test without real server

---

### Q18: What are best practices for MCP server design?

**Answer:** Best practices:

- **Clear Tool Names:** Descriptive, consistent
- **Detailed Descriptions:** Help the LLM understand when to use
- **Proper Error Handling:** Return meaningful errors
- **Idempotency:** Same input = same output
- **Timeouts:** Don't hang indefinitely

---

### Q19: How do you handle MCP server failures?

**Answer:** Failure handling:

- **Connection Retry:** Automatic reconnection
- **Fallback Tools:** Alternative approaches
- **Graceful Degradation:** Continue without unavailable tools
- **Monitoring:** Alert on failures
- **Circuit Breaker:** Stop calling failing servers

---

## Scenario Questions

### Q20: How would you build a weather MCP server?

**Answer:** Implementation:

1. **Define Tool:** `get_weather(location)`
2. **API Integration:** Connect to weather API
3. **Error Handling:** Handle invalid locations
4. **Caching:** Cache results to reduce API calls
5. **Rate Limiting:** Respect API limits

---

### Q21: How do you connect an MCP server to a database?

**Answer:** Database connection:

```python
@server.list_tools()
async def list_tools():
    return [Tool(
        name="query_db",
        description="Run SQL query",
        inputSchema={...}
    )]

@server.call_tool()
async def call_tool(name, arguments):
    if name == "query_db":
        return run_query(arguments["sql"])
```

---

## Summary

Key MCP topics:

1. **Overview:** What is MCP, why it matters
2. **Servers:** Creating and running MCP servers
3. **Clients:** Connecting to and using servers
4. **Security:** Protecting MCP communications
5. **Production:** Debugging, failure handling

---

## References

- [MCP Specification](references.md)
- [MCP Server Examples](references.md)
- [MCP Client SDK](references.md)

---

## Enterprise-Level Questions

### Q22: How do you implement authentication in MCP servers?

**Answer:** Authentication implementation:

```python
from mcp.server import Server
from functools import wraps

# API Key authentication
API_KEYS = {"key1": "client1", "key2": "client2"}

def authenticate(func):
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        # Extract API key from request
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise PermissionError("No authorization header")
        
        api_key = auth_header.replace("Bearer ", "")
        if api_key not in API_KEYS:
            raise PermissionError("Invalid API key")
        
        return await func(request, *args, **kwargs)
    return wrapper

# Usage
@server.call_tool()
@authenticate
async def call_tool(name: str, arguments: dict):
    # Tool implementation
    pass
```

---

### Q23: What are the best practices for MCP server performance?

**Answer:** Performance best practices:

| Practice | Description |
|----------|-------------|
| **Connection Pooling** | Reuse connections to reduce overhead |
| **Caching** | Cache frequently accessed data |
| **Async Operations** | Use async/await for I/O operations |
| **Rate Limiting** | Prevent abuse with rate limits |
| **Resource Limits** | Limit memory and execution time |

```python
# Caching example
from functools import lru_cache
import time

cache = {}
CACHE_TTL = 300

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    key = f"{name}:{json.dumps(arguments)}"
    
    if key in cache:
        result, timestamp = cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return result
    
    result = await execute_tool(name, arguments)
    cache[key] = (result, time.time())
    return result
```

---

### Q24: How do you handle MCP server failures and resilience?

**Answer:** Resilience patterns:

1. **Circuit Breaker** - Stop calling failing servers
2. **Retry with Backoff** - Exponential backoff for transient failures
3. **Fallback** - Use alternative tools when primary fails
4. **Timeout** - Set reasonable timeouts

```python
# Retry with exponential backoff
import asyncio

async def retry_call(client, tool, args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.call_tool(tool, args)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait)

# Circuit breaker
class CircuitBreaker:
    def __init__(self, threshold=5):
        self.failures = 0
        self.threshold = threshold
        self.state = "closed"
    
    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "open"
```

---

### Q25: How do you secure MCP communications in production?

**Answer:** Security measures:

- **TLS/SSL** - Encrypt all network communication
- **API Keys** - Token-based authentication
- **Input Validation** - Sanitize all tool inputs
- **Rate Limiting** - Prevent abuse
- **Audit Logging** - Log all requests and responses
- **IP Whitelisting** - Restrict access to known IPs

```python
# Security configuration
SECURITY_CONFIG = {
    "tls_enabled": True,
    "require_api_key": True,
    "rate_limit": {
        "calls_per_minute": 100,
        "burst": 20
    },
    "allowed_ips": ["10.0.0.0/8", "192.168.0.0/16"]
}
```

---

### Q26: How do you monitor MCP servers in production?

**Answer:** Monitoring strategy:

| Metric | Description | Tools |
|--------|-------------|-------|
| **Request Rate** | Calls per second | Prometheus |
| **Latency** | Response time | Grafana |
| **Error Rate** | Failed requests | Datadog |
| **Tool Usage** | Popular tools | Custom dashboard |
| **Resource Usage** | CPU, Memory | CloudWatch |

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram

request_counter = Counter('mcp_requests_total', 'Total MCP requests')
latency_histogram = Histogram('mcp_request_latency', 'Request latency')

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    start = time.time()
    try:
        result = await execute_tool(name, arguments)
        request_counter.labels(tool=name, status='success').inc()
        return result
    finally:
        latency_histogram.observe(time.time() - start)
```

---

### Q27: How do you scale MCP servers horizontally?

**Answer:** Horizontal scaling approach:

```
┌─────────────────────────────────────────────────────────────┐
│                   LOAD BALANCER                             │
│                    (nginx/haproxy)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ MCP     │  │ MCP     │  │ MCP     │  │ MCP     │
   │ Server 1│  │ Server 2│  │ Server 3│  │ Server 4│
   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                      ┌──────▼──────┐
                      │  Shared     │
                      │  State      │
                      │  (Redis)    │
                      └─────────────┘
```

Implementation:
1. Use stateless servers with shared state
2. Implement sticky sessions if needed
3. Use connection pooling
4. Deploy behind load balancer

---

### Q28: How do you implement MCP server logging and tracing?

**Answer:** Logging implementation:

```python
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Structured logging
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    logger.info(json.dumps({
        "event": "tool_call",
        "timestamp": datetime.utcnow().isoformat(),
        "tool": name,
        "args": arguments
    }))
    
    try:
        result = await execute_tool(name, arguments)
        logger.info(json.dumps({
            "event": "tool_success",
            "tool": name,
            "duration_ms": duration
        }))
        return result
    except Exception as e:
        logger.error(json.dumps({
            "event": "tool_error",
            "tool": name,
            "error": str(e)
        }))
        raise
```

---

### Q29: What are the differences between MCP transport mechanisms?

**Answer:** Transport comparison:

| Transport | Use Case | Pros | Cons |
|-----------|----------|------|------|
| **Stdio** | Local processes | Simple, secure | No network access |
| **SSE** | Web apps | Real-time, HTTP | Complex setup |
| **HTTP** | REST APIs | Familiar, scalable | More overhead |

```python
# Stdio transport (most common for local)
from mcp.server.stdio import stdio_server

async with stdio_server() as streams:
    await app.run(streams[0], streams[1], options)

# SSE transport for web
from mcp.server.sse import SseServerTransport

transport = SseServerTransport("/mcp")
async with serve(app, transport) as server:
    await server.serve()
```

---

### Q30: How do you test MCP servers and clients?

**Answer:** Testing strategy:

```python
# Unit tests
import pytest

@pytest.mark.asyncio
async def test_tool_execution():
    server = create_test_server()
    result = await server.call_tool("add", {"a": 1, "b": 2})
    assert result[0].text == "3"

@pytest.mark.asyncio
async def test_tool_schema():
    server = create_test_server()
    tools = await server.list_tools()
    assert any(t.name == "add" for t in tools)

# Integration tests
@pytest.mark.asyncio
async def test_server_client():
    # Start server
    proc = await asyncio.create_subprocess_exec(
        "python", "server.py",
        stdout=asyncio.subprocess.PIPE
    )
    
    # Connect client
    async with Client("test") as client:
        result = await client.call_tool("test", {})
        assert result
    
    proc.terminate()
```

---

### Q31: How do you handle MCP protocol versioning?

**Answer:** Version handling:

```python
# Server side - advertise version
app = Server("my-server")

@app.list_tools()
async def list_tools():
    return tools

# Client side - check version during initialize
async with Client("my-server") as client:
    # Initialize with version negotiation
    await client.initialize(
        protocol_version="1.0.0",
        capabilities={"tools": True, "resources": True}
    )
    
    # Check server capabilities
    server_info = client.server_info
```

---

### Q32: What are common MCP anti-patterns to avoid?

**Answer:** Anti-patterns:

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| **Large tool schemas** | Hard to parse | Keep schemas simple |
| **No error handling** | Poor UX | Return meaningful errors |
| **Synchronous calls** | Blocking | Use async/await |
| **No input validation** | Security risk | Validate all inputs |
| **Missing timeouts** | Hanging requests | Set reasonable timeouts |

---

### Q33: How do you migrate from custom integrations to MCP?

**Answer:** Migration strategy:

1. **Inventory** - List all current integrations
2. **Prioritize** - Start with simple integrations
3. **Wrapper** - Create MCP wrapper for existing services
4. **Migrate** - Replace custom code with MCP calls
5. **Validate** - Test functionality
6. **Iterate** - Move more integrations

```python
# Wrap existing service as MCP
class LegacyServiceWrapper:
    def __init__(self, legacy_service):
        self.service = legacy_service
    
    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="legacy_api",
                description="Legacy API wrapper",
                inputSchema={...}
            )
        ]
    
    @app.call_tool()
    async def call_tool(name, arguments):
        # Call legacy service
        result = self.service.execute(name, arguments)
        return [TextContent(type="text", text=str(result))]
```

---

### Q34: How do you implement MCP in a microservices architecture?

**Answer:** Microservices integration:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / BFF                        │
│                    (MCP Client)                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
     ▼                    ▼                    ▼
┌─────────┐         ┌─────────┐         ┌─────────┐
│  User   │         │  Order  │         │  Payment│
│ Service │         │ Service │         │ Service │
│ (MCP)   │         │ (MCP)   │         │ (MCP)   │
└─────────┘         └─────────┘         └─────────┘
```

Implementation:
- Each microservice exposes MCP server
- API Gateway/BFF acts as MCP client
- Single entry point for AI applications
- Service-to-service communication via MCP

---

### Q35: What is the future roadmap for MCP?

**Answer:** MCP roadmap directions:

- **Enhanced Security** - Built-in OAuth, mTLS support
- **Better Tool Discovery** - Semantic tool matching
- **Multi-modal Support** - Image, audio tool support
- **Standardized Prompts** - Prompt library ecosystem
- **Performance** - Binary protocol, compression
- **Ecosystem Growth** - More servers, better tooling

---

## Quick Reference

### MCP Methods

| Method | Direction | Description |
|--------|-----------|-------------|
| `initialize` | Client→Server | Start session |
| `tools/list` | Client→Server | Get available tools |
| `tools/call` | Client→Server | Execute tool |
| `resources/list` | Client→Server | Get available resources |
| `resources/read` | Client→Server | Read resource |
| `prompts/list` | Client→Server | Get available prompts |
| `prompts/get` | Client→Server | Get prompt content |

### Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32000 | Auth error |

---

End of Interview Questions
