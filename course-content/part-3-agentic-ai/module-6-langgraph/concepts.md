# Module 6: LangGraph Deep Dive — Core Concepts

## Table of Contents
- [6.1 LangGraph Overview and Core Concepts](#61-langgraph-overview-and-core-concepts)
- [6.2 Building Blocks: Nodes, Edges, State Management](#62-building-blocks-nodes-edges-state-management)
- [6.3 Cyclic vs. DAG Graphs — Human-in-the-Loop Patterns](#63-cyclic-vs-dag-graphs--human-in-the-loop-patterns)
- [Summary](#summary)

---

## 6.1 LangGraph Overview and Core Concepts

### What is LangGraph?

LangGraph is a library for building **stateful, multi-actor applications** with LLMs. It extends LangChain by adding a **graph-based orchestration layer** that enables cycles, branching, persistence, and human-in-the-loop interactions — capabilities that traditional DAG-only chains cannot provide.

LangGraph was created to solve a fundamental problem: **LLM applications are not linear pipelines**. Real-world agents need to loop, retry, branch based on conditions, maintain state across turns, pause for human input, and recover from failures. LangGraph provides the primitives to model these workflows as executable graphs.

### Why LangGraph Exists

```
Traditional Chains (LangChain)          LangGraph
─────────────────────────────          ──────────
Linear, directed acyclic graphs        Cyclic graphs with loops
Stateless between calls                Persistent state management
No built-in human intervention         Human-in-the-loop primitives
Single execution path                  Conditional branching & routing
No checkpointing                       Built-in checkpointing & time travel
Hard to debug intermediate steps       Stream every step, inspect state
```

### LangGraph vs. LangChain Agents Comparison

| Feature | LangChain Agents | LangGraph |
|---------|-----------------|-----------|
| **Execution Model** | Linear ReAct loop | Arbitrary graph (cycles, branches) |
| **State Management** | Implicit (conversation history) | Explicit TypedDict/Pydantic state |
| **Control Flow** | Fixed loop with tool calling | Full graph: parallel, conditional, nested |
| **Human-in-the-Loop** | Limited (callback-based) | Native (`interrupt`, `interrupt_before/after`) |
| **Persistence** | Manual implementation | Built-in checkpointer (Memory, SQLite, Postgres) |
| **Streaming** | Token-level only | Step-level, node-level, event-level |
| **Debugging** | Verbose logging | Visual graph + state snapshots |
| **Subgraphs** | Not supported | First-class composable subgraphs |
| **Time Travel** | Not supported | Replay from any checkpoint |
| **Best For** | Simple tool-using agents | Complex multi-step workflows, production agents |

### When to Use LangGraph

```
Use LangGraph when:                          Use LangChain when:
────────────────────────                     ─────────────────
✓ Multi-step reasoning with loops            ✓ Simple Q&A chains
✓ Human approval checkpoints                 ✓ Straightforward tool calling
✓ State that evolves across steps            ✓ Stateless transformations
✓ Conditional routing based on LLM output    ✓ Linear prompt → LLM → output
✓ Retry and self-correction patterns         ✓ Basic RAG pipelines
✓ Multi-agent coordination                   ✓ Single-turn conversations
✓ Production-grade reliability               ✓ Prototyping and experimentation
```

### Core Concepts

#### StateGraph

The `StateGraph` is the central abstraction. It defines:
- **State**: A schema (TypedDict or Pydantic) that flows through the graph
- **Nodes**: Functions that read and update state
- **Edges**: Connections between nodes (normal or conditional)

```
┌─────────────────────────────────────────────────────────┐
│                    StateGraph                           │
│                                                         │
│   ┌──────────┐        ┌──────────┐        ┌──────────┐ │
│   │  Node A  │───────▶│  Node B  │───────▶│  Node C  │ │
│   │(research)│        │ (analyze)│        │(synthesize)│ │
│   └──────────┘        └──────────┘        └──────────┘ │
│        ▲                                     │         │
│        │            ┌──────────┐             │         │
│        └────────────│  Node D  │◀────────────┘         │
│                     │  (review)│                        │
│                     └──────────┘                        │
│                                                         │
│   State: {messages, iterations, result, next_node}     │
└─────────────────────────────────────────────────────────┘
```

#### State

State is the shared context that flows through every node. Each node receives the current state and returns updates (not the full state).

```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """State schema — every node reads from and writes to this."""
    messages: Annotated[List, add_messages]  # Accumulates messages
    iterations: int                           # Counter
    result: str                               # Final output
    next_node: str                            # Routing hint
```

The `Annotated[..., add_messages]` reducer is critical: it tells LangGraph how to merge updates. For messages, it **appends** rather than replaces.

#### Nodes

Nodes are pure functions that take state and return state updates:

```python
def my_node(state: AgentState) -> dict:
    """Node function signature."""
    # Read from state
    current_messages = state["messages"]
    
    # Do work (LLM call, tool execution, etc.)
    result = do_something(current_messages)
    
    # Return state updates (NOT the full state)
    return {
        "messages": [result],
        "iterations": state["iterations"] + 1
    }
```

#### Edges

| Edge Type | Description | Example |
|-----------|-------------|---------|
| **Normal Edge** | Always goes from A to B | `graph.add_edge("a", "b")` |
| **Conditional Edge** | Routes based on state | `graph.add_conditional_edges("a", router)` |
| **Entry Point** | Where execution starts | `graph.set_entry_point("a")` |
| **END** | Terminal node | `graph.add_edge("c", END)` |

### Installation and Setup

```bash
# Core LangGraph
pip install langgraph

# Checkpointers (persistence)
pip install langgraph-checkpoint-sqlite
pip install langgraph-checkpoint-postgres

# Prebuilt components
pip install langgraph-prebuilt

# LangChain integration (for LLMs, tools)
pip install langchain langchain-openai langchain-anthropic
```

```python
# Verify installation
import langgraph
print(f"LangGraph version: {langgraph.__version__}")

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
print("All imports successful!")
```

### First LangGraph Example: Simple State Machine

Let's build a minimal graph that classifies a query, researches it, and generates a response.

```python
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

# 1. Define State
class SimpleState(TypedDict):
    messages: Annotated[List, add_messages]
    classification: str
    response: str

# 2. Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 3. Define Nodes
def classify_node(state: SimpleState) -> dict:
    """Classify the user query type."""
    system_prompt = """Classify the query into one of: factual, creative, analytical.
    Respond with only the category name."""
    
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        *state["messages"]
    ])
    
    return {
        "classification": response.content.strip().lower(),
        "messages": [response]
    }

def research_node(state: SimpleState) -> dict:
    """Generate a response based on classification."""
    category = state["classification"]
    
    prompts = {
        "factual": "Provide a factual, concise answer with key details.",
        "creative": "Provide a creative, engaging response with examples.",
        "analytical": "Provide a structured analysis with pros and cons."
    }
    
    system_prompt = prompts.get(category, "Provide a helpful response.")
    
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        *state["messages"]
    ])
    
    return {
        "response": response.content,
        "messages": [response]
    }

# 4. Define Routing
def route_after_classify(state: SimpleState) -> str:
    """Always go to research after classification."""
    return "research"

# 5. Build Graph
graph = StateGraph(SimpleState)

# Add nodes
graph.add_node("classify", classify_node)
graph.add_node("research", research_node)

# Add edges
graph.set_entry_point("classify")
graph.add_conditional_edges("classify", route_after_classify, {"research": "research"})
graph.add_edge("research", END)

# Compile
app = graph.compile()

# Visualize the graph
# print(app.get_graph().draw_ascii())

# 6. Execute
result = app.invoke({
    "messages": [{"role": "user", "content": "What is quantum computing?"}]
})

print(f"Classification: {result['classification']}")
print(f"Response: {result['response'][:200]}...")
```

**Output:**
```
Classification: factual
Response: Quantum computing is a type of computing that uses quantum mechanical phenomena...
```

### Graph Visualization

```
┌──────────────────────────────────────────────────┐
│                  Simple Graph                    │
│                                                  │
│  [ENTRY] ──▶ ┌──────────┐     ┌──────────┐      │
│              │ classify │────▶│ research │──▶ END│
│              └──────────┘     └──────────┘      │
│                                                  │
│  State: {messages, classification, response}    │
└──────────────────────────────────────────────────┘
```

### Key Takeaways — 6.1

| Concept | Key Point |
|---------|-----------|
| **LangGraph Purpose** | Stateful, cyclic graph orchestration for LLM applications |
| **vs LangChain** | LangGraph adds cycles, persistence, human-in-the-loop, and fine-grained control |
| **StateGraph** | Central abstraction defining state, nodes, and edges |
| **State** | TypedDict/Pydantic schema; nodes return updates, not full state |
| **Nodes** | Pure functions: `state → dict` (state updates) |
| **Edges** | Normal (always), Conditional (router function), Entry, END |
| **Compilation** | `graph.compile()` creates an executable application |

---

## 6.2 Building Blocks: Nodes, Edges, State Management

### State Definition: TypedDict vs. Pydantic

LangGraph supports two state definition approaches, each with trade-offs:

| Aspect | TypedDict | Pydantic BaseModel |
|--------|-----------|-------------------|
| **Syntax** | `class State(TypedDict)` | `class State(BaseModel)` |
| **Validation** | Runtime type hints only | Full validation with constraints |
| **Reducers** | `Annotated[type, reducer]` | Same, but with model validators |
| **Default Values** | Not supported directly | `field: str = "default"` |
| **Nested Models** | Manual TypedDict nesting | Native Pydantic model nesting |
| **Serialization** | Manual | `model_dump()` / `model_validate()` |
| **Best For** | Simple state schemas | Complex state with validation |

#### TypedDict State (Recommended for Most Cases)

```python
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
import operator

class ResearchState(TypedDict):
    """State for a research agent."""
    messages: Annotated[List, add_messages]
    query: str
    search_results: List[dict]
    summary: str
    critique: Optional[str]
    revised_summary: Optional[str]
    iteration: Annotated[int, operator.add]  # Auto-incrementing counter
    is_complete: bool
```

#### Pydantic State (For Complex Validation)

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import operator

class ResearchStatePydantic(BaseModel):
    """State with Pydantic validation."""
    query: str = Field(..., min_length=5, description="The research query")
    search_results: List[dict] = Field(default_factory=list)
    summary: str = Field(default="", max_length=5000)
    iteration: int = Field(default=0, ge=0, le=10)
    is_complete: bool = Field(default=False)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    class Config:
        # Allow LangGraph to merge updates
        extra = "allow"
```

#### Built-in Reducers

Reducers define how state updates are merged. LangGraph provides several:

| Reducer | Behavior | Use Case |
|---------|----------|----------|
| `add_messages` | Appends messages to list | Conversation history |
| `operator.add` | Adds numeric values | Counters, accumulators |
| `operator.or_` | Merges dictionaries | Config accumulation |
| Custom reducer | Your own merge logic | Complex state merging |

```python
from typing import TypedDict, Annotated
import operator

def merge_dicts(existing: dict, update: dict) -> dict:
    """Custom reducer: deep merge dictionaries."""
    merged = existing.copy()
    merged.update(update)
    return merged

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    counter: Annotated[int, operator.add]
    metadata: Annotated[dict, merge_dicts]
    flags: Annotated[set, lambda existing, update: existing | update]
```

### Node Functions

#### Node Signature and Contract

```python
def node_function(state: StateType) -> dict:
    """
    Node function contract:
    
    INPUT:  Current state (full state object)
    OUTPUT: Dictionary of state updates (NOT the full state)
    
    Rules:
    1. Return ONLY the fields that changed
    2. LangGraph merges updates using reducers
    3. Return empty dict {} if no changes needed
    4. Can be sync or async (def / async def)
    """
    
    # Read from state
    query = state["query"]
    messages = state["messages"]
    
    # Do work
    result = process(query, messages)
    
    # Return updates
    return {
        "summary": result.summary,
        "is_complete": result.is_complete,
        "iteration": 1  # Will be added to existing counter
    }
```

#### Node Types

| Node Type | Purpose | Example |
|-----------|---------|---------|
| **LLM Node** | Calls an LLM for reasoning/generation | `generate_response(state)` |
| **Tool Node** | Executes external tools | `execute_search(state)` |
| **Router Node** | Determines next step | `route_based_on_state(state)` |
| **Validator Node** | Checks output quality | `validate_output(state)` |
| **Human Node** | Waits for human input | `await_approval(state)` |

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

llm = ChatOpenAI(model="gpt-4o")

# LLM Node
def generate_node(state: ResearchState) -> dict:
    """Generate a summary from research findings."""
    system_prompt = """You are a research summarizer. Create a concise, 
    accurate summary from the provided search results."""
    
    context = "\n".join(
        f"- {r['title']}: {r['snippet']}" 
        for r in state.get("search_results", [])
    )
    
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Query: {state['query']}\n\nSources:\n{context}"}
    ])
    
    return {"summary": response.content}

# Tool Node
@tool
def web_search(query: str, num_results: int = 5) -> List[dict]:
    """Search the web for information."""
    # In production: use Tavily, SerpAPI, or similar
    return [{"title": f"Result for {query}", "snippet": "..."}]

def search_node(state: ResearchState) -> dict:
    """Execute search and store results."""
    results = web_search.invoke(state["query"])
    return {"search_results": results}

# Validator Node
def validate_node(state: ResearchState) -> dict:
    """Validate the summary quality."""
    evaluation = llm.invoke(f"""
    Evaluate this summary for:
    1. Completeness (covers all key points)
    2. Accuracy (no hallucinations)
    3. Clarity (well-structured)
    
    Summary: {state['summary']}
    
    Respond with JSON: {{"score": 1-10, "is_good": true/false, "feedback": "..."}}
    """)
    
    import json
    eval_result = json.loads(evaluation.content)
    
    return {
        "critique": eval_result.get("feedback", ""),
        "is_complete": eval_result.get("is_good", False)
    }
```

### Edges: Normal, Conditional, Entry/Exit

#### Normal Edges

Always execute the target node after the source node completes.

```python
graph.add_edge("search", "generate")   # After search, always generate
graph.add_edge("generate", "validate") # After generate, always validate
```

#### Conditional Edges

Route to different nodes based on state analysis.

```python
def router(state: ResearchState) -> str:
    """Determine the next node based on validation results."""
    if state.get("is_complete"):
        return "end"
    elif state.get("iteration", 0) >= 3:
        return "end"  # Max iterations reached
    else:
        return "revise"  # Need to improve

graph.add_conditional_edges(
    "validate",           # Source node
    router,               # Routing function
    {                     # Route mapping
        "end": END,
        "revise": "generate"
    }
)
```

#### Entry Point

```python
graph.set_entry_point("search")  # Execution starts here
```

#### Complete Edge Configuration

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(ResearchState)

# Add nodes
graph.add_node("search", search_node)
graph.add_node("generate", generate_node)
graph.add_node("validate", validate_node)
graph.add_node("revise", revise_node)

# Configure edges
graph.set_entry_point("search")
graph.add_edge("search", "generate")
graph.add_edge("generate", "validate")
graph.add_conditional_edges("validate", router, {
    "end": END,
    "revise": "generate"
})
```

### StateGraph Compilation and Invocation

#### Compilation

```python
# Basic compilation
app = graph.compile()

# With checkpointing (persistence)
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# With interrupt points (human-in-the-loop)
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["validate"],  # Pause before validation
    interrupt_after=["generate"]    # Pause after generation
)
```

#### Invocation Modes

| Mode | Method | Use Case |
|------|--------|----------|
| **invoke** | `app.invoke(input)` | Run to completion, return final state |
| **stream** | `app.stream(input)` | Step-by-step state snapshots |
| **astream** | `async for event in app.astream(input)` | Async step-by-step |
| **stream_events** | `app.stream_events(input)` | Fine-grained events (tokens, tool calls) |

```python
# 1. Invoke — run to completion
final_state = app.invoke({
    "query": "What are the latest advances in fusion energy?",
    "messages": [{"role": "user", "content": "What are the latest advances in fusion energy?"}],
    "iteration": 0,
    "is_complete": False
})
print(final_state["summary"])

# 2. Stream — see each step
for step in app.stream({
    "query": "Explain CRISPR gene editing",
    "messages": [{"role": "user", "content": "Explain CRISPR gene editing"}],
    "iteration": 0,
    "is_complete": False
}):
    print(f"Step output: {step}")
    print("---")

# 3. Stream with mode control
for step in app.stream(input_data, stream_mode="values"):
    # "values" = full state after each step
    print(f"Full state: {step.keys()}")

for step in app.stream(input_data, stream_mode="updates"):
    # "updates" = only what changed in this step
    print(f"Updates: {step}")

for step in app.stream(input_data, stream_mode="debug"):
    # "debug" = internal execution details
    print(f"Debug: {step}")
```

### Checkpointing and Persistence

Checkpointing saves the graph state at every step, enabling:
- **Resumability**: Pause and resume execution
- **Time Travel**: Replay from any checkpoint
- **Human-in-the-Loop**: Pause for human input, then continue
- **Debugging**: Inspect state at any point

#### MemorySaver (In-Memory)

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Run with a thread ID (isolates conversations)
config = {"configurable": {"thread_id": "conversation-1"}}

result = app.invoke({
    "query": "What is machine learning?",
    "messages": [{"role": "user", "content": "What is machine learning?"}],
    "iteration": 0,
    "is_complete": False
}, config=config)

# Later: resume or inspect
state = app.get_state(config)
print(f"Current state: {state.values}")
print(f"Next node: {state.next}")
```

#### SQLiteSaver (Persistent)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": "session-42"}}
    
    result = app.invoke(input_data, config=config)
    
    # All checkpoints persist across process restarts
```

#### Inspecting and Replaying Checkpoints

```python
# Get current state
state = app.get_state(config)
print(f"Values: {state.values}")
print(f"Next: {state.next}")

# Get state history (all checkpoints)
history = list(app.get_state_history(config))
for checkpoint in history:
    print(f"Checkpoint: {checkpoint.values}")
    print(f"Next: {checkpoint.next}")
    print("---")

# Replay from a specific checkpoint
target_checkpoint = history[2]  # Third checkpoint
replay_config = {
    "configurable": {
        "thread_id": "session-42",
        "checkpoint_id": target_checkpoint.config["configurable"]["checkpoint_id"]
    }
}
result = app.invoke(None, config=replay_config)

# Update state at a checkpoint (time travel + edit)
app.update_state(config, {"summary": "Manually corrected summary"})
```

### Streaming with LangGraph

#### Stream Modes

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", streaming=True)

# Mode 1: "values" — Full state after each node
for event in app.stream(input_data, stream_mode="values"):
    print(f"State keys: {event.keys()}")

# Mode 2: "updates" — Only changed fields per node
for event in app.stream(input_data, stream_mode="updates"):
    for node_name, update in event.items():
        print(f"Node '{node_name}' updated: {update.keys()}")

# Mode 3: "debug" — Internal execution info
for event in app.stream(input_data, stream_mode="debug"):
    print(f"Event type: {event['type']}")
    print(f"Payload: {event['payload']}")
```

#### Streaming LLM Tokens

```python
from langgraph.types import stream_mode

# Stream individual LLM tokens within nodes
for event in app.stream_events(input_data, version="v2"):
    kind = event["event"]
    
    if kind == "on_chat_model_stream":
        token = event["data"]["chunk"].content
        if token:
            print(token, end="", flush=True)
    
    elif kind == "on_tool_start":
        print(f"\n[Tool starting: {event['name']}]")
    
    elif kind == "on_tool_end":
        print(f"\n[Tool completed: {event['name']}]")
    
    elif kind == "on_chain_end":
        print(f"\n[Node completed: {event['name']}]")
```

#### Async Streaming

```python
import asyncio

async def run_graph():
    async for event in app.astream(input_data, stream_mode="updates"):
        for node_name, update in event.items():
            print(f"Node '{node_name}': {update}")

asyncio.run(run_graph())
```

### Complete Code Example: Multi-Step Research Agent

This example demonstrates all building blocks in a production-quality research agent.

```python
"""
Multi-Step Research Agent with LangGraph
=========================================
A research agent that:
1. Searches for information
2. Generates a draft summary
3. Critiques its own work
4. Revises if needed (loop)
5. Produces a final report
"""

from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json
import operator

# ─────────────────────────────────────────────
# 1. State Definition
# ─────────────────────────────────────────────

class ResearchState(TypedDict):
    """Complete state for the research agent."""
    messages: Annotated[List, add_messages]
    query: str
    search_results: List[dict]
    draft: str
    critique: str
    revised_draft: str
    iteration: Annotated[int, operator.add]
    quality_score: float
    is_approved: bool
    final_report: str

# ─────────────────────────────────────────────
# 2. LLM and Tools
# ─────────────────────────────────────────────

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

@tool
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information on a topic."""
    # Placeholder — replace with Tavily, SerpAPI, etc.
    results = [
        {"title": f"Source on {query}", "snippet": f"Detailed information about {query}..."},
        {"title": f"Research on {query}", "snippet": f"Latest findings regarding {query}..."},
    ]
    return json.dumps(results)

@tool
def extract_key_points(text: str) -> str:
    """Extract key points from a text."""
    return llm.invoke(f"Extract the 5 most important points from:\n{text}").content

# ─────────────────────────────────────────────
# 3. Node Functions
# ─────────────────────────────────────────────

def search_node(state: ResearchState) -> dict:
    """Search for information related to the query."""
    print(f"🔍 Searching for: {state['query']}")
    
    results = search_web.invoke(state["query"])
    search_data = json.loads(results)
    
    return {
        "search_results": search_data,
        "iteration": 1,
        "messages": [AIMessage(content=f"Found {len(search_data)} sources.")]
    }

def draft_node(state: ResearchState) -> dict:
    """Generate an initial draft summary."""
    print("📝 Generating draft...")
    
    context = "\n\n".join(
        f"Source: {s['title']}\n{s['snippet']}"
        for s in state["search_results"]
    )
    
    response = llm.invoke([
        SystemMessage(content="""You are a research analyst. Write a comprehensive 
        draft summary based on the provided sources. Include key findings, 
        statistics, and different perspectives."""),
        HumanMessage(content=f"Query: {state['query']}\n\nSources:\n{context}")
    ])
    
    return {
        "draft": response.content,
        "iteration": 1,
        "messages": [AIMessage(content="Draft generated.")]
    }

def critique_node(state: ResearchState) -> dict:
    """Critique the draft for quality."""
    print("🔎 Critiquing draft...")
    
    response = llm.invoke([
        SystemMessage(content="""You are a critical reviewer. Evaluate the draft summary on:
        1. Completeness — Does it cover all important aspects?
        2. Accuracy — Are claims supported by sources?
        3. Clarity — Is it well-organized and easy to understand?
        4. Depth — Does it provide sufficient detail?
        
        Respond with JSON:
        {
            "score": <1-10>,
            "strengths": ["..."],
            "weaknesses": ["..."],
            "suggestions": ["..."],
            "needs_revision": <true/false>
        }"""),
        HumanMessage(content=f"Query: {state['query']}\n\nDraft:\n{state['draft']}")
    ])
    
    critique_data = json.loads(response.content)
    
    return {
        "critique": json.dumps(critique_data, indent=2),
        "quality_score": critique_data["score"],
        "is_approved": not critique_data["needs_revision"],
        "iteration": 1,
        "messages": [AIMessage(content=f"Critique score: {critique_data['score']}/10")]
    }

def revise_node(state: ResearchState) -> dict:
    """Revise the draft based on critique feedback."""
    print("✏️ Revising draft...")
    
    critique_data = json.loads(state["critique"])
    
    response = llm.invoke([
        SystemMessage(content="""You are improving a research summary based on critique feedback.
        Address all weaknesses and incorporate all suggestions while maintaining accuracy."""),
        HumanMessage(content=f"""Original Query: {state['query']}

Original Draft:
{state['draft']}

Critique:
Strengths: {critique_data['strengths']}
Weaknesses: {critique_data['weaknesses']}
Suggestions: {critique_data['suggestions']}

Generate an improved version.""")
    ])
    
    return {
        "revised_draft": response.content,
        "draft": response.content,  # Update draft for next iteration
        "iteration": 1,
        "messages": [AIMessage(content=f"Revision complete. Iteration: {state['iteration'] + 1}")]
    }

def finalize_node(state: ResearchState) -> dict:
    """Generate the final report."""
    print("📋 Finalizing report...")
    
    best_draft = state.get("revised_draft") or state["draft"]
    
    response = llm.invoke([
        SystemMessage(content="""Format this as a professional research report with:
        - Executive Summary
        - Key Findings
        - Detailed Analysis
        - Conclusion
        - Sources Referenced"""),
        HumanMessage(content=f"Query: {state['query']}\n\nContent:\n{best_draft}")
    ])
    
    return {
        "final_report": response.content,
        "messages": [AIMessage(content="Final report generated.")]
    }

# ─────────────────────────────────────────────
# 4. Routing Logic
# ─────────────────────────────────────────────

def route_after_critique(state: ResearchState) -> str:
    """Decide whether to revise or finalize."""
    max_iterations = 3
    
    if state.get("is_approved"):
        return "finalize"
    elif state.get("iteration", 0) >= max_iterations:
        return "finalize"  # Force finish after max iterations
    else:
        return "revise"

# ─────────────────────────────────────────────
# 5. Build and Compile Graph
# ─────────────────────────────────────────────

def build_research_agent():
    """Construct the research agent graph."""
    
    graph = StateGraph(ResearchState)
    
    # Add nodes
    graph.add_node("search", search_node)
    graph.add_node("draft", draft_node)
    graph.add_node("critique", critique_node)
    graph.add_node("revise", revise_node)
    graph.add_node("finalize", finalize_node)
    
    # Configure flow
    graph.set_entry_point("search")
    graph.add_edge("search", "draft")
    graph.add_edge("draft", "critique")
    graph.add_conditional_edges("critique", route_after_critique, {
        "finalize": "finalize",
        "revise": "revise"
    })
    graph.add_edge("revise", "critique")  # Loop back for re-evaluation
    graph.add_edge("finalize", END)
    
    # Compile with persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)

# ─────────────────────────────────────────────
# 6. Execute
# ─────────────────────────────────────────────

if __name__ == "__main__":
    agent = build_research_agent()
    
    # Visualize
    # print(agent.get_graph().draw_ascii())
    
    input_data = {
        "query": "What are the latest breakthroughs in room-temperature superconductors?",
        "messages": [HumanMessage(
            content="What are the latest breakthroughs in room-temperature superconductors?"
        )],
        "iteration": 0,
        "is_approved": False,
        "quality_score": 0.0
    }
    
    config = {"configurable": {"thread_id": "research-001"}}
    
    # Stream execution
    print("=" * 60)
    print("RESEARCH AGENT EXECUTION")
    print("=" * 60)
    
    for step in agent.stream(input_data, config=config, stream_mode="updates"):
        for node_name, update in step.items():
            print(f"\n▶ Node: {node_name}")
            for key, value in update.items():
                if key != "messages":
                    val_str = str(value)[:200]
                    print(f"  {key}: {val_str}")
    
    # Get final state
    final_state = agent.get_state(config)
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(final_state.values.get("final_report", "No report generated"))
    
    # Inspect history
    print("\n" + "=" * 60)
    print("EXECUTION HISTORY")
    print("=" * 60)
    for i, checkpoint in enumerate(agent.get_state_history(config)):
        print(f"Checkpoint {i}: next={checkpoint.next}, "
              f"iteration={checkpoint.values.get('iteration', 'N/A')}")
```

**Execution Flow:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Research Agent Graph                         │
│                                                                 │
│  [ENTRY] ──▶ ┌──────┐    ┌──────┐    ┌──────────┐             │
│              │search│───▶│draft │───▶│ critique │             │
│              └──────┘    └──────┘    └────┬─────┘             │
│                                           │                     │
│                          ┌────────────────┼────────────────┐   │
│                          │                │                │   │
│                     ┌────▼─────┐    ┌─────▼──────┐         │   │
│                     │ finalize │    │   revise   │         │   │
│                     └────┬─────┘    └─────┬──────┘         │   │
│                          │               │                  │   │
│                          ▼               └──────────────────┘   │
│                         END                                     │
│                                                                 │
│  Loop: critique → revise → critique (max 3 iterations)         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Takeaways — 6.2

| Concept | Key Point |
|---------|-----------|
| **State** | Use TypedDict for simplicity, Pydantic for validation |
| **Reducers** | `add_messages` for lists, `operator.add` for counters |
| **Nodes** | Return only changed fields; LangGraph merges with reducers |
| **Conditional Edges** | Router function returns string key mapped to target node |
| **Compilation** | `compile()` creates executable app; add checkpointer for persistence |
| **Streaming** | `stream_mode="values"` for full state, `"updates"` for changes |
| **Checkpointing** | MemorySaver for dev, SQLiteSaver/PostgresSaver for production |
| **Time Travel** | `get_state_history()` to replay, `update_state()` to edit |

---

## 6.3 Cyclic vs. DAG Graphs — Human-in-the-Loop Patterns

### DAG Graphs: When to Use

**DAG (Directed Acyclic Graph)** graphs have no cycles — execution flows in one direction from entry to END.

#### When to Use DAGs

| Scenario | Why DAG |
|----------|---------|
| Linear pipelines | Sequential processing with no retry needed |
| Data transformation | ETL-style: extract → transform → load |
| Simple RAG | Retrieve → Augment → Generate |
| Fixed workflows | Approval chains with predetermined steps |
| Batch processing | Parallel branches that converge |

#### DAG Example: Document Processing Pipeline

```python
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class DocState(TypedDict):
    messages: Annotated[List, add_messages]
    document: str
    extracted_text: str
    summary: str
    translation: str
    final_output: str

def extract_node(state: DocState) -> dict:
    """Extract text from document."""
    # OCR, PDF parsing, etc.
    return {"extracted_text": state["document"]}

def summarize_node(state: DocState) -> dict:
    """Summarize extracted text."""
    summary = llm.invoke(f"Summarize: {state['extracted_text']}").content
    return {"summary": summary}

def translate_node(state: DocState) -> dict:
    """Translate summary to Spanish."""
    translation = llm.invoke(f"Translate to Spanish: {state['summary']}").content
    return {"translation": translation}

def format_node(state: DocState) -> dict:
    """Format final output."""
    output = f"Summary: {state['summary']}\nTranslation: {state['translation']}"
    return {"final_output": output}

# Build DAG
dag = StateGraph(DocState)
dag.add_node("extract", extract_node)
dag.add_node("summarize", summarize_node)
dag.add_node("translate", translate_node)
dag.add_node("format", format_node)

dag.set_entry_point("extract")
dag.add_edge("extract", "summarize")
dag.add_edge("summarize", "translate")
dag.add_edge("translate", "format")
dag.add_edge("format", END)

app = dag.compile()
```

**DAG Flow:**
```
[ENTRY] ──▶ ┌───────┐    ┌──────────┐    ┌───────────┐    ┌────────┐    END
            │extract │───▶│summarize │───▶│ translate │───▶│ format │
            └───────┘    └──────────┘    └───────────┘    └────────┘
            
No loops. No retries. One pass from start to finish.
```

#### Parallel DAG Branches

```python
from langgraph.graph import StateGraph, END

class ParallelState(TypedDict):
    messages: Annotated[List, add_messages]
    query: str
    web_result: str
    db_result: str
    combined: str

def web_search_node(state: ParallelState) -> dict:
    return {"web_result": f"Web results for: {state['query']}"}

def db_query_node(state: ParallelState) -> dict:
    return {"db_result": f"Database results for: {state['query']}"}

def combine_node(state: ParallelState) -> dict:
    combined = f"Web: {state['web_result']}\nDB: {state['db_result']}"
    return {"combined": combined}

parallel_dag = StateGraph(ParallelState)
parallel_dag.add_node("web", web_search_node)
parallel_dag.add_node("db", db_query_node)
parallel_dag.add_node("combine", combine_node)

parallel_dag.set_entry_point("web")
parallel_dag.add_edge("web", "db")
parallel_dag.add_edge("db", "combine")
parallel_dag.add_edge("combine", END)
```

### Cyclic Graphs: Loops, Retry, Self-Correction

**Cyclic graphs** contain loops — nodes can route back to previous nodes, enabling retry, self-correction, and iterative refinement.

#### When to Use Cycles

| Scenario | Why Cycle |
|----------|-----------|
| Self-correction | Generate → critique → revise → re-critique |
| Tool retry | Tool fails → retry with different parameters |
| Clarification | LLM asks user for more info → re-process |
| Iterative refinement | Draft → review → improve → re-review |
| Agentic loops | ReAct-style: think → act → observe → repeat |

#### Cycle Example: Self-Correcting Code Generator

```python
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage
import operator

class CodeState(TypedDict):
    messages: Annotated[List, add_messages]
    requirement: str
    code: str
    test_result: str
    error_message: str
    attempts: Annotated[int, operator.add]
    is_passing: bool

def generate_code_node(state: CodeState) -> dict:
    """Generate code based on requirements."""
    error_context = ""
    if state.get("error_message"):
        error_context = f"\nPrevious error: {state['error_message']}\nFix this issue."
    
    response = llm.invoke([
        SystemMessage(content="You are an expert Python developer. Write clean, tested code."),
        HumanMessage(content=f"""
        Requirement: {state['requirement']}
        {error_context}
        
        Write the complete Python code. Include error handling.
        """)
    ])
    
    return {
        "code": response.content,
        "attempts": 1
    }

def test_code_node(state: CodeState) -> dict:
    """Execute and test the generated code."""
    try:
        # In production: use a sandboxed execution environment
        exec_globals = {}
        exec(state["code"], exec_globals)
        
        # Run a basic test
        if "binary_search" in state["requirement"].lower():
            test_func = exec_globals.get("binary_search")
            if test_func:
                result = test_func([1, 2, 3, 4, 5], 3)
                if result == 2:
                    return {"test_result": "PASS", "is_passing": True}
        
        return {"test_result": "PASS (basic)", "is_passing": True}
        
    except Exception as e:
        return {
            "test_result": "FAIL",
            "error_message": str(e),
            "is_passing": False
        }

def route_after_test(state: CodeState) -> str:
    """Route based on test results."""
    if state.get("is_passing"):
        return "done"
    elif state.get("attempts", 0) >= 5:
        return "done"  # Give up after 5 attempts
    else:
        return "fix"

def build_code_agent():
    """Build self-correcting code agent."""
    graph = StateGraph(CodeState)
    
    graph.add_node("generate", generate_code_node)
    graph.add_node("test", test_code_node)
    
    graph.set_entry_point("generate")
    graph.add_edge("generate", "test")
    graph.add_conditional_edges("test", route_after_test, {
        "done": END,
        "fix": "generate"
    })
    
    return graph.compile()

# Usage
code_agent = build_code_agent()
result = code_agent.invoke({
    "requirement": "Write a binary search function",
    "messages": [HumanMessage(content="Write a binary search function")],
    "attempts": 0,
    "is_passing": False
})
print(f"Final code:\n{result['code']}")
print(f"Test result: {result['test_result']}")
print(f"Attempts: {result['attempts']}")
```

**Cyclic Flow:**
```
┌─────────────────────────────────────────────────────┐
│               Self-Correcting Agent                 │
│                                                     │
│  [ENTRY] ──▶ ┌──────────┐     ┌──────┐            │
│              │ generate │────▶│ test │            │
│              └──────────┘     └──┬───┘            │
│                   ▲              │                 │
│                   │    ┌─────────┴─────────┐      │
│                   │    │                   │      │
│                   │  PASS               FAIL       │
│                   │    │                   │      │
│                   │    ▼                   ▼      │
│                   │   END          ┌──────────┐   │
│                   │                │  (retry) │   │
│                   └────────────────│ generate │   │
│                                    └──────────┘   │
│                                                   │
│  Max 5 attempts, then force END                   │
└─────────────────────────────────────────────────────┘
```

### Human-in-the-Loop Patterns

LangGraph provides first-class support for human-in-the-loop workflows through three mechanisms:

| Mechanism | How It Works | Use Case |
|-----------|-------------|----------|
| `interrupt_before` | Pauses execution before specified nodes | Review before sensitive actions |
| `interrupt_after` | Pauses execution after specified nodes | Review generated content |
| `interrupt()` | Node-level pause with custom prompt | Dynamic approval requests |

#### Pattern 1: `interrupt_before` — Review Before Action

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

# Build graph with interrupt before the "deploy" node
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["deploy"]  # Pause before deployment
)

config = {"configurable": {"thread_id": "deploy-session-1"}}

# Step 1: Run until interruption
for event in app.stream({
    "query": "Deploy the latest model",
    "messages": [HumanMessage(content="Deploy the latest model")]
}, config):
    print(f"Step: {event}")

# At this point, execution is paused before "deploy"
# Check what's about to happen
state = app.get_state(config)
print(f"Paused before: {state.next}")
print(f"Current state: {state.values}")

# Step 2: Human reviews and approves
# Resume execution
result = app.invoke(
    Command(resume={"approved": True, "reviewer": "admin"}),
    config
)
```

#### Pattern 2: `interrupt_after` — Review Generated Content

```python
# Pause after the "generate_email" node
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_after=["generate_email"]  # Pause after email generation
)

# Run until interruption
for event in app.stream(input_data, config):
    print(event)

# Human reviews the generated email
state = app.get_state(config)
generated_email = state.values.get("email_draft")
print(f"Generated email:\n{generated_email}")

# Human edits if needed
app.update_state(config, {
    "email_draft": generated_email.replace("Dear Customer", "Dear Valued Customer")
})

# Resume
result = app.invoke(Command(resume=True), config)
```

#### Pattern 3: `interrupt()` — Dynamic Approval in Node

```python
from langgraph.types import interrupt

def approval_node(state: ResearchState) -> dict:
    """Node that requests human approval."""
    
    # This call PAUSES the graph and waits for human input
    human_input = interrupt({
        "action": "approve_publication",
        "content": state.get("final_report", ""),
        "question": "Do you approve this report for publication?"
    })
    
    if human_input.get("approved"):
        return {"is_approved": True, "messages": [AIMessage(content="Approved by human reviewer")]}
    else:
        return {
            "is_approved": False,
            "critique": human_input.get("feedback", "Needs revision"),
            "messages": [AIMessage(content="Rejected. Feedback: " + human_input.get("feedback", ""))]
        }
```

### Time Travel: Replaying from Checkpoints

Time travel lets you inspect, replay, or branch from any point in the graph's execution history.

```python
# Run the graph
config = {"configurable": {"thread_id": "time-travel-demo"}}
result = app.invoke(input_data, config)

# 1. View full execution history
print("=== EXECUTION HISTORY ===")
for i, snapshot in enumerate(app.get_state_history(config)):
    print(f"\nCheckpoint {i}:")
    print(f"  Next node: {snapshot.next}")
    print(f"  State keys: {list(snapshot.values.keys())}")
    print(f"  Checkpoint ID: {snapshot.config['configurable']['checkpoint_id']}")

# 2. Replay from a specific checkpoint
target = list(app.get_state_history(config))[2]  # Third checkpoint
replay_config = {
    "configurable": {
        "thread_id": "time-travel-demo",
        "checkpoint_id": target.config["configurable"]["checkpoint_id"]
    }
}

# Replay from this point forward
replayed = app.invoke(None, config=replay_config)

# 3. Branch: Edit state and continue from checkpoint
branch_config = {
    "configurable": {
        "thread_id": "time-travel-demo",
        "checkpoint_id": target.config["configurable"]["checkpoint_id"]
    }
}

# Modify state at this checkpoint
app.update_state(branch_config, {
    "query": "Modified query for branch experiment",
    "iteration": 0
})

# Continue with modified state
branched = app.invoke(None, config=branch_config)
```

**Time Travel Visualization:**
```
Execution Timeline:
─────────────────────────────────────────────────────
Checkpoint 0: [ENTRY] → search     (initial state)
Checkpoint 1: search → draft       (search complete)
Checkpoint 2: draft → critique     (draft ready)     ◄── Replay from here
Checkpoint 3: critique → revise    (needs revision)
Checkpoint 4: revise → critique    (revision done)
Checkpoint 5: critique → finalize  (approved)
Checkpoint 6: finalize → END       (complete)
─────────────────────────────────────────────────────

Replay: Start from Checkpoint 2 → re-run draft → critique → ...
Branch: Edit state at Checkpoint 2 → continue with new parameters
```

### State Modification at Breakpoints

You can modify state at any checkpoint, enabling human corrections, parameter tuning, or A/B testing.

```python
# Run until breakpoint
config = {"configurable": {"thread_id": "edit-demo"}}
for event in app.stream(input_data, config, stream_mode="updates"):
    print(event)

# Inspect current state
state = app.get_state(config)
print(f"Current draft: {state.values.get('draft', '')[:100]}...")

# Edit the state
app.update_state(config, {
    "draft": "Manually corrected draft with accurate information.",
    "iteration": state.values.get("iteration", 0) + 1
})

# Verify the edit
updated_state = app.get_state(config)
print(f"Updated draft: {updated_state.values['draft']}")

# Continue execution
result = app.invoke(Command(resume=True), config)
```

### Pattern: Review-and-Revise with Human Approval

```python
"""
Review-and-Revise Pattern
==========================
A complete human-in-the-loop workflow where:
1. Agent generates content
2. Human reviews and can edit
3. Agent incorporates feedback
4. Human gives final approval
"""

from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

class ReviewState(TypedDict):
    messages: Annotated[List, add_messages]
    topic: str
    draft: str
    human_feedback: Optional[str]
    revised_draft: str
    human_approved: bool
    final_content: str

llm = ChatOpenAI(model="gpt-4o")

def generate_draft(state: ReviewState) -> dict:
    """Generate initial draft."""
    response = llm.invoke([
        SystemMessage(content="Write a comprehensive article on the given topic."),
        HumanMessage(content=f"Topic: {state['topic']}")
    ])
    return {"draft": response.content}

def human_review(state: ReviewState) -> dict:
    """Pause for human review and feedback."""
    feedback = interrupt({
        "action": "review_draft",
        "draft": state["draft"],
        "instructions": "Review the draft. Provide feedback or edit directly."
    })
    
    return {
        "human_feedback": feedback.get("feedback", ""),
        "draft": feedback.get("edited_draft", state["draft"]),
        "human_approved": feedback.get("approved", False)
    }

def revise_draft(state: ReviewState) -> dict:
    """Revise based on human feedback."""
    response = llm.invoke([
        SystemMessage(content="Revise the draft based on human feedback."),
        HumanMessage(content=f"""
        Original Draft: {state['draft']}
        Human Feedback: {state['human_feedback']}
        
        Generate an improved version.""")
    ])
    return {"revised_draft": response.content}

def finalize(state: ReviewState) -> dict:
    """Produce final content."""
    final = state.get("revised_draft") or state["draft"]
    return {"final_content": final}

def route_after_review(state: ReviewState) -> str:
    """Decide next step based on human approval."""
    if state.get("human_approved"):
        return "finalize"
    else:
        return "revise"

# Build graph
review_graph = StateGraph(ReviewState)
review_graph.add_node("generate", generate_draft)
review_graph.add_node("review", human_review)
review_graph.add_node("revise", revise_draft)
review_graph.add_node("finalize", finalize)

review_graph.set_entry_point("generate")
review_graph.add_edge("generate", "review")
review_graph.add_conditional_edges("review", route_after_review, {
    "finalize": "finalize",
    "revise": "revise"
})
review_graph.add_edge("revise", "review")  # Loop back for re-review
review_graph.add_edge("finalize", END)

# Compile with interrupt before human review
review_app = review_graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["review"]
)

