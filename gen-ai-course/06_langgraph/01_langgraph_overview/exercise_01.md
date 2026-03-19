# Exercise 01: Building Your First LangGraph

## Objective

Create a simple LangGraph application that processes user input through multiple nodes and demonstrates the core concepts of state, nodes, and edges.

## Requirements

1. Create a LangGraph that processes user input through three nodes
2. Implement state management to track the processing steps
3. Add conditional routing based on the input content
4. Visualize the graph structure

## Instructions

### Step 1: Set up the project

Create a new Python file called `simple_graph.py` and set up the basic imports:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
```

### Step 2: Define the State Schema

Create a TypedDict that represents the state flowing through your graph:

```python
class ProcessingState(TypedDict):
    """State that flows through the processing graph."""
    input_text: str
    processed_text: str
    step_count: int
    category: str
    final_output: str
```

### Step 3: Create the Nodes

Implement three nodes that will process the input:

1. **Input Validation Node**: Check if input is valid and categorize it
2. **Text Processing Node**: Transform the text based on its category
3. **Output Formatting Node**: Format the final output

```python
def validate_input(state: ProcessingState) -> ProcessingState:
    """Validate and categorize the input text."""
    input_text = state["input_text"]
    
    # Basic validation
    if not input_text or not input_text.strip():
        return {
            "processed_text": "Invalid input: empty text",
            "step_count": 1,
            "category": "invalid"
        }
    
    # Categorize input
    input_lower = input_text.lower()
    if any(word in input_lower for word in ["hello", "hi", "hey"]):
        category = "greeting"
    elif any(word in input_lower for word in ["help", "support", "issue"]):
        category = "support"
    elif any(word in input_lower for word in ["buy", "purchase", "price"]):
        category = "sales"
    else:
        category = "general"
    
    return {
        "processed_text": input_text.strip(),
        "step_count": 1,
        "category": category
    }

def process_text(state: ProcessingState) -> ProcessingState:
    """Process the text based on its category."""
    processed_text = state["processed_text"]
    category = state["category"]
    step_count = state["step_count"]
    
    # Transform text based on category
    if category == "greeting":
        transformed = f"Hello! I received your greeting: '{processed_text}'"
    elif category == "support":
        transformed = f"Support team notified about: '{processed_text}'"
    elif category == "sales":
        transformed = f"Sales inquiry logged: '{processed_text}'"
    else:
        transformed = f"General message processed: '{processed_text}'"
    
    return {
        "processed_text": transformed,
        "step_count": step_count + 1
    }

def format_output(state: ProcessingState) -> ProcessingState:
    """Format the final output."""
    processed_text = state["processed_text"]
    category = state["category"]
    step_count = state["step_count"]
    
    final_output = f"""
=== PROCESSING COMPLETE ===
Category: {category.upper()}
Steps Taken: {step_count}
Output: {processed_text}
=== END ===
"""
    
    return {
        "final_output": final_output,
        "step_count": step_count + 1
    }
```

### Step 4: Build the Graph

Create the graph with proper node connections:

```python
# Create the graph
graph = StateGraph(ProcessingState)

# Add nodes
graph.add_node("validate", validate_input)
graph.add_node("process", process_text)
graph.add_node("format", format_output)

# Set entry point
graph.set_entry_point("validate")

# Add edges
graph.add_edge("validate", "process")
graph.add_edge("process", "format")
graph.add_edge("format", END)

# Compile the graph
app = graph.compile()
```

### Step 5: Test the Graph

Create a function to test your graph with different inputs:

```python
def test_graph():
    """Test the graph with various inputs."""
    test_cases = [
        "Hello, how are you?",
        "I need help with my account",
        "What's the price of your product?",
        "This is just a test message",
        "",
        "   ",
        "Hey there!"
    ]
    
    for test_input in test_cases:
        print(f"\n--- Testing: '{test_input}' ---")
        try:
            result = app.invoke({
                "input_text": test_input,
                "processed_text": "",
                "step_count": 0,
                "category": "",
                "final_output": ""
            })
            print(result["final_output"])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_graph()
```

### Step 6: Visualize the Graph

Add code to visualize your graph:

```python
def visualize_graph():
    """Display the graph structure."""
    try:
        # Get Mermaid diagram
        mermaid_code = app.get_graph().draw_mermaid()
        print("Graph Visualization (Mermaid):")
        print(mermaid_code)
        
        # Save as PNG if possible
        try:
            app.get_graph().draw_mermaid_png(output_file_path="simple_graph.png")
            print("Graph saved as simple_graph.png")
        except Exception as e:
            print(f"Could not save PNG: {e}")
            
    except Exception as e:
        print(f"Visualization error: {e}")

if __name__ == "__main__":
    test_graph()
    visualize_graph()
```

## Expected Output

When you run your program, you should see:

1. Test results for each input case showing the processed output
2. A Mermaid diagram representing your graph structure
3. A PNG file with the visualized graph (if dependencies are available)

## Advanced Challenge

### Add Conditional Routing

Modify your graph to include conditional routing:

1. Add a decision node that checks if the input contains sensitive information
2. Route sensitive inputs to a special handling path
3. Add an additional node for sensitive content processing

```python
def check_sensitivity(state: ProcessingState) -> ProcessingState:
    """Check if input contains sensitive information."""
    sensitive_keywords = ["password", "credit card", "ssn", "social security"]
    text = state["input_text"].lower()
    
    is_sensitive = any(keyword in text for keyword in sensitive_keywords)
    
    return {
        "is_sensitive": is_sensitive,
        "processed_text": state["processed_text"],
        "step_count": state["step_count"],
        "category": state["category"]
    }

def handle_sensitive(state: ProcessingState) -> ProcessingState:
    """Handle sensitive content."""
    return {
        "processed_text": "[SENSITIVE CONTENT REDACTED]",
        "step_count": state["step_count"] + 1,
        "category": "sensitive"
    }

# Add conditional routing
graph.add_node("check_sensitivity", check_sensitivity)
graph.add_node("handle_sensitive", handle_sensitive)

# Modify the graph structure
graph.set_entry_point("validate")
graph.add_edge("validate", "check_sensitivity")

def route_after_check(state: ProcessingState) -> str:
    """Route based on sensitivity check."""
    if state.get("is_sensitive", False):
        return "handle_sensitive"
    return "process"

graph.add_conditional_edges(
    "check_sensitivity",
    route_after_check,
    {
        "handle_sensitive": "handle_sensitive",
        "process": "process"
    }
)

graph.add_edge("handle_sensitive", "format")
graph.add_edge("process", "format")
graph.add_edge("format", END)
```

## Submission

Submit your completed `simple_graph.py` file that includes:

1. ✅ Basic three-node graph implementation
2. ✅ State management with proper TypedDict
3. ✅ Input validation and categorization
4. ✅ Text processing and output formatting
5. ✅ Graph visualization
6. ✅ Test cases for different input types
7. ✅ [Optional] Advanced conditional routing for sensitive content

## Evaluation Criteria

- **Functionality**: Graph runs without errors and processes inputs correctly
- **State Management**: Proper use of state to track processing steps
- **Code Quality**: Clean, readable code with appropriate comments
- **Testing**: Comprehensive test cases covering different scenarios
- **Visualization**: Successful graph visualization
- **Advanced Features**: Implementation of conditional routing (bonus)