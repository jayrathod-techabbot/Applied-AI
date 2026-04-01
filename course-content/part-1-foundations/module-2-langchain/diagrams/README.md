# Module 2: LangChain Framework — Diagrams

This directory contains text-based and Mermaid diagrams illustrating key LangChain concepts.

---

## 1. LangChain Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Chatbot  │  │   RAG    │  │  Agent   │  │ Workflow Engine  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│                      ORCHESTRATION LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │  Chains  │  │  Agents  │  │  Graphs  │  │    Workflows     │    │
│  │  (LCEL)  │  │Executor  │  │(LangGraph)│  │   (Custom)       │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│                      INTEGRATION LAYER                               │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐  │
│  │Prompts │ │ Memory │ │ Tools  │ │Indexes │ │Parsers │ │Calls  │  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └───────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                        PROVIDER LAYER                                │
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ OpenAI │ │ Anthropic │ │ Google │ │ Hugging  │ │ Local Models │  │
│  │        │ │  Claude   │ │ Gemini │ │  Face    │ │  (Ollama)    │  │
│  └────────┘ └──────────┘ └────────┘ └──────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    subgraph Application["Application Layer"]
        A1[Chatbot]
        A2[RAG System]
        A3[Agent]
        A4[Workflow]
    end

    subgraph Orchestration["Orchestration Layer"]
        O1[Chains / LCEL]
        O2[Agent Executor]
        O3[LangGraph]
    end

    subgraph Integration["Integration Layer"]
        I1[Prompt Templates]
        I2[Memory]
        I3[Tools]
        I4[Vector Stores]
        I5[Output Parsers]
        I6[Callbacks]
    end

    subgraph Provider["Provider Layer"]
        P1[OpenAI]
        P2[Anthropic]
        P3[Google]
        P4[HuggingFace]
        P5[Local]
    end

    Application --> Orchestration
    Orchestration --> Integration
    Integration --> Provider
```

---

## 2. Chain Execution Flow (LCEL)

### Linear Chain Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Input      │────>│   Prompt     │────>│    Model     │────>│   Parser     │
│  Dict        │     │  Template    │     │  (LLM/Chat)  │     │  (Output)    │
│              │     │              │     │              │     │              │
│ {"topic":    │     │ "Tell me     │     │  Generates   │     │  Structured  │
│  "Python"}   │     │ about        │     │  raw text    │     │  output      │
│              │     │ {topic}"      │     │              │     │  (str/json)  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Mermaid Diagram

```mermaid
flowchart LR
    Input["Input Dict\n{topic: Python}"]
    Prompt["ChatPromptTemplate\nFormat prompt"]
    Model["ChatOpenAI\nGenerate response"]
    Parser["StrOutputParser\nExtract text"]
    Output["Final Output\nFormatted string"]

    Input -->|invoke| Prompt
    Prompt -->|messages| Model
    Model -->|AIMessage| Parser
    Parser -->|str| Output

    style Input fill:#e1f5fe
    style Prompt fill:#fff3e0
    style Model fill:#f3e5f5
    style Parser fill:#e8f5e9
    style Output fill:#fce4ec
```

### Parallel Chain Flow

```
                    ┌──────────────────┐
                    │   Input Text     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Summary      │ │ Keywords     │ │ Sentiment    │
     │ Chain        │ │ Chain        │ │ Chain        │
     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                    ┌──────────────────┐
                    │  Combined Output │
                    │  {summary,       │
                    │   keywords,      │
                    │   sentiment}     │
                    └──────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart TB
    Input["Input Text"]

    subgraph Parallel["RunnableParallel"]
        S["Summary Chain"]
        K["Keywords Chain"]
        Sent["Sentiment Chain"]
    end

    Output["Combined Output\n{summary, keywords, sentiment}"]

    Input --> S
    Input --> K
    Input --> Sent
    S --> Output
    K --> Output
    Sent --> Output

    style Input fill:#e1f5fe
    style S fill:#fff3e0
    style K fill:#e8f5e9
    style Sent fill:#f3e5f5
    style Output fill:#fce4ec