# Usage
config = {"configurable": {"thread_id": "review-001"}}

# Step 1: Generate draft (runs until interrupt)
for event in review_app.stream({
    "topic": "The impact of AI on healthcare",
    "messages": [HumanMessage(content="Write about AI in healthcare")]
}, config):
    print(f"Step: {list(event.keys())}")

# Step 2: Human reviews
state = review_app.get_state(config)
print(f"Draft generated: {state.values['draft'][:200]}...")

# Human provides feedback
review_app.invoke(
    Command(resume={
        "approved": False,
        "feedback": "Add more statistics and case studies. Make it more data-driven.",
        "edited_draft": None
    }),
    config
)

# Step 3: Agent revises, then human reviews again
# (The loop continues until human approves)
```

**Review-and-Revise Flow:**
```
┌─────────────────────────────────────────────────────────────────┐
│                  Review-and-Revise Pattern                      │
│                                                                 │
│  [ENTRY] ──▶ ┌──────────┐     ┌──────────┐                    │
│              │ generate │────▶│  review  │◀─── INTERRUPT      │
│              └──────────┘     └────┬─────┘                    │
│                                    │                           │
│                          ┌─────────┴─────────┐                │
│                          │                   │                │
│                       APPROVED           REJECTED             │
│                          │                   │                │
│                          ▼                   ▼                │
│                   ┌──────────┐        ┌──────────┐           │
│                   │ finalize │        │  revise  │           │
│                   └────┬─────┘        └────┬─────┘           │
│                        │                   │                  │
│                        ▼                   └──────────────────┘
│                       END                                      │
│                                                                 │
│  Human can: approve, reject with feedback, or edit directly    │
└─────────────────────────────────────────────────────────────────┘
```

### Pattern: Tool Execution with Human Approval

```python
"""
Tool Execution with Human Approval
====================================
Before executing sensitive tools (database writes, API calls, 
file operations), pause for human confirmation.
"""

