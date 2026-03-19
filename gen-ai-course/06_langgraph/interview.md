# LangGraph Interview Questions

## Basic Concepts

### 1. What is LangGraph and how does it differ from LangChain?

**Answer:**
LangGraph is a library for building stateful, multi-agent applications using Large Language Models. It represents workflows as directed graphs where:
- **Nodes** = computational steps (functions that process state)
- **Edges** = flow control (how to move between nodes)
- **State** = shared data that flows through the graph

**Key differences from LangChain:**
- **Workflow**: LangChain uses sequential chains, LangGraph uses directed graphs
- **Cycles**: LangChain doesn't support cycles, LangGraph fully supports them
- **State**: LangChain has limited state, LangGraph has full state management
- **Complexity**: LangChain for simple linear flows, LangGraph for complex multi-agent flows
- **Debugging**: LangGraph provides graph visualization for easier debugging

### 2. What are the three core components of LangGraph?

**Answer:**
1. **State**: A dictionary that flows through the graph, carrying information between nodes
2. **Nodes**: Python functions that take current state as input, process/transform it, and return updates
3. **Edges**: Define how to move between nodes (normal edges always move, conditional edges choose based on state)

### 3. What is the purpose of state in LangGraph?

**Answer:**
State serves as the shared data that flows through the graph, enabling:
- **Persistence**: Maintaining context across multiple node executions
- **Communication**: Passing information between different parts of the workflow
- **Memory**: Storing conversation history, intermediate results, and application state
- **Coordination**: Allowing nodes to access and modify shared data

## Intermediate Concepts

### 4. How do you create a simple LangGraph workflow?

**Answer:**
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define state schema
class GraphState(TypedDict):
    messages: list
    user_input: str
    final_response: str

# Create nodes
def process_input(state: GraphState) -> GraphState:
    return {
        "messages": state["messages"] + [{"role": "user", "content": state["user_input"]}]
    }

def generate_response(state: GraphState) -> GraphState:
    # LLM logic here
    return {"final_response": "Generated response"}

# Build graph
graph = StateGraph(GraphState)
graph.add_node("process", process_input)
graph.add_node("generate", generate_response)
graph.set_entry_point("process")
graph.add_edge("process", "generate")
graph.add_edge("generate", END)

# Compile
app = graph.compile()
```

### 5. What are conditional edges and when would you use them?

**Answer:**
Conditional edges allow the graph to choose the next node based on the current state, rather than always following a fixed path.

**Use cases:**
- **Routing**: Directing workflow based on user input or conditions
- **Validation**: Checking if data meets criteria before proceeding
- **Branching logic**: Different paths for different scenarios
- **Error handling**: Redirecting to error handling nodes

**Example:**
```python
def should_continue(state: GraphState) -> str:
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

### 6. How do you implement cycles in LangGraph?

**Answer:**
Cycles are implemented by having edges that point back to previous nodes, enabling iterative processing:

```python
def reason_node(state: GraphState) -> GraphState:
    # LLM decides action
    return {"action": "search"}

def action_node(state: GraphState) -> GraphState:
    # Execute action
    return {"observation": "Found information"}

def should_continue(state: GraphState) -> str:
    if state.get("iterations", 0) >= 3:
        return "end"
    return "continue"

# Build cyclic graph
graph = StateGraph(GraphState)
graph.add_node("reason", reason_node)
graph.add_node("act", action_node)
graph.set_entry_point("reason")
graph.add_edge("reason", "act")
graph.add_conditional_edges(
    "act",
    should_continue,
    {
        "continue": "reason",
        "end": END
    }
)
```

## Advanced Concepts

### 7. How do you integrate tools with LangGraph?

**Answer:**
Tools are integrated by creating nodes that execute tool calls and handle their results:

```python
from langchain.tools import tool

@tool
def search_wikipedia(query: str) -> str:
    return f"Information about {query}"

class ToolState(TypedDict):
    query: str
    tool_calls: list
    tool_results: list
    final_answer: str

def call_tools(state: ToolState) -> ToolState:
    # Get tool suggestions from LLM
    return {"tool_calls": tool_calls}

def execute_tools(state: ToolState) -> ToolState:
    # Execute the called tools
    return {"tool_results": results}

def generate_answer(state: ToolState) -> ToolState:
    # Generate final answer from tool results
    return {"final_answer": response}

# Build tool workflow
graph = StateGraph(ToolState)
graph.add_node("call_tools", call_tools)
graph.add_node("execute_tools", execute_tools)
graph.add_node("generate", generate_answer)
graph.set_entry_point("call_tools")
graph.add_edge("call_tools", "execute_tools")
graph.add_edge("execute_tools", "generate")
graph.add_edge("generate", END)
```

### 8. What is human-in-the-loop (HITL) and how is it implemented?

**Answer:**
HITL allows humans to interrupt and influence the execution of LangGraph workflows.

**Implementation:**
```python
from langgraph.graph import interrupt

class HITLState(TypedDict):
    user_request: str
    approval_required: bool
    approved: bool
    response: str

def request_approval(state: HITLState) -> HITLState:
    # This interrupts the graph and waits for human input
    approved = interrupt({
        "message": f"Approval needed for: {state['user_request']}",
        "required_action": "Please approve or reject"
    })
    return {"approved": approved}

def check_approval(state: HITLState) -> str:
    if state.get("approval_required", False):
        return "request_approval"
    return "execute"

# Build HITL graph
graph = StateGraph(HITLState)
graph.add_node("request_approval", request_approval)
graph.add_conditional_edges(
    "process",
    check_approval,
    {
        "request_approval": "request_approval",
        "execute": "execute"
    }
)
```

### 9. How do you handle memory and state persistence in LangGraph?

**Answer:**
Memory is handled through state management and can be made persistent:

```python
# Short-term memory (message history)
class ConversationState(TypedDict):
    messages: list  # Chat message history
    user_input: str

# Long-term memory (vector store integration)
class PersistentMemoryState(TypedDict):
    user_id: str
    query: str
    context: list  # Retrieved from vector store
    response: str

# State persistence with checkpointing
from langgraph.checkpoint import MemorySaver

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# Save and resume state
config = {"configurable": {"thread_id": "1"}}
result = app.invoke({"user_input": "Hello"}, config=config)

# Resume later
result = app.invoke({"user_input": "How are you?"}, config=config)
```

### 10. How do you debug and visualize LangGraph applications?

**Answer:**
LangGraph provides several debugging and visualization tools:

```python
# Get graph visualization
mermaid_code = app.get_graph().draw_mermaid()
print(mermaid_code)

# Stream execution for debugging
for chunk in app.stream(
    {"user_input": "Hello"},
    stream_mode="values"
):
    print(f"State update: {chunk}")

# Add debug logging
def debug_node(state):
    print(f"State at node: {state}")
    return state

graph.add_node("debug", debug_node)

# Visualize with Mermaid
app.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

## Practical Applications

### 11. Describe a multi-agent collaboration scenario using LangGraph.

**Answer:**
```python
class MultiAgentState(TypedDict):
    task: str
    research_result: str
    writing_result: str
    review_result: str
    final_result: str

def research_agent(state: MultiAgentState) -> MultiAgentState:
    # Research agent collects information
    return {"research_result": "Research findings"}

def writing_agent(state: MultiAgentState) -> MultiAgentState:
    # Writing agent creates content based on research
    return {"writing_result": "Written content"}

def review_agent(state: MultiAgentState) -> MultiAgentState:
    # Review agent evaluates the content
    return {"review_result": "Review feedback", "final_result": "Final content"}

# Build multi-agent graph
graph = StateGraph(MultiAgentState)
graph.add_node("research", research_agent)
graph.add_node("write", writing_agent)
graph.add_node("review", review_agent)
graph.set_entry_point("research")
graph.add_edge("research", "write")
graph.add_edge("write", "review")
graph.add_edge("review", END)
```

### 12. How would you implement a reflection pattern in LangGraph?

**Answer:**
The reflection pattern allows agents to review and improve their outputs:

```python
class ReflectionState(TypedDict):
    task: str
    draft: str
    feedback: str
    iterations: int
    final: str

