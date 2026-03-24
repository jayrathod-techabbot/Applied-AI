# MCP Architecture Diagram

This document contains ASCII diagrams to visualize MCP architecture and message flows.

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP ECOSYSTEM                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────┐
                              │  AI Application  │
                              │  (Claude, GPT,   │
                              │   Gemini, etc.)  │
                              └────────┬─────────┘
                                       │
                                       ▼
                    ┌────────────────────────────────┐
                    │         MCP Client             │
                    │  ┌──────────────────────────┐  │
                    │  │ • Session Management     │  │
                    │  │ • Tool Discovery         │  │
                    │  │ • Request/Response       │  │
                    │  │ • Connection Pooling     │  │
                    │  └──────────────────────────┘  │
                    └───────────────┬────────────────┘
                                    │
                                    ▼
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                     PROTOCOL LAYER (JSON-RPC 2.0)                  ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║  Messages: initialize, tools/list, tools/call, resources/list      ║
    ╚═══════════════════════════════════════════════════════════════════╝
                                    │
                    ┌───────────────┴────────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │   Stdio Transport │           │  SSE/HTTP Trans  │
        │   (Local Process) │           │  (Network Stream) │
        └───────────────────┘           └───────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                         SERVICE LAYER                              ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            ║
    ║    │   Weather   │  │   Database  │  │  Filesystem │            ║
    ║    │   Server    │  │   Server    │  │   Server    │            ║
    ║    └─────────────┘  └─────────────┘  └─────────────┘            ║
    ║         │                │                │                       ║
    ║         ▼                ▼                ▼                       ║
    ║    ┌─────────┐     ┌─────────┐     ┌─────────┐                  ║
    ║    │External │     │   SQL   │     │   OS    │                  ║
    ║    │   API   │     │   DB    │     │  Files  │                  ║
    ║    └─────────┘     └─────────┘     └─────────┘                  ║
    ║                                                                   ║
    └───────────────────────────────────────────────────────────────────┘
```

---

## 2. MCP Server Internal Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MCP SERVER INTERNAL STRUCTURE                    │
└─────────────────────────────────────────────────────────────────────────┘

    ┌───────────────────────────────────────────────────────────────────┐
    │                         MCP Server                                │
    ├───────────────────────────────────────────────────────────────────┤
    │                                                                    │
    │  ┌─────────────────────────────────────────────────────────────┐  │
    │  │                    Request Handler                           │  │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
    │  │  │ initialize  │  │  tools/list │  │ tools/call  │          │  │
    │  │  │   handler   │  │   handler   │  │   handler  │          │  │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘          │  │
    │  └─────────────────────────────────────────────────────────────┘  │
    │                              │                                     │
    │                              ▼                                     │
    │  ┌─────────────────────────────────────────────────────────────┐  │
    │  │                      Tool Registry                          │  │
    │  │  ┌──────────────────────────────────────────────────────┐   │  │
    │  │  │  Tool 1: get_weather    │ Tool 2: query_database     │   │  │
    │  │  │  Tool 3: read_file     │ Tool 4: send_email         │   │  │
    │  │  └──────────────────────────────────────────────────────┘   │  │
    │  └─────────────────────────────────────────────────────────────┘  │
    │                              │                                     │
    │                              ▼                                     │
    │  ┌─────────────────────────────────────────────────────────────┐  │
    │  │                     Business Logic                          │  │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
    │  │  │  API Client │  │   DB Driver │  │  FS Handler │        │  │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘        │  │
    │  └─────────────────────────────────────────────────────────────┘  │
    │                              │                                     │
    │                              ▼                                     │
    │  ┌─────────────────────────────────────────────────────────────┐  │
    │  │                    External Services                       │  │
    │  │   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐       │  │
    │  │   │Weather │   │PostgreSQL│ │  S3    │   │  SMTP  │       │  │
    │  │   │  API   │   │   DB    │   │Bucket │   │Server  │       │  │
    │  │   └────────┘   └────────┘   └────────┘   └────────┘       │  │
    │  └─────────────────────────────────────────────────────────────┘  │
    │                                                                    │
    └───────────────────────────────────────────────────────────────────┘
```