from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

@tool
def delete_database_records(query: str) -> str:
    """Delete records from the database matching the query."""
    # DANGEROUS OPERATION — requires human approval
    return f"Deleted records matching: {query}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    return f"Email sent to {to}: {subject}"

@tool
def search_database(query: str) -> str:
    """Search the database (safe, no approval needed)."""
    return f"Search results for: {query}"

# Create tool node
tools = [delete_database_records, send_email, search_database]
tool_node = ToolNode(tools)

class ToolApprovalState(TypedDict):
    messages: Annotated[List, add_messages]
    tool_name: str
    tool_input: dict
    tool_approved: bool

def llm_node(state: ToolApprovalState) -> dict:
    """LLM decides which tool to call."""
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        return {
            "tool_name": tool_call["name"],
            "tool_input": tool_call["args"],
            "messages": [response]
        }
    return {"messages": [response]}

def approval_router(state: ToolApprovalState) -> str:
    """Route based on tool sensitivity."""
    sensitive_tools = ["delete_database_records", "send_email"]
    
    if state.get("tool_name") in sensitive_tools:
        return "human_approval"
    else:
        return "execute_tool"

def human_approval_node(state: ToolApprovalState) -> dict:
    """Request human approval for sensitive tool."""
    approval = interrupt({
        "action": "approve_tool",
        "tool": state["tool_name"],
        "input": state["tool_input"],
        "question": f"Approve execution of {state['tool_name']}?"
    })
    
    return {"tool_approved": approval.get("approved", False)}

