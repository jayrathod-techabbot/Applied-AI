# Module 5: Model Context Protocol (MCP) — Diagrams

This directory contains text-based diagrams illustrating key MCP concepts.

---

## Table of Contents
- [1. MCP Architecture Overview](#1-mcp-architecture-overview)
- [2. Client-Server Communication Flow](#2-client-server-communication-flow)
- [3. Tool/Resource/Prompt Registration](#3-toolresourceprompt-registration)
- [4. Enterprise Integration Pattern](#4-enterprise-integration-pattern)

---

## 1. MCP Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP HOST                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MCP Client Layer                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │   LLM App    │  │ Agent Frame  │  │ Custom Client  │  │  │
│  │  │  (Claude)    │  │  (LangChain) │  │  (Your App)    │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │  │
│  │         └──────────────────┼──────────────────┘           │  │
│  │                    MCP Client SDK                         │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Session Manager │ Transport │ Protocol Handler   │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   JSON-RPC 2.0    │
                    │   Messages Over   │
                    │   Transport Layer │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                       MCP SERVERS                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Server A   │  │   Server B   │  │      Server C        │  │
│  │  (Database)  │  │  (Web API)   │  │   (File System)      │  │
│  │              │  │              │  │                      │  │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────────────┐ │  │
│  │ │ Resources│ │  │ │ Resources│ │  │ │ Resources        │ │  │
│  │ │ Tools    │ │  │ │ Tools    │ │  │ │ Tools            │ │  │
│  │ │ Prompts  │ │  │ │ Prompts  │ │  │ │ Prompts          │ │  │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────────────┘ │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

```
┌──────────────────────────────────────────────────────────────┐
│                    MCP CLIENT COMPONENTS                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Application Layer                                       │ │
│  │  - LLM Integration (Claude, GPT, etc.)                  │ │
│  │  - Agent Orchestration                                   │ │
│  │  - User Interface                                        │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Client SDK Layer                                        │ │
│  │  - ClientSession: Manages connection lifecycle          │ │
│  │  - Protocol Handler: JSON-RPC message formatting        │ │
│  │  - Capability Negotiator: Handshake management          │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Transport Layer                                         │ │
│  │  - StdioClientTransport: Local process communication    │ │
│  │  - SSEClientTransport: HTTP with Server-Sent Events     │ │
│  │  - WebSocketClientTransport: Real-time bidirectional    │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    MCP SERVER COMPONENTS                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Transport Layer                                         │ │
│  │  - StdioServerTransport: Receives from stdin            │ │
│  │  - SSEServerTransport: HTTP endpoint + SSE stream       │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Server SDK Layer                                        │ │
│  │  - Server: Core server instance                          │ │
│  │  - Protocol Handler: Routes JSON-RPC requests           │ │
│  │  - Capability Manager: Declares server capabilities     │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Resource/Tool/Prompt Handlers                           │ │
│  │  - @server.list_resources() / @server.read_resource()   │ │
│  │  - @server.list_tools() / @server.call_tool()           │ │
│  │  - @server.list_prompts() / @server.get_prompt()        │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Backend Integrations                                    │ │
│  │  - Database connectors, API clients, file handlers      │ │
│  │  - Authentication, rate limiting, caching               │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Client-Server Communication Flow

### Full Communication Sequence

```
CLIENT                                              SERVER
  │                                                   │
  │  ──── 1. CONNECT (Transport Layer) ────────────►  │
  │       (stdio pipe / HTTP connection / WS)         │
  │                                                   │
  │  ──── 2. INITIALIZE REQUEST ──────────────────►  │
  │       {                                           │
  │         "jsonrpc": "2.0",                         │
  │         "id": 1,                                  │
  │         "method": "initialize",                   │
  │         "params": {                               │
  │           "protocolVersion": "2024-11-05",        │
  │           "capabilities": {"sampling": {}},       │
  │           "clientInfo": {                         │
  │             "name": "my-client",                  │
  │             "version": "1.0.0"                    │
  │           }                                       │
  │         }                                         │
  │       }                                           │
  │                                                   │
  │  ◄─── 3. INITIALIZE RESPONSE ──────────────────  │
  │       {                                           │
  │         "jsonrpc": "2.0",                         │
  │         "id": 1,                                  │
  │         "result": {                               │
  │           "protocolVersion": "2024-11-05",        │
  │           "capabilities": {                       │
  │             "tools": {"listChanged": true},       │
  │             "resources": {                        │
  │               "subscribe": true,                  │
  │               "listChanged": true                 │
  │             },                                    │
  │             "prompts": {"listChanged": true}      │
  │           },                                      │
  │           "serverInfo": {                         │
  │             "name": "analytics-server",           │
  │             "version": "1.0.0"                    │
  │           }                                       │
  │         }                                         │
  │       }                                           │
  │                                                   │
  │  ──── 4. INITIALIZED NOTIFICATION ────────────►  │
  │       {                                           │
  │         "jsonrpc": "2.0",                         │
  │         "method": "notifications/initialized"     │
  │       }                                           │
  │                                                   │
  │  ════════ HANDSHAKE COMPLETE ════════════════     │
  │                                                   │
  │  ──── 5. LIST TOOLS REQUEST ──────────────────►  │
  │       {"jsonrpc":"2.0","id":2,"method":"tools/list"}
  │                                                   │
  │  ◄─── 6. LIST TOOLS RESPONSE ──────────────────  │
  │       {"jsonrpc":"2.0","id":2,"result":{          │
  │         "tools":[                                 │
  │           {"name":"query_db",                     │
  │            "description":"Execute SQL query",     │
  │            "inputSchema":{...}},                  │
  │           {"name":"analyze_data",                 │
  │            "description":"Analyze dataset",       │
  │            "inputSchema":{...}}                   │
  │         ]}}                                       │
  │                                                   │
  │  ──── 7. CALL TOOL REQUEST ───────────────────►  │
  │       {"jsonrpc":"2.0","id":3,                    │
  │        "method":"tools/call",                     │
  │        "params":{                                 │
  │          "name":"query_db",                       │
  │          "arguments":{"query":"SELECT * FROM users│
  │                        LIMIT 10"}}}               │
  │                                                   │
  │  ◄─── 8. TOOL EXECUTION + RESPONSE ────────────  │
  │       {"jsonrpc":"2.0","id":3,"result":{          │
  │         "content":[                               │
  │           {"type":"text",                         │
  │            "text":"[{id:1,name:'Alice'},          │
  │                     {id:2,name:'Bob'}]"}          │
  │         ]}}                                       │
  │                                                   │
  │  ──── 9. READ RESOURCE REQUEST ───────────────►  │
  │       {"jsonrpc":"2.0","id":4,                    │
  │        "method":"resources/read",                 │
  │        "params":{"uri":"file://data/report.csv"}} │
  │                                                   │
  │  ◄─── 10. RESOURCE CONTENT RESPONSE ───────────  │
  │       {"jsonrpc":"2.0","id":4,"result":{          │
  │         "contents":[                              │
  │           {"uri":"file://data/report.csv",        │
  │            "mimeType":"text/csv",                 │
  │            "text":"date,revenue,users\n..."}      │
  │         ]}}                                       │
  │                                                   │
  │  ──── 11. SUBSCRIBE RESOURCE ─────────────────►  │
  │       {"jsonrpc":"2.0","id":5,                    │
  │        "method":"resources/subscribe",            │
  │        "params":{"uri":"file://data/report.csv"}} │
  │                                                   │
  │  ◄─── 12. SUBSCRIBE ACKNOWLEDGED ──────────────  │
  │       {"jsonrpc":"2.0","id":5,"result":null}      │
  │                                                   │
  │       ... (time passes, resource changes) ...     │
  │                                                   │
  │  ◄─── 13. RESOURCE UPDATED NOTIFICATION ───────  │
  │       {"jsonrpc":"2.0",                           │
  │        "method":"notifications/resources/updated",│
  │        "params":{"uri":"file://data/report.csv"}} │
  │                                                   │
  │  ──── 14. RE-READ UPDATED RESOURCE ───────────►  │
  │       (client reads resource again)               │
  │                                                   │
  │  ◄─── 15. UPDATED CONTENT ─────────────────────  │
  │       (server returns new content)                │
  │                                                   │
```

### Tool Call Flow Detail

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User   │────►│  LLM App     │────►│  MCP Client  │────►│  MCP Server  │
│ Request │     │  (Claude)    │     │  (SDK)       │     │  (Backend)   │
└─────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                      │                      │                      │
    1. User asks:     │                      │                      │
    "What are our     │                      │                      │
    Q3 sales?"        │                      │                      │
                      │                      │                      │
    2. LLM decides    │                      │                      │
    to use tool       │                      │                      │
    "query_sales"     │                      │                      │
                      │                      │                      │
    3. LLM generates  │                      │                      │
    tool call with    │                      │                      │
    arguments         │                      │                      │
    {period: "Q3"}    │                      │                      │
                      │─────────────────────►│                      │
                      │  tools/call          │                      │
                      │  {name:"query_sales",│                      │
                      │   args:{period:"Q3"}}│                      │
                      │                      │                      │
                      │                      │─────────────────────►│
                      │                      │  Execute tool logic   │
                      │                      │  (query database)     │
                      │                      │                      │
                      │                      │◄─────────────────────│
                      │                      │  Tool result:         │
                      │                      │  {revenue: $1.2M}     │
                      │                      │                      │
                      │◄─────────────────────│                      │
                      │  Tool response       │                      │
                      │  {content:[{text:...}]}                     │
                      │                      │                      │
    4. LLM receives   │                      │                      │
    tool result and   │                      │                      │
    generates final   │                      │                      │
    answer            │                      │                      │
                      │                      │                      │
    5. Final answer   │                      │                      │
    "Q3 sales were    │                      │                      │
    $1.2M in revenue" │                      │                      │
◄─────────────────────│                      │                      │
```

### Notification Flow

```
SERVER EVENT                          NOTIFICATION                          CLIENT ACTION
     │                                      │                                    │
     │  Tool list changes                   │                                    │
     │  (new tool added)                    │                                    │
     ├─────────────────────────────────────►│                                    │
     │  notifications/tools/                │                                    │
     │  list_changed                        │                                    │
     │                                      ├───────────────────────────────────►│
     │                                      │  Client receives notification      │
     │                                      │  Client calls tools/list           │
     │                                      │  Client updates tool registry      │
     │                                      │                                    │
     │  Resource content changes            │                                    │
     │  (file updated)                      │                                    │
     ├─────────────────────────────────────►│                                    │
     │  notifications/resources/            │                                    │
     │  updated {uri: "..."}                │                                    │
     │                                      ├───────────────────────────────────►│
     │                                      │  Client receives notification      │
     │                                      │  Client calls resources/read       │
     │                                      │  Client updates cached content     │
     │                                      │                                    │
     │  Server log message                  │                                    │
     ├─────────────────────────────────────►│                                    │
     │  notifications/message               │                                    │
     │  {level:"info",data:"..."}           │                                    │
     │                                      ├───────────────────────────────────►│
     │                                      │  Client logs/displays message      │
```

---

## 3. Tool/Resource/Prompt Registration

### Tool Registration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOOL REGISTRATION PROCESS                            │
│                                                                              │
│  STEP 1: DEFINE TOOL SCHEMA                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  @server.list_tools()                                               │    │
│  │  async def list_tools():                                            │    │
│  │      return [                                                       │    │
│  │          Tool(                                                      │    │
│  │              name="query_database",                                 │    │
│  │              description="Execute read-only SQL query",             │    │
│  │              inputSchema={                                          │    │
│  │                  "type": "object",                                  │    │
│  │                  "properties": {                                    │    │
│  │                      "query":  {"type": "string"},                  │    │
│  │                      "limit":  {"type": "integer", "default": 100}  │    │
│  │                  },                                                 │    │
│  │                  "required": ["query"]                              │    │
│  │              }                                                      │    │
│  │          )                                                          │    │
│  │      ]                                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  STEP 2: CLIENT DISCOVERS TOOLS                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Client Request:              Server Response:                       │    │
│  │  ┌──────────────────────┐    ┌──────────────────────────────────┐  │    │
│  │  │ {"jsonrpc":"2.0",    │───►│ {"jsonrpc":"2.0",                │  │    │
│  │  │  "id":1,             │    │  "id":1,                         │  │    │
│  │  │  "method":"tools/    │    │  "result":{                      │  │    │
│  │  │  list"}              │    │    "tools":[                     │  │    │
│  │  └──────────────────────┘    │      {                           │  │    │
│  │                              │        "name":"query_database",  │  │    │
│  │                              │        "description":"Execute...",│  │    │
│  │                              │        "inputSchema":{...}       │  │    │
│  │                              │      }                           │  │    │
│  │                              │    ]}}                           │  │    │
│  │                              └──────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  STEP 3: LLM SELECTS TOOL                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LLM receives tool list → Analyzes user request → Selects tool     │    │
│  │  "User asks for database query → query_database tool matches →     │    │
│  │   Generate arguments: {query: 'SELECT * FROM sales', limit: 50}"   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  STEP 4: TOOL EXECUTION                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Client Request:              Server Handler:                        │    │
│  │  ┌──────────────────────┐    ┌──────────────────────────────────┐  │    │
│  │  │ {"jsonrpc":"2.0",    │───►│ @server.call_tool()              │  │    │
│  │  │  "id":2,             │    │ async def call_tool(name, args): │  │    │
│  │  │  "method":"tools/    │    │   if name == "query_database":   │  │    │
│  │  │  call",              │    │     results = await db.execute(  │  │    │
│  │  │  "params":{          │    │       args["query"],             │  │    │
│  │  │      "name":         │    │       args.get("limit", 100)     │  │    │
│  │  │        "query_       │    │     )                            │  │    │
│  │  │        database",    │    │     return [TextContent(         │  │    │
│  │  │      "arguments":{   │    │       type="text",               │  │    │
│  │  │        "query":      │    │       text=json.dumps(results)   │  │    │
│  │  │          "SELECT *   │    │     )]                           │  │    │
│  │  │          FROM sales" │    │                                  │  │    │
│  │  │      }               │    │                                  │  │    │
│  │  │  }}                  │    │                                  │  │    │
│  │  └──────────────────────┘    └──────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Resource Registration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESOURCE REGISTRATION                         │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. SERVER REGISTERS RESOURCES                             │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  @server.list_resources()                           │  │  │
│  │  │  async def list_resources():                        │  │  │
│  │  │      return [                                       │  │  │
│  │  │          Resource(                                  │  │  │
│  │  │              uri="file://data/sales.csv",           │  │  │
│  │  │              name="Sales Data",                     │  │  │
│  │  │              description="Monthly sales 2024",      │  │  │
│  │  │              mimeType="text/csv"                    │  │  │
│  │  │          ),                                         │  │  │
│  │  │          Resource(                                  │  │  │
│  │  │              uri="db://analytics/users",            │  │  │
│  │  │              name="User Metrics",                   │  │  │
│  │  │              description="User engagement data",    │  │  │
│  │  │              mimeType="application/json"            │  │  │
│  │  │          )                                          │  │  │
│  │  │      ]                                              │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  2. CLIENT READS RESOURCE                                  │  │
│  │                                                            │  │
│  │  Client:                    Server:                        │  │
│  │  resources/read ─────────►  @server.read_resource(uri)    │  │
│  │  {uri:"file://data/         ├─ Check URI pattern           │  │
│  │   sales.csv"}               ├─ Open file / query DB        │  │
│  │                             ├─ Read content                │  │
│  │  ◄───────────────────────── └─ Return content              │  │
│  │  {contents:[                                               │  │
│  │    {uri:"file://data/                                      │  │
│  │     sales.csv",                                            │  │
│  │     mimeType:"text/csv",                                   │  │
│  │     text:"date,revenue\n..."}                              │  │
│  │  ]}                                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  3. RESOURCE SUBSCRIPTION (Real-time Updates)              │  │
│  │                                                            │  │
│  │  Client:                    Server:                        │  │
│  │  resources/subscribe ─────►  Register subscription         │  │
│  │  {uri:"file://data/         for URI                       │  │
│  │   sales.csv"}                                               │  │
│  │                             ... (file changes) ...         │  │
│  │  ◄─────────────────────────  notifications/resources/      │  │
│  │                              updated                       │  │
│  │                              {uri:"file://data/sales.csv"} │  │
│  │                                                            │  │
│  │  Client re-reads resource to get updated content           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Prompt Registration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROMPT REGISTRATION                           │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. SERVER DEFINES PROMPT TEMPLATES                        │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  @server.list_prompts()                             │  │  │
│  │  │  async def list_prompts():                          │  │  │
│  │  │      return [                                       │  │  │
│  │  │          Prompt(                                    │  │  │
│  │  │              name="code_review",                    │  │  │
│  │  │              description="Review code for issues",  │  │  │
│  │  │              arguments=[                            │  │  │
│  │  │                  {                                  │  │  │
│  │  │                      "name": "language",            │  │  │
│  │  │                      "required": True,              │  │  │
│  │  │                      "description": "Programming    │  │  │
│  │  │                                       language"     │  │  │
│  │  │                  },                                 │  │  │
│  │  │                  {                                  │  │  │
│  │  │                      "name": "focus",               │  │  │
│  │  │                      "required": False,             │  │  │
│  │  │                      "description": "Review focus   │  │  │
│  │  │                                       area"         │  │  │
│  │  │                  }                                  │  │  │
│  │  │              ]                                      │  │  │
│  │  │          )                                          │  │  │
│  │  │      ]                                              │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  2. CLIENT REQUESTS PROMPT WITH ARGUMENTS                  │  │
│  │                                                            │  │
│  │  Client Request:                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  prompts/get                                        │  │  │
│  │  │  {                                                  │  │  │
│  │  │    "name": "code_review",                           │  │  │
│  │  │    "arguments": {                                   │  │  │
│  │  │      "language": "python",                          │  │  │
│  │  │      "focus": "security"                            │  │  │
│  │  │    }                                                │  │  │
│  │  │  }                                                  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  Server Response:                                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  {                                                  │  │  │
│  │  │    "messages": [{                                   │  │  │
│  │  │      "role": "user",                                │  │  │
│  │  │      "content": {                                   │  │  │
│  │  │        "type": "text",                              │  │  │
│  │  │        "text": "Review the following Python code    │  │  │
│  │  │               for security vulnerabilities:..."     │  │  │
│  │  │      }                                              │  │  │
│  │  │    }]                                               │  │  │
│  │  │  }                                                  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  Client sends the prompt message to the LLM                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Enterprise Integration Pattern

### Enterprise MCP Mesh Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ENTERPRISE MCP MESH                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         CLIENT TIER                                  │    │
│  │                                                                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │    │
│  │  │  AI Chatbot  │  │  Agent App   │  │  Analytics   │  │  Mobile  │ │    │
│  │  │  (Web)       │  │  (Desktop)   │  │  Dashboard   │  │  App     │ │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │    │
│  │         │                 │                 │                │        │    │
│  │         └─────────────────┴─────────────────┴────────────────┘        │    │
│  │                            │                                          │    │
│  │                    ┌───────┴───────┐                                  │    │
│  │                    │  MCP Client   │                                  │    │
│  │                    │  Gateway      │                                  │    │
│  │                    │               │                                  │    │
│  │                    │ - Auth        │                                  │    │
│  │                    │ - Routing     │                                  │    │
│  │                    │ - Rate Limit  │                                  │    │
│  │                    │ - Load Balance│                                  │    │
│  │                    │ - Audit Log   │                                  │    │
│  │                    └───────┬───────┘                                  │    │
│  └────────────────────────────┼─────────────────────────────────────────┘    │
│                               │                                              │
│  ┌────────────────────────────┼─────────────────────────────────────────┐    │
│  │                      SERVER TIER                                      │    │
│  │                               │                                       │    │
│  │              ┌────────────────┼────────────────┐                      │    │
│  │              │                │                │                      │    │
│  │     ┌────────┴──────┐ ┌──────┴──────┐ ┌──────┴───────┐               │    │
│  │     │  Data MCP     │ │  CRM MCP    │ │  Code MCP    │               │    │
│  │     │  Server       │ │  Server     │ │  Server      │               │    │
│  │     │               │ │             │ │              │               │    │
│  │     │ Tools:        │ │ Tools:      │ │ Tools:       │               │    │
│  │     │ - sql_query   │ │ - get_deals │ │ - search_code│               │    │
│  │     │ - get_schema  │ │ - get_contact│ │ - get_pr    │               │    │
│  │     │ - export_data │ │ - create_lead│ │ - run_tests │               │    │
│  │     │               │ │             │ │              │               │    │
│  │     │ Resources:    │ │ Resources:  │ │ Resources:   │               │    │
│  │     │ - db://sales  │ │ - api://crm │ │ - git://repo │               │    │
│  │     │ - db://users  │ │ - api://leads│ │ - file://src │               │    │
│  │     └───────────────┘ └─────────────┘ └──────────────┘               │    │
│  │                                                                       │    │
│  │     ┌───────────────────────────────────────────────────────────┐     │    │
│  │     │              EXTERNAL SYSTEMS                              │     │    │
│  │     │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │     │    │
│  │     │  │PostgreSQL│ │Salesforce│ │  GitHub  │ │  Snowflake   │ │     │    │
│  │     │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │     │    │
│  │     └───────────────────────────────────────────────────────────┘     │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                      CROSS-CUTTING CONCERNS                            │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │   │
│  │  │  Auth/OAuth│ │  Rate      │ │  Audit     │ │  Monitoring &     │  │   │
│  │  │  Middleware│ │  Limiter   │ │  Logger    │ │  Alerting          │  │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow Through Enterprise Architecture

```
USER REQUEST: "Show me Q3 sales from Salesforce and compare with our database"

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: USER → CLIENT APPLICATION                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  User types query into chat interface                                  │  │
│  │  Client app sends query to LLM with available tool descriptions        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  STEP 2: LLM → TOOL SELECTION                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  LLM analyzes query and determines it needs:                          │  │
│  │  1. fetch_crm_data (to get Salesforce Q3 data)                        │  │
│  │  2. sql_query (to get internal database Q3 data)                      │  │
│  │  3. analyze_comparison (to compare both datasets)                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  STEP 3: CLIENT → MCP GATEWAY                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Gateway receives tool call requests                                  │  │
│  │  ├─ Authenticates client (JWT token validation)                       │  │
│  │  ├─ Checks authorization (user has access to CRM + DB tools)          │  │
│  │  ├─ Rate limiting check (within quota)                                │  │
│  │  └─ Routes each tool call to appropriate MCP server                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  STEP 4: GATEWAY → MCP SERVERS (Parallel Execution)                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────┐     ┌─────────────────────┐                 │  │
│  │  │  CRM MCP Server     │     │  Data MCP Server    │                 │  │
│  │  │                     │     │                     │                 │  │
│  │  │ fetch_crm_data      │     │ sql_query           │                 │  │
│  │  │ {object_type:"deals"│     │ {query:"SELECT      │                 │  │
│  │  │  filters:{          │     │  SUM(revenue)       │                 │  │
│  │  │    quarter:"Q3"}}   │     │  FROM sales         │                 │  │
│  │  │                     │     │  WHERE quarter='Q3'"}                 │  │
│  │  │                     │     │                     │                 │  │
│  │  │ ─► Salesforce API   │     │ ─► PostgreSQL       │                 │  │
│  │  │ ◄─ {deals:[...]}    │     │ ◄─ {sum: 1250000}   │                 │  │
│  │  └─────────────────────┘     └─────────────────────┘                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  STEP 5: GATEWAY → ANALYSIS TOOL                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Gateway combines results and calls analysis tool:                    │  │
│  │  analyze_comparison({                                                 │  │
│  │    crm_data: {deals: [...], total: 1300000},                          │  │
│  │    db_data: {total: 1250000}                                          │  │
│  │  })                                                                   │  │
│  │                                                                       │  │
│  │  Result: {                                                            │  │
│  │    variance: 50000,                                                   │  │
│  │    variance_pct: 4.0,                                                 │  │
│  │    explanation: "CRM shows 4% higher due to pending deals..."         │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  STEP 6: LLM → FINAL RESPONSE                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  LLM receives analysis results and generates natural language answer: │  │
│  │                                                                       │  │
│  │  "In Q3, Salesforce CRM shows $1.3M in deals while our internal      │  │
│  │   database records $1.25M in recognized revenue. The 4% variance     │  │
│  │   is primarily due to 5 deals in 'negotiation' stage in CRM that     │  │
│  │   haven't been closed yet."                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  STEP 7: AUDIT LOG                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  All operations logged for compliance:                                │  │
│  │  {                                                                    │  │
│  │    "timestamp": "2024-01-15T10:30:00Z",                               │  │
│  │    "user_id": "user_123",                                             │  │
│  │    "tools_called": ["fetch_crm_data", "sql_query",                    │  │
│  │                      "analyze_comparison"],                            │  │
│  │    "duration_ms": 2450,                                               │  │
│  │    "status": "success"                                                │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Integration Patterns Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MCP INTEGRATION PATTERNS                                  │
│                                                                              │
│  PATTERN 1: SIDECAR                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────────────┐    ┌─────────────────────┐                 │    │
│  │  │   Main Application  │    │   MCP Server        │                 │    │
│  │  │   ┌───────────────┐ │    │   ┌───────────────┐ │                 │    │
│  │  │   │  LLM Client   │ │    │   │  Tools        │ │                 │    │
│  │  │   │  (stdio)      │◄┼────┤   │  Resources    │ │                 │    │
│  │  │   └───────────────┘ │    │   │  Prompts      │ │                 │    │
│  │  │                     │    │   └───────────────┘ │                 │    │
│  │  └─────────────────────┘    └─────────────────────┘                 │    │
│  │                                                                       │    │
│  │  Use Case: Desktop apps, local agents, single-user tools              │    │
│  │  Pros: Low latency, simple setup, no network overhead                 │    │
│  │  Cons: One-to-one only, not scalable                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PATTERN 2: GATEWAY                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │    │
│  │  │ Client A │  │ Client B │  │ Client C │                          │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘                          │    │
│  │       └─────────────┼─────────────┘                                  │    │
│  │                ┌────┴────┐                                             │    │
│  │                │ Gateway │ ← Auth, Rate Limit, Routing, Audit         │    │
│  │                └────┬────┘                                             │    │
│  │          ┌──────────┼──────────┐                                       │    │
│  │     ┌────┴────┐ ┌───┴────┐ ┌───┴────┐                                 │    │
│  │     │ Server A│ │Server B│ │Server C│                                 │    │
│  │     └─────────┘ └────────┘ └────────┘                                 │    │
│  │                                                                       │    │
│  │  Use Case: Enterprise, multi-tenant, centralized control              │    │
│  │  Pros: Centralized auth, audit, rate limiting, load balancing         │    │
│  │  Cons: Single point of failure, added latency                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PATTERN 3: MESH                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │    │
│  │  │ Client A │  │ Client B │  │ Client C │                          │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘                          │    │
│  │       │             │             │                                   │    │
│  │  ┌────┴─────────────┴─────────────┴────┐                             │    │
│  │  │       Service Discovery             │                             │    │
│  │  │       (Registry)                    │                             │    │
│  │  └────┬─────────────┬─────────────┬────┘                             │    │
│  │       │             │             │                                   │    │
│  │  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐                               │    │
│  │  │ Server A│  │ Server B│  │ Server C│  (each with own tools)        │    │
│  │  └─────────┘  └─────────┘  └─────────┘                               │    │
│  │                                                                       │    │
│  │  Use Case: Microservices, distributed teams, independent deployments  │    │
│  │  Pros: Decoupled, independently deployable, fault isolated            │    │
│  │  Cons: Complex discovery, harder to manage globally                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PATTERN 4: PROXY                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────┐          ┌──────────────────────────────────┐         │    │
│  │  │  Client  │─────────►│     MCP Proxy Server             │         │    │
│  │  └──────────┘          │                                  │         │    │
│  │                        │  ┌────────────────────────────┐  │         │    │
│  │                        │  │  Legacy API Adapter        │  │         │    │
│  │                        │  │  REST → MCP Tool Mapping   │  │         │    │
│  │                        │  │  SOAP → MCP Tool Mapping   │  │         │    │
│  │                        │  │  GraphQL → MCP Tool Mapping│  │         │    │
│  │                        │  └────────────────────────────┘  │         │    │
│  │                        └──────────────────────────────────┘         │    │
│  │                                                                       │    │
│  │  Use Case: Legacy system modernization, API wrapper                   │    │
│  │  Pros: No changes to legacy systems, incremental adoption             │    │
│  │  Cons: Translation overhead, potential feature limitations            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MCP SECURITY LAYERS                                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 1: TRANSPORT SECURITY                                         │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  - TLS 1.3 for all HTTP/SSE connections                       │  │    │
│  │  │  - OS-level process isolation for stdio                        │  │    │
│  │  │  - Certificate pinning for sensitive connections               │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 2: AUTHENTICATION                                             │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  Client ────[JWT / API Key / OAuth Token]────► Gateway        │  │    │
│  │  │                                                               │  │    │
│  │  │  Gateway validates:                                           │  │    │
│  │  │  ├─ Token signature and expiry                                │  │    │
│  │  │  ├─ Client identity and permissions                           │  │    │
│  │  │  └─ Token revocation status                                   │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 3: AUTHORIZATION (RBAC)                                       │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  Role        │ Tools Allowed      │ Resources Allowed         │  │    │
│  │  │  ────────────┼────────────────────┼───────────────────────────│  │    │
│  │  │  Analyst     │ sql_query,         │ db://analytics/*          │  │    │
│  │  │              │ get_table_info     │ file://reports/*          │  │    │
│  │  │  ────────────┼────────────────────┼───────────────────────────│  │    │
│  │  │  Sales Rep   │ fetch_crm_data,    │ api://crm/deals           │  │    │
│  │  │              │ generate_report    │ api://crm/contacts        │  │    │
│  │  │  ────────────┼────────────────────┼───────────────────────────│  │    │
│  │  │  Admin       │ ALL tools          │ ALL resources             │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 4: INPUT VALIDATION                                           │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  - JSON Schema validation (automatic via SDK)                 │  │    │
│  │  │  - SQL injection prevention (read-only enforcement)           │  │    │
│  │  │  - Path traversal prevention (resource URI validation)        │  │    │
│  │  │  - Size limits on inputs and outputs                          │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 5: RATE LIMITING & QUOTAS                                     │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  - Per-client tool call rate limits                           │  │    │
│  │  │  - Per-tool rate limits (expensive operations)                │  │    │
│  │  │  - Daily/monthly quotas                                       │  │    │
│  │  │  - External API rate limit pass-through                       │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 6: AUDIT & MONITORING                                         │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  - All tool calls logged with user, tool, args, result size   │  │    │
│  │  │  - Sensitive data redaction in logs                           │  │    │
│  │  │  - Anomaly detection on usage patterns                        │  │    │
│  │  │  - Real-time alerting on security events                      │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```
