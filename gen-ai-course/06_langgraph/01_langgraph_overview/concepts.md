# Concepts: LangGraph Overview

## What is LangGraph?

LangGraph is a library for building stateful, multi-agent applications using Large Language Models. It represents workflows as directed graphs where:

- **Nodes** = computational steps (functions that process state)
- **Edges** = flow control (how to move between nodes)
- **State** = shared data that flows through the graph

### Key Features

| Feature | Description |
|---------|-------------|
| **Cycles** | Support for looping (essential for agents) |
| **Stateful** | Persistent context across interactions |
| **Human-in-the-loop** | Interrupt and resume workflows |
| **Visualization** | Debug and understand agent flows |
| **Persistence** | Save and resume graph state |

## Core Concepts

### 1. State

State is a dictionary that flows through the graph. It carries information between nodes.

```python
from typing import TypedDict

# Define state schema
class GraphState(TypedDict):
    """State that flows through the graph."""
    messages: list  # Chat message history
    user_input: str
    final_response: str
    steps_taken: int
```

### 2. Nodes

Nodes are Python functions that:
- Take current state as input
- Process/transform the state
- Return updates to the state

```python
def process_input(state: GraphState) -> GraphState:
    """Node that processes user input."""
    user_input = state["user_input"]
    
    # Process the input
    processed = user_input.upper()
    
    # Return state updates
    return {
        "messages": state["messages"] + [{"role": "user", "content": processed}],
        "steps_taken": state.get("steps_taken", 0) + 1,
    }
```

### 3. Edges

Edges define how to move between nodes:

- **Normal Edges**: Always move from A to B
- **Conditional Edges**: Choose next node based on state

```python
from langgraph.graph import END

# Normal edge: always go to next node
graph.add_edge("node_a", "node_b")

# Conditional edge: choose based on state
def should_continue(state: GraphState) -> str:
    """Determine next step based on state."""
    if state.get("steps_taken", 0) > 5:
        return "end"
    return "continue"

graph.add_conditional_edges(
    "node_b",
    should_continue,
    {
        "continue": "node_c",
        "end": END,
    }
)
```

### 4. Graph Compilation

```python
from langgraph.graph import StateGraph

# Create and compile the graph
graph = StateGraph(GraphState)

# Add nodes
graph.add_node("process", process_input)
graph.add_node("generate", generate_response)

# Add edges
graph.set_entry_point("process")
graph.add_edge("process", "generate")
graph.add_edge("generate", END)

# Compile
app = graph.compile()
```

## LangChain vs LangGraph

| Aspect | LangChain | LangGraph |
|--------|-----------|-----------|
| **Workflow** | Sequential chains | Directed graphs |
| **Cycles** | Not supported | Fully supported |
| **State** | Limited | Full state management |
| **Complexity** | Simple linear flows | Complex multi-agent flows |
| **Debugging** | Harder | Graph visualization |

### When to Use LangGraph

LangGraph is ideal when you need:
- **Iterative processing**: Agents that think and act in cycles
- **Complex routing**: Different paths based on conditions
- **State management**: Maintaining context across multiple steps
- **Multi-agent systems**: Coordination between multiple agents
- **Human interaction**: Pausing and resuming workflows

### When to Use LangChain

LangChain is better for:
- **Simple linear workflows**: Straightforward input-output chains
- **Quick prototyping**: Rapid development of basic LLM applications
- **Single-shot tasks**: One-time processing without state
- **Simple tool usage**: Basic tool integration without complex state

## Building Your First Graph

### Simple Chat Graph

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define state
class ChatState(TypedDict):
    messages: list
    user_input: str

# Initialize LLM
llm = ChatOpenAI(model="gpt-4")

# Node 1: Process user input
def process_user_input(state: ChatState) -> ChatState:
    """Add user message to state."""
    return {
        "messages": state["messages"] + [{"role": "user", "content": state["user_input"]}]
    }

# Node 2: Generate response
def generate_response(state: ChatState) -> ChatState:
    """Generate LLM response."""
    response = llm.invoke(state["messages"])
    return {
        "messages": state["messages"] + [response]
    }

# Build graph
graph = StateGraph(ChatState)
graph.add_node("process", process_user_input)
graph.add_node("respond", generate_response)
graph.set_entry_point("process")
graph.add_edge("process", "respond")
graph.add_edge("respond", END)

# Compile
app = graph.compile()

# Run
result = app.invoke({
    "messages": [],
    "user_input": "Hello, how are you?"
})

print(result["messages"])
```

### Graph with Conditional Logic

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict

class DecisionState(TypedDict):
    user_query: str
    category: str
    response: str
    needs_escalation: bool

llm = ChatOpenAI(model="gpt-4")

def classify_query(state: DecisionState) -> DecisionState:
    """Classify user query."""
    query = state["user_query"]
    
    # Simple classification
    if "help" in query.lower() or "support" in query.lower():
        category = "support"
    elif "buy" in query.lower() or "price" in query.lower():
        category = "sales"
    else:
        category = "general"
    
    return {"category": category}

def handle_support(state: DecisionState) -> DecisionState:
    """Handle support query."""
    return {
        "response": "I'll connect you with our support team.",
        "needs_escalation": True
    }

def handle_sales(state: DecisionState) -> DecisionState:
    """Handle sales query."""
    return {
        "response": "I'd be happy to help you with your purchase!",
        "needs_escalation": False
    }

def handle_general(state: DecisionState) -> DecisionState:
    """Handle general query."""
    response = llm.invoke(f"Answer this question: {state['user_query']}")
    return {
        "response": response.content,
        "needs_escalation": False
    }

def should_route(state: DecisionState) -> str:
    """Route to appropriate handler."""
    category = state.get("category", "general")
    return category

# Build graph
graph = StateGraph(DecisionState)

graph.add_node("classify", classify_query)
graph.add_node("support", handle_support)
graph.add_node("sales", handle_sales)
graph.add_node("general", handle_general)

graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify",
    should_route,
    {
        "support": "support",
        "sales": "sales",
        "general": "general"
    }
)

# All handlers lead to end
graph.add_edge("support", END)
graph.add_edge("sales", END)
graph.add_edge("general", END)

app = graph.compile()
```

## Graph Visualization and Debugging

### Visualizing the Graph

```python
# Get graph as Mermaid diagram
mermaid_code = app.get_graph().draw_mermaid()
print(mermaid_code)

# Or save as image (requires additional dependencies)
# app.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

### Debugging Tips

```python
# Add debug logging
def debug_node(state):
    print(f"State at node: {state}")
    return state

# Add to graph
graph.add_node("debug", debug_node)

# Use breakpoints for inspection
app = graph.compile()

# Run with breakpoints
for chunk in app.stream(
    {"user_input": "Hello"},
    stream_mode="values"
):
    print(chunk)
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| State not updating | Ensure node returns state dict |
| Infinite loops | Add max iterations check |
| Tools not working | Check tool binding |
| Memory issues | Use checkpointing |
| Graph not executing | Check entry point and edges |

## Summary

This module covered the fundamental concepts of LangGraph:

1. **What is LangGraph?**: A framework for building stateful, multi-agent applications
2. **Core Components**: State, Nodes, Edges, and Graph compilation
3. **LangChain vs LangGraph**: When to use each framework
4. **Building Graphs**: Simple chat and conditional routing examples
5. **Visualization**: Debugging and understanding graph flows

LangGraph enables building sophisticated, stateful agent applications with full control over workflow execution. The next module will dive deeper into the building blocks of LangGraph applications.