def tool_router_after_approval(state: ToolApprovalState) -> str:
    if state.get("tool_approved"):
        return "execute_tool"
    else:
        return END  # Skip tool execution if not approved

# Build graph
tool_graph = StateGraph(ToolApprovalState)
tool_graph.add_node("llm", llm_node)
tool_graph.add_node("human_approval", human_approval_node)
tool_graph.add_node("tools", tool_node)

tool_graph.set_entry_point("llm")
tool_graph.add_conditional_edges("llm", approval_router, {
    "human_approval": "human_approval",
    "execute_tool": "tools"
})
tool_graph.add_conditional_edges("human_approval", tool_router_after_approval, {
    "execute_tool": "tools",
    END: END
})
tool_graph.add_edge("tools", END)

tool_app = tool_graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_approval"]
)
```

**Tool Approval Flow:**
```
┌──────────────────────────────────────────────────────────────┐
│              Tool Execution with Approval                    │
│                                                              │
│  [ENTRY] ──▶ ┌─────┐                                        │
│              │ LLM │                                        │
│              └──┬──┘                                        │
│                 │                                            │
│        ┌────────┴────────┐                                  │
│        │                 │                                  │
│   Sensitive          Safe Tool                              │
│        │                 │                                  │
│        ▼                 ▼                                  │
│  ┌───────────┐    ┌───────────┐                            │
│  │   human   │    │  execute  │                            │
│  │ approval  │    │   tool    │                            │
│  └─────┬─────┘    └─────┬─────┘                            │
│        │                │                                  │
│   ┌────┴────┐           │                                  │
│   │         │           │                                  │
│ APPROVED  DENIED        │                                  │
│   │         │           │                                  │
│   ▼         ▼           ▼                                  │
│ execute    END         END                                 │
│   tool                                                        │
│     │                                                         │
│     ▼                                                         │
│    END                                                        │
└──────────────────────────────────────────────────────────────┘
```

### Best Practices for LangGraph

| Practice | Description | Code Example |
|----------|-------------|--------------|
| **Keep State Minimal** | Only store what's needed; avoid bloating state | Use separate TypedDict per graph complexity |
| **Use TypedDict Over Dict** | Type safety catches errors early | `class State(TypedDict): ...` |
| **Always Use Checkpointer** | Even in dev; enables debugging | `compile(checkpointer=MemorySaver())` |
| **Name Nodes Clearly** | Descriptive names aid debugging | `graph.add_node("validate_output", ...)` not `graph.add_node("node2", ...)` |
| **Handle Max Iterations** | Prevent infinite loops in cycles | `if state["iteration"] >= MAX: return END` |
| **Use `stream_mode="updates"`** | See what changed, not full state | `for step in app.stream(..., stream_mode="updates")` |
| **Subgraphs for Modularity** | Compose complex graphs from smaller ones | `subgraph = sub_workflow.compile(); graph.add_node("sub", subgraph)` |
| **Error Nodes** | Graceful failure handling | Add a dedicated error/recovery node |
| **Thread IDs** | Isolate concurrent executions | `config = {"configurable": {"thread_id": uuid4()}}` |
| **Validate State Updates** | Don't return None values | `return {"field": value or ""}` not `{"field": None}` |

#### Subgraph Pattern

```python
from langgraph.graph import StateGraph, END