```

---

## 3. Memory Integration Pattern

### Conversation Flow with Memory

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                               │
│                     "What did I ask before?"                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Memory Load                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ ConversationBufferMemory                                  │  │
│  │ ┌───────────────────────────────────────────────────────┐ │  │
│  │ │ Human: What is Python?                                │ │  │
│  │ │ AI: Python is a programming language...               │ │  │
│  │ │ Human: Who created it?                                │ │  │
│  │ │ AI: Guido van Rossum created Python in 1991.          │ │  │
│  │ └───────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prompt + History + Current Input                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ System: You are a helpful assistant.                      │  │
│  │ Human: What is Python?                                    │  │
│  │ AI: Python is a programming language...                   │  │
│  │ Human: Who created it?                                    │  │
│  │ AI: Guido van Rossum created Python in 1991.              │  │
│  │ Human: What did I ask before?                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LLM Response                             │
│              "You previously asked about Python                 │
│               and who created it."                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Memory Save                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Save: {input: "What did I ask before?",                   │  │
│  │        output: "You previously asked about..."}           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
sequenceDiagram
    participant User
    participant Memory
    participant Prompt
    participant LLM

    User->>Prompt: "What did I ask before?"
    Prompt->>Memory: load_memory_variables()
    Memory-->>Prompt: chat_history (previous exchanges)
    Prompt->>Prompt: Combine system + history + input
    Prompt->>LLM: Formatted messages
    LLM-->>Prompt: AI response
    Prompt->>Memory: save_context(input, output)
    Prompt-->>User: Response with context
```

### Memory Type Comparison

```
┌─────────────────────────────┬────────────────────────────────────┐
│ Memory Type                 │ Storage Strategy                   │
├─────────────────────────────┼────────────────────────────────────┤
│ ConversationBufferMemory    │ All messages stored                │
│                             │ [M1, M2, M3, M4, M5, ...]          │
├─────────────────────────────┼────────────────────────────────────┤
│ ConversationBufferWindow    │ Last N messages only               │
│                             │ [..., M(n-2), M(n-1), Mn]          │
├─────────────────────────────┼────────────────────────────────────┤
│ ConversationSummaryMemory   │ Single summary string              │
│                             │ "User asked about Python..."       │
├─────────────────────────────┼────────────────────────────────────┤
│ SummaryBufferMemory         │ Summary + recent messages          │
│                             │ [Summary, M(n-1), Mn]              │
├─────────────────────────────┼────────────────────────────────────┤
│ VectorStoreRetrieverMemory  │ Semantic search in vector store    │
│                             │ Retrieve top-k relevant memories   │
└─────────────────────────────┴────────────────────────────────────┘
```

---

## 4. Agent-Tool Interaction Loop

### ReAct Agent Loop

```
┌──────────────────────────────────────────────────────────────────┐
│                         START                                     │
│                    User: "What is 23 * 45?"                      │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    THOUGHT          │
                    │ "I need to multiply │
                    │  23 by 45. I'll use │
                    │  the calculator."   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    ACTION           │
                    │ Tool: calculator    │
                    │ Input: "23 * 45"    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   OBSERVATION       │
                    │ Tool Output: "1035" │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    THOUGHT          │
                    │ "I now have the     │
                    │  answer: 1035"      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  FINAL ANSWER       │
                    │ "23 * 45 = 1035"    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       END           │
                    └─────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart TD
    User["User Input"]
    Agent["LLM Agent"]
    Decision{Needs Tool?}
    Tool["Execute Tool"]
    Observation["Tool Result"]
    FinalAnswer["Final Answer"]

    User --> Agent
    Agent --> Decision
    Decision -->|Yes| Tool
    Decision -->|No| FinalAnswer
    Tool --> Observation
    Observation --> Agent
    FinalAnswer --> End["Response to User"]

    style User fill:#e1f5fe
    style Agent fill:#f3e5f5
    style Tool fill:#fff3e0
    style Observation fill:#e8f5e9
    style FinalAnswer fill:#fce4ec
    style End fill:#c8e6c9
```