---

## 3. Message Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MCP MESSAGE FLOW                                  │
└─────────────────────────────────────────────────────────────────────────┘

Client                              Server
  │                                    │
  │  1. initialize request            │
  ├───────────────────────────────────►│
  │                                    │ 2. Process initialization
  │                                    │ 3. Load server capabilities
  │                                    │
  │  4. initialize response           │
  │◄───────────────────────────────────┤
  │    (server info, protocol version) │
  │                                    │
  │  5. tools/list request            │
  ├───────────────────────────────────►│
  │                                    │ 6. Get available tools
  │                                    │
  │  7. tools/list response           │
  │◄───────────────────────────────────┤
  │    (list of tool definitions)      │
  │                                    │
  │  8. LLM decides to call tool      │
  │                                    │
  │  9. tools/call request            │
  ├───────────────────────────────────►│
  │    (tool name, arguments)         │ 10. Validate arguments
  │                                    │ 11. Execute tool logic
  │                                    │ 12. Call external service
  │                                    │
  │ 13. tools/call response           │
  │◄───────────────────────────────────┤
  │    (tool result, errors)           │
  │                                    │
  │ 14. LLM generates response        │
  ▼                                    ▼


DETAILED MESSAGE EXAMPLES:

┌────────────────────────────────────────────────────────────────────┐
│  TOOLS/LIST REQUEST                                                │
├────────────────────────────────────────────────────────────────────┤
│  {                                                                 │
│    "jsonrpc": "2.0",                                              │
│    "id": 1,                                                       │
│    "method": "tools/list"                                        │
│  }                                                                 │
└────────────────────────────────────────────────────────────────────┘
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  TOOLS/LIST RESPONSE                                               │
├────────────────────────────────────────────────────────────────────┤
│  {                                                                 │
│    "jsonrpc": "2.0",                                              │
│    "id": 1,                                                       │
│    "result": {                                                    │
│      "tools": [                                                  │
│        {                                                          │
│          "name": "get_weather",                                  │
│          "description": "Get weather for a location",            │
│          "inputSchema": {                                        │
│            "type": "object",                                     │
│            "properties": {                                      │
│              "location": {"type": "string"}                     │
│            },                                                    │
│            "required": ["location"]                              │
│          }                                                        │
│        }                                                          │
│      ]                                                            │
│    }                                                              │
│  }                                                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Resource Management Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       RESOURCE MANAGEMENT FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