# Subgraph: Research workflow
class ResearchSubState(TypedDict):
    query: str
    results: List[dict]
    summary: str

def search(state: ResearchSubState) -> dict:
    return {"results": [{"title": "Result", "content": "..."}]}

def summarize(state: ResearchSubState) -> dict:
    return {"summary": f"Summary of research on: {state['query']}"}

research_subgraph = StateGraph(ResearchSubState)
research_subgraph.add_node("search", search)
research_subgraph.add_node("summarize", summarize)
research_subgraph.set_entry_point("search")
research_subgraph.add_edge("search", "summarize")
research_subgraph.add_edge("summarize", END)

# Main graph
class MainState(TypedDict):
    messages: Annotated[List, add_messages]
    topic: str
    research_summary: str
    final_output: str

def research_node(state: MainState) -> dict:
    """Invoke subgraph as a node."""
    compiled_subgraph = research_subgraph.compile()
    result = compiled_subgraph.invoke({"query": state["topic"]})
    return {"research_summary": result["summary"]}

def write_node(state: MainState) -> dict:
    response = llm.invoke(f"Write an article based on: {state['research_summary']}")
    return {"final_output": response.content}

main_graph = StateGraph(MainState)
main_graph.add_node("research", research_node)
main_graph.add_node("write", write_node)
main_graph.set_entry_point("research")
main_graph.add_edge("research", "write")
main_graph.add_edge("write", END)