def generate_draft(state: ReflectionState) -> ReflectionState:
    # Generate initial draft
    return {"draft": "Initial draft content", "iterations": 0}

def reflect(state: ReflectionState) -> ReflectionState:
    # Reflect on draft and provide feedback
    return {"feedback": "Constructive feedback", "iterations": state["iterations"] + 1}

def improve(state: ReflectionState) -> ReflectionState:
    # Improve draft based on feedback
    return {"draft": "Improved draft content"}

def should_continue(state: ReflectionState) -> str:
    # Decide whether to continue reflecting
    if state["iterations"] >= 2:  # Max 2 reflection cycles
        return "finish"
    return "reflect"

def finish(state: ReflectionState) -> ReflectionState:
    # Finalize the response
    return {"final": state["draft"]}

# Build reflection graph
graph = StateGraph(ReflectionState)
graph.add_node("draft", generate_draft)
graph.add_node("reflect", reflect)
graph.add_node("improve", improve)
graph.add_node("finish", finish)
graph.set_entry_point("draft")
graph.add_edge("draft", "reflect")
graph.add_conditional_edges(
    "reflect",
    should_continue,
    {
        "reflect": "improve",
        "finish": "finish"
    }
)
graph.add_edge("improve", "reflect")
graph.add_edge("finish", END)
```

### 13. What are some performance optimization strategies for LangGraph?

**Answer:**
1. **State minimization**: Only store necessary data in state
2. **Lazy evaluation**: Defer expensive operations until needed
3. **Caching**: Cache expensive computations between nodes
4. **Parallel execution**: Use parallel nodes where possible
5. **Checkpointing**: Use selective checkpointing to reduce memory usage
6. **Edge optimization**: Minimize unnecessary edge traversals
7. **Node optimization**: Optimize individual node performance

### 14. How do you handle errors and exceptions in LangGraph?

**Answer:**
```python
class ErrorHandlingState(TypedDict):
    input: str
    result: str
    error: str
    retry_count: int

def safe_node(state: ErrorHandlingState) -> ErrorHandlingState:
    try:
        # Risky operation
        result = risky_operation(state["input"])
        return {"result": result}
    except Exception as e:
        return {"error": str(e), "retry_count": state.get("retry_count", 0) + 1}

def should_retry(state: ErrorHandlingState) -> str:
    if state.get("error") and state.get("retry_count", 0) < 3:
        return "retry"
    elif state.get("error"):
        return "error_handler"
    return "success"

# Build error-handling graph
graph = StateGraph(ErrorHandlingState)
graph.add_node("process", safe_node)
graph.add_node("retry", safe_node)  # Retry the same operation
graph.add_node("error_handler", handle_error)
graph.add_node("success", handle_success)
graph.set_entry_point("process")
graph.add_conditional_edges(
    "process",
    should_retry,
    {
        "retry": "retry",
        "error_handler": "error_handler",
        "success": "success"
    }
)
```

### 15. How would you deploy a LangGraph application to production?

**Answer:**
Production deployment considerations:

1. **State management**: Use persistent storage (Redis, database) instead of in-memory
2. **Scalability**: Implement load balancing and horizontal scaling
3. **Monitoring**: Add logging, metrics, and health checks
4. **Security**: Implement authentication, authorization, and input validation
5. **Error handling**: Robust error handling and graceful degradation
6. **Testing**: Comprehensive unit and integration tests
7. **Documentation**: Clear API documentation and usage examples

```python
# Production setup example
from langgraph.checkpoint import PostgresSaver
import asyncpg

# Use persistent checkpointing
checkpoint = PostgresSaver(asyncpg.create_pool("postgresql://..."))
app = graph.compile(checkpointer=checkpoint)

# Add monitoring
import logging
logging.basicConfig(level=logging.INFO)

# Add health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "graph": "compiled"}