Client                              Server
  │                                    │
  │  1. resources/list request         │
  ├───────────────────────────────────►│
  │                                    │ 2. Scan available resources
  │                                    │
  │  3. resources/list response       │
  │◄───────────────────────────────────┤
  │    (list of available resources)  │
  │                                    │
  │  4. resources/read request        │
  │    (resource URI: file:///data/)  │
  ├───────────────────────────────────►│
  │                                    │ 5. Validate resource URI
  │                                    │ 6. Read resource content
  │                                    │
  │  7. resources/read response       │
  │◄───────────────────────────────────┤
  │    (resource content, mime type)  │
  │                                    │
  ▼                                    ▼


RESOURCE TYPES:

┌─────────────────────────────────────────────────────────────────────────┐
│  Resource URI Examples                                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  file:///path/to/file.txt         - Local file                         │
│  database://table/rows           - Database query result              │
│  api://endpoint/data             - API response                        │
│  s3://bucket/key                 - S3 object                          │
│  secret://api-key                - Secret/value (masked)              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Enterprise Multi-Server Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE MCP DEPLOYMENT                            │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   Load Balancer  │
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
    │  MCP Gateway    │      │  MCP Gateway    │      │  MCP Gateway    │
    │  (Server 1)     │      │  (Server 2)     │      │  (Server N)     │
    └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
             │                        │                        │
    ┌────────┴────────┐      ┌───────┴────────┐      ┌───────┴────────┐
    │                 │      │                 │      │                 │
    ▼                 ▼      ▼                 ▼      ▼                 ▼
┌────────┐      ┌────────┐  ┌────────┐      ┌────────┐  ┌────────┐      ┌────────┐
│Weather │      │Database│  │Weather │      │Database│  │Weather │      │Database│
│Server  │      │Server  │  │Server  │      │Server  │  │Server  │      │Server  │
└────────┘      └────────┘  └────────┘      └────────┘  └────────┘      └────────┘

SERVICE LAYER:
┌─────────────────────────────────────────────────────────────────────┐
│  Internal Services (VPC)                                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ PostgreSQL│ │    Redis  │ │    S3     │ │  Kafka   │          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │
└─────────────────────────────────────────────────────────────────────┘

EXTERNAL SERVICES:
┌─────────────────────────────────────────────────────────────────────┐
│  Third-party APIs                                                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                        │
│  │  Weather  │ │   Maps    │ │   Stocks  │                        │
│  │    API    │ │    API    │ │    API    │                        │
│  └───────────┘ └───────────┘ └───────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       ERROR HANDLING FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────┐
                                    │    Client    │
                                    └──────┬───────┘
                                           │
                                           │ tools/call
                                           ▼
                                  ┌────────────────┐
                                  │   Validate     │
                                  │   Arguments    │
                                  └───────┬────────┘
                                          │
           ┌──────────────────────────────┼──────────────────────────────┐
           │                              │                              │
           ▼                              ▼                              ▼
    ┌─────────────┐               ┌─────────────┐               ┌─────────────┐
    │   Valid     │               │   Invalid   │               │   Missing   │
    │  Arguments  │               │  Arguments  │               │  Required   │
    └──────┬──────┘               └──────┬──────┘               └──────┬──────┘
           │                             │                             │
           ▼                             ▼                             ▼
    ┌─────────────┐               ┌─────────────┐               ┌─────────────┐
    │  Execute    │               │  Return     │               │  Return     │
    │   Tool      │               │  Error      │               │  Error      │
    └──────┬──────┘               └──────┬──────┘               └──────┬──────┘
           │                             │                             │
           ▼                             ▼                             ▼
    ┌─────────────┐               ┌─────────────┐               ┌─────────────┐
    │   Success   │               │  -32700     │               │  -32600     │
    │   Result    │               │  Parse      │               │  Invalid    │
    │             │               │  Error      │               │  Request    │
    └─────────────┘               └─────────────┘               └─────────────┘


ERROR RESPONSE FORMAT:

{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Missing required parameter 'location'"
  }
}


ERROR CODES:

┌─────────────────────────────────────────────────────────────────────────┐
│  Standard JSON-RPC Error Codes                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  -32700  │ Parse Error       │ Invalid JSON format                    │
│  -32600  │ Invalid Request   │ JSON not valid request object          │
│  -32601  │ Method Not Found  │ Method doesn't exist                   │
│  -32602  │ Invalid Params    │ Invalid method parameters              │
│  -32603  │ Internal Error    │ Internal server error                  │
│                                                                         │
│  Custom Enterprise Codes:                                              │
│  -32000  │ Authentication Error                                        │
│  -32001  │ Authorization Error                                         │
│  -32002  │ Resource Not Found                                          │
│  -32003  │ Rate Limit Exceeded                                         │
│  -32004  │ Service Unavailable                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

These diagrams illustrate:

1. **High-Level Architecture** - The complete MCP ecosystem
2. **Server Internal Structure** - How MCP servers work internally
3. **Message Flow** - The JSON-RPC communication pattern
4. **Resource Management** - How resources are discovered and accessed
5. **Enterprise Deployment** - Scalable multi-server architecture
6. **Error Handling** - How errors are communicated

---

## Next Steps

- Continue to [02_mcp_servers](../02_mcp_servers/README.md) to build MCP servers
- Continue to [03_mcp_client](../03_mcp_client/README.md) to build MCP clients