app = main_graph.compile()
```

**Subgraph Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Main Graph                             │
│                                                             │
│  [ENTRY] ──▶ ┌──────────┐     ┌──────────┐                │
│              │ research │────▶│   write  │──▶ END          │
│              └────┬─────┘     └──────────┘                │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │              Research Subgraph               │          │
│  │                                              │          │
│  │  ┌───────┐    ┌───────────┐                 │          │
│  │  │search │───▶│ summarize │──▶ (return)     │          │
│  │  └───────┘    └───────────┘                 │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  Subgraphs are invoked as nodes in the parent graph        │
└─────────────────────────────────────────────────────────────┘
```

### Key Takeaways — 6.3

| Concept | Key Point |
|---------|-----------|
| **DAG Graphs** | Linear, no cycles; use for pipelines, fixed workflows |
| **Cyclic Graphs** | Contain loops; use for retry, self-correction, agentic patterns |
| **interrupt_before** | Pauses before a node; human reviews what's about to happen |
| **interrupt_after** | Pauses after a node; human reviews what was produced |
| **interrupt()** | Node-level pause with custom prompt and data |
| **Time Travel** | `get_state_history()` to inspect, `update_state()` to edit |
| **State Modification** | Edit state at any checkpoint, then continue or branch |
| **Subgraphs** | Compose complex graphs from reusable sub-workflows |
| **Max Iterations** | Always guard cycles with iteration limits |
| **Thread IDs** | Use unique thread IDs to isolate concurrent executions |