### Tool Calling Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TOOL CALLING AGENT                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      LLM (GPT-4/Claude)                     │   │
│  │                                                             │   │
│  │  Input: "What's the weather in Tokyo and convert 25°C to °F"│   │
│  │                                                             │   │
│  │  Output: [Tool Calls]                                       │   │
│  │    1. get_weather(city="Tokyo")                             │   │
│  │    2. celsius_to_fahrenheit(celsius=25)                     │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│              ┌──────────────┴──────────────┐                       │
│              ▼                             ▼                       │
│  ┌─────────────────────┐     ┌─────────────────────┐              │
│  │  get_weather Tool   │     │ celsius_to_fahrenheit │              │
│  │  → "Sunny, 25°C"    │     │ → "77°F"              │              │
│  └──────────┬──────────┘     └──────────┬──────────┘              │
│             │                           │                          │
│             └──────────────┬────────────┘                          │
│                            ▼                                       │
│              ┌─────────────────────────┐                          │
│              │    LLM Synthesizes      │                          │
│              │ "In Tokyo it's sunny    │                          │
│              │  at 25°C, which is 77°F"│                          │
│              └─────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
sequenceDiagram
    participant User
    participant Agent as AgentExecutor
    participant LLM as ChatOpenAI
    participant Tool1 as get_weather
    participant Tool2 as celsius_to_f

    User->>Agent: "Weather in Tokyo? Convert 25°C to °F"
    Agent->>LLM: Prompt + tools schema
    LLM-->>Agent: Tool calls: [get_weather(Tokyo), celsius_to_f(25)]
    Agent->>Tool1: get_weather("Tokyo")
    Tool1-->>Agent: "Sunny, 25°C"
    Agent->>Tool2: celsius_to_f(25)
    Tool2-->>Agent: "77°F"
    Agent->>LLM: Results + original question
    LLM-->>Agent: "In Tokyo it's sunny at 25°C (77°F)"
    Agent-->>User: Final answer
```

---

## 5. RAG Pipeline (Bonus)

### Retrieval-Augmented Generation Flow

```mermaid
flowchart LR
    subgraph Indexing["Indexing Phase"]
        Docs["Documents"] --> Split["Text Splitter"]
        Split --> Chunks["Chunks"]
        Chunks --> Embed["Embedding Model"]
        Embed --> Vectors["Vector Store"]
    end

    subgraph Query["Query Phase"]
        Question["User Question"] --> QEmbed["Embed Question"]
        QEmbed --> Search["Similarity Search"]
        Vectors --> Search
        Search --> Context["Top-K Chunks"]
    end

    subgraph Generation["Generation Phase"]
        Context --> Prompt["Augmented Prompt"]
        Question --> Prompt
        Prompt --> LLM["LLM"]
        LLM --> Answer["Answer"]
    end

    Indexing -.-> Query
    Query --> Generation

    style Docs fill:#e1f5fe
    style Vectors fill:#fff3e0
    style Question fill:#f3e5f5
    style LLM fill:#e8f5e9
    style Answer fill:#fce4ec
```

---

## 6. Complete LangChain Application Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LANGCHAIN APPLICATION                           │
│                                                                     │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
│  │  User   │───>│  Input   │───>│  Chain   │───>│   Output     │  │
│  │ Interface│    │Validation│    │Execution │    │  Formatting  │  │
│  └─────────┘    └──────────┘    └────┬─────┘    └──────────────┘  │
│                                      │                              │
│              ┌───────────────────────┼───────────────────────┐     │
│              │                       │                       │     │
│              ▼                       ▼                       ▼     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │     Memory       │  │     Tools        │  │   Vector Store   │ │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌──────────────┐ │ │
│  │ │Conversation  │ │  │ │Web Search    │ │  │ │Document      │ │ │
│  │ │History       │ │  │ │Calculator    │ │  │ │Chunks        │ │ │
│  │ │Summary       │ │  │ │API Calls     │ │  │ │Embeddings    │ │ │
│  │ └──────────────┘ │  │ └──────────────┘ │  │ └──────────────┘ │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Callbacks & Monitoring                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│  │  │Token     │  │Latency   │  │Error     │  │Cost      │   │   │
│  │  │Tracking  │  │Tracking  │  │Handling  │  │Tracking  │   │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```
