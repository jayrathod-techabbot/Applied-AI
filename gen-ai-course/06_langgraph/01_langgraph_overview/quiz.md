# LangGraph Overview Quiz

## Multiple Choice Questions

### 1. What is the primary purpose of LangGraph?

A) To create static data visualizations  
B) To build stateful, multi-agent applications with LLMs  
C) To replace LangChain entirely  
D) To provide a GUI for LLM applications  

**Answer:** B

### 2. Which of the following is NOT a core component of LangGraph?

A) State  
B) Nodes  
C) Edges  
D) Prompts  

**Answer:** D

### 3. What does the State in LangGraph represent?

A) A single variable  
B) A dictionary that flows through the graph  
C) The final output only  
D) User input exclusively  

**Answer:** B

### 4. Nodes in LangGraph are:

A) Static functions that don't interact with state  
B) Python functions that process and transform state  
C) Database connections  
D) LLM model instances  

**Answer:** B

### 5. Conditional edges in LangGraph:

A) Always move to the same next node  
B) Choose the next node based on the current state  
C) Skip nodes randomly  
D) Only work with specific LLMs  

**Answer:** B

### 6. When would you choose LangGraph over LangChain?

A) For simple, linear workflows  
B) When you need iterative processing with cycles  
C) For single-shot tasks without state  
D) When you want the simplest possible implementation  

**Answer:** B

### 7. What is the purpose of graph compilation in LangGraph?

A) To convert Python code to machine code  
B) To create an executable workflow from the defined graph  
C) To optimize the LLM prompts  
D) To validate the Python syntax  

**Answer:** B

### 8. Which method sets the starting point of a LangGraph workflow?

A) `set_start_point()`  
B) `set_entry_point()`  
C) `add_start_node()`  
D) `compile_graph()`  

**Answer:** B

### 9. What does the `END` constant represent in LangGraph?

A) The beginning of the graph  
B) A special node for error handling  
C) The termination point of the workflow  
D) A conditional branch  

**Answer:** C

### 10. Which of the following is a valid use case for LangGraph?

A) Simple text generation without state  
B) Multi-agent collaboration with state management  
C) Static data processing  
D) Single-function applications  

**Answer:** B

## True/False Questions

### 11. LangGraph supports cycles, allowing agents to iterate and refine their outputs.

**Answer:** True

### 12. State in LangGraph is immutable and cannot be modified by nodes.

**Answer:** False

### 13. LangGraph provides built-in visualization capabilities for debugging workflows.

**Answer:** True

### 14. All nodes in a LangGraph must return the complete state dictionary.

**Answer:** True

### 15. Conditional edges can only be used with boolean conditions.

**Answer:** False

## Fill in the Blanks

### 16. In LangGraph, __________ define how to move between nodes.

**Answer:** Edges

### 17. The __________ method is used to add normal connections between nodes.

**Answer:** `add_edge()`

### 18. __________ edges allow the graph to choose the next node based on state conditions.

**Answer:** Conditional

### 19. The __________ is the compiled, executable version of a LangGraph workflow.

**Answer:** app (or compiled graph)

### 20. LangGraph extends __________ with graph-based workflows.

**Answer:** LangChain

## Short Answer Questions

### 21. Explain the difference between normal edges and conditional edges in LangGraph.

**Answer:** Normal edges always move from one node to another specific node, while conditional edges choose the next node based on the current state. Normal edges provide fixed routing, while conditional edges enable dynamic workflow paths.

### 22. What are the key benefits of using state in LangGraph applications?

**Answer:** State enables memory across node executions, allows communication between different parts of the workflow, supports complex multi-step processes, and enables agents to maintain context throughout their execution.

### 23. Describe when you would use LangGraph instead of LangChain.

**Answer:** Use LangGraph when you need iterative processing, complex routing based on conditions, state management across multiple steps, multi-agent coordination, or human-in-the-loop interactions. Use LangChain for simpler, linear workflows.

### 24. What is the role of the `TypedDict` in LangGraph state definition?

**Answer:** `TypedDict` provides type hints for the state structure, making the code more maintainable and helping with IDE support. It defines the expected keys and their types in the state dictionary.

### 25. How does graph visualization help in LangGraph development?

**Answer:** Graph visualization helps developers understand the workflow structure, debug complex routing, identify potential issues, and communicate the application architecture to others. It provides a visual representation of how data flows through the system.

## Code Analysis

### 26. Identify the issue in this LangGraph code:

```python
from langgraph.graph import StateGraph

class MyState(TypedDict):
    input: str
    output: str

def process_node(state: MyState) -> MyState:
    return {"output": state["input"].upper()}

graph = StateGraph(MyState)
graph.add_node("process", process_node)
graph.set_entry_point("process")
app = graph.compile()
```

**Answer:** The code is missing the `END` import and the edge to END. It should include `from langgraph.graph import StateGraph, END` and `graph.add_edge("process", END)`.

### 27. What does this conditional edge function do?

```python
def route_by_length(state: MyState) -> str:
    if len(state["input"]) > 10:
        return "long"
    else:
        return "short"
```

**Answer:** This function routes the workflow to different nodes based on the length of the input string. If the input is longer than 10 characters, it goes to the "long" node; otherwise, it goes to the "short" node.

## Scenario Questions

### 28. You need to build a customer service chatbot that can:
- Greet users
- Categorize their requests (sales, support, general)
- Route to appropriate handlers
- Escalate complex issues to human agents

Which LangGraph concepts would you use and why?

**Answer:** Use state to track conversation context, nodes for each processing step (greeting, categorization, routing, escalation), conditional edges for routing based on request type and complexity, and potentially human-in-the-loop for escalation scenarios.

### 29. When would you use checkpointing in a LangGraph application?

**Answer:** Use checkpointing when you need to save and resume graph state, handle long-running workflows, implement human-in-the-loop interactions, or ensure fault tolerance in production applications.

### 30. How would you debug a LangGraph application that's not producing expected outputs?

**Answer:** Use graph visualization to understand the workflow, add debug logging to nodes, stream execution to see state changes, check state updates in each node, verify edge routing logic, and validate the initial state structure.