---

## Summary

This module provided a deep dive into LangGraph, the graph-based orchestration library for building stateful, multi-actor LLM applications.

### What We Covered

**6.1 LangGraph Overview and Core Concepts**
- LangGraph exists to solve the limitations of linear chains: it enables cycles, persistence, human-in-the-loop, and fine-grained control flow
- Compared LangGraph vs. LangChain Agents across 10 dimensions
- Core abstractions: `StateGraph`, State (TypedDict/Pydantic), Nodes (pure functions), Edges (normal/conditional)
- Built a first LangGraph example: a classify → research state machine

**6.2 Building Blocks: Nodes, Edges, State Management**
- State definition with TypedDict (simple) and Pydantic (validated)
- Built-in reducers: `add_messages`, `operator.add`, custom reducers
- Node function contract: read state, return updates only
- Edge types: normal, conditional, entry point, END
- Checkpointing: MemorySaver, SQLiteSaver, state history inspection
- Streaming: `stream_mode` options (`values`, `updates`, `debug`), `stream_events` for token-level
- Complete multi-step research agent with self-critique loop

**6.3 Cyclic vs. DAG Graphs — Human-in-the-Loop Patterns**
- DAG graphs: linear pipelines for fixed workflows (document processing, simple RAG)
- Cyclic graphs: loops for self-correction, retry, iterative refinement
- Human-in-the-loop: `interrupt_before`, `interrupt_after`, `interrupt()`
- Time travel: replay from any checkpoint, branch with state edits
- Review-and-Revise pattern: generate → human review → revise → re-review
- Tool execution with human approval: sensitive tools require confirmation
- Subgraph composition for modular, reusable workflows
- Best practices: minimal state, always checkpoint, max iterations, clear naming

### LangGraph Architecture at a Glance

```
┌──────────────────────────────────────────────────────────────────────┐
│                        LangGraph Architecture                        │
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │  StateGraph  │   │    Nodes     │   │    Edges     │            │
│  │              │   │              │   │              │            │
│  │ • State      │   │ • LLM calls  │   │ • Normal     │            │
│  │ • Reducers   │   │ • Tool exec  │   │ • Conditional│            │
│  │ • Schema     │   │ • Validation │   │ • Entry/END  │            │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │
│         │                  │                  │                     │
│         └──────────────────┼──────────────────┘                     │
│                            ▼                                        │
│                   ┌─────────────────┐                              │
│                   │   Compiled App  │                              │
│                   │                 │                              │
│                   │ • invoke()      │                              │
│                   │ • stream()      │                              │
│                   │ • astream()     │                              │
│                   │ • stream_events │                              │
│                   └────────┬────────┘                              │
│                            │                                        │
│         ┌──────────────────┼──────────────────┐                    │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ Checkpointer│  │   Human-in  │  │  Subgraphs  │                │
│  │             │  │  -the-Loop  │  │             │                │
│  │ • Memory    │  │             │  │ • Compose   │                │
│  │ • SQLite    │  │ • interrupt │  │ • Reuse     │                │
│  │ • Postgres  │  │ • time trav │  │ • Nest      │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                      │
│  Execution Modes: DAG (linear) or Cyclic (loops, retry, agents)    │
└──────────────────────────────────────────────────────────────────────┘
```

### Next Steps

With LangGraph fundamentals established, you can now:
- Build production agents with human oversight
- Design self-correcting workflows with cyclic graphs
- Create modular systems using subgraph composition
- Implement reliable, checkpointed multi-step pipelines
- Stream real-time updates from complex agent workflows
