#!/usr/bin/env python3
"""
LangGraph Overview - Exercise 01 Solution

This file contains the complete solution for the LangGraph Overview
exercise, demonstrating all the core concepts of LangGraph.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict


class ProcessingState(TypedDict):
    """State that flows through the processing graph."""
    input_text: str
    processed_text: str
    step_count: int
    category: str
    final_output: str


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


def create_simple_graph():
    """Create and compile the simple processing graph."""
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
    return graph.compile()


def test_graph():
    """Test the graph with various inputs."""
    app = create_simple_graph()
    
    test_cases = [
        "Hello, how are you?",
        "I need help with my account",
        "What's the price of your product?",
        "This is just a test message",
        "",
        "   ",
        "Hey there!"
    ]
    
    print("🧪 Testing Simple LangGraph")
    print("=" * 50)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: '{test_input}' ---")
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
            print(f"❌ Error: {e}")


def visualize_graph():
    """Display the graph structure."""
    app = create_simple_graph()
    
    print("\n📊 Graph Visualization")
    print("=" * 50)
    
    try:
        # Get Mermaid diagram
        mermaid_code = app.get_graph().draw_mermaid()
        print("Graph Visualization (Mermaid):")
        print(mermaid_code)
        
        # Save as PNG if possible
        try:
            app.get_graph().draw_mermaid_png(output_file_path="simple_graph.png")
            print("\n✅ Graph saved as simple_graph.png")
        except Exception as e:
            print(f"\n⚠️  Could not save PNG: {e}")
            
    except Exception as e:
        print(f"❌ Visualization error: {e}")


def create_advanced_graph():
    """Create an advanced graph with conditional routing."""
    
    class AdvancedState(TypedDict):
        """Enhanced state with sensitivity tracking."""
        input_text: str
        processed_text: str
        step_count: int
        category: str
        final_output: str
        is_sensitive: bool
    
    def check_sensitivity(state: AdvancedState) -> AdvancedState:
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

    def handle_sensitive(state: AdvancedState) -> AdvancedState:
        """Handle sensitive content."""
        return {
            "processed_text": "[SENSITIVE CONTENT REDACTED]",
            "step_count": state["step_count"] + 1,
            "category": "sensitive"
        }

    def route_after_check(state: AdvancedState) -> str:
        """Route based on sensitivity check."""
        if state.get("is_sensitive", False):
            return "handle_sensitive"
        return "process"

    # Create the advanced graph
    graph = StateGraph(AdvancedState)

    # Add nodes
    graph.add_node("validate", validate_input)
    graph.add_node("check_sensitivity", check_sensitivity)
    graph.add_node("handle_sensitive", handle_sensitive)
    graph.add_node("process", process_text)
    graph.add_node("format", format_output)

    # Set entry point
    graph.set_entry_point("validate")

    # Add edges with conditional routing
    graph.add_edge("validate", "check_sensitivity")
    
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

    return graph.compile()


def test_advanced_graph():
    """Test the advanced graph with sensitive content detection."""
    app = create_advanced_graph()
    
    test_cases = [
        "Hello, how are you?",
        "My password is 123456",
        "I need help with my account",
        "Credit card number is 1234-5678-9012-3456",
        "What's the price of your product?",
        "This is just a test message"
    ]
    
    print("\n🧪 Testing Advanced LangGraph (with Sensitive Content Detection)")
    print("=" * 70)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: '{test_input}' ---")
        try:
            result = app.invoke({
                "input_text": test_input,
                "processed_text": "",
                "step_count": 0,
                "category": "",
                "final_output": "",
                "is_sensitive": False
            })
            print(result["final_output"])
        except Exception as e:
            print(f"❌ Error: {e}")


def demonstrate_core_concepts():
    """Demonstrate all core LangGraph concepts."""
    print("🎯 LangGraph Core Concepts Demonstration")
    print("=" * 50)
    
    print("\n1. ✅ State Management")
    print("   - State flows through the graph as a dictionary")
    print("   - Each node can read and modify the state")
    print("   - State maintains context across multiple steps")
    
    print("\n2. ✅ Node Creation")
    print("   - Nodes are Python functions that process state")
    print("   - Each node takes current state and returns updates")
    print("   - Nodes can perform validation, processing, formatting")
    
    print("\n3. ✅ Edge Connections")
    print("   - Normal edges: fixed routing between nodes")
    print("   - Conditional edges: dynamic routing based on state")
    print("   - Entry points define where the graph starts")
    
    print("\n4. ✅ Graph Compilation")
    print("   - Graph definition becomes executable workflow")
    print("   - Compilation validates the graph structure")
    print("   - Compiled graph can be invoked with input state")
    
    print("\n5. ✅ Visualization")
    print("   - Built-in Mermaid diagram generation")
    print("   - PNG export for documentation")
    print("   - Debugging and understanding workflow structure")
    
    print("\n6. ✅ Conditional Routing")
    print("   - Dynamic workflow paths based on conditions")
    print("   - Content-based routing (e.g., sensitive data)")
    print("   - Multi-path processing capabilities")


def main():
    """Main function to run all demonstrations."""
    print("🚀 LangGraph Overview - Exercise 01 Solution")
    print("Building Your First LangGraph Application")
    print("=" * 50)
    
    # Demonstrate core concepts
    demonstrate_core_concepts()
    
    # Test basic graph
    test_graph()
    
    # Visualize basic graph
    visualize_graph()
    
    # Test advanced graph with conditional routing
    test_advanced_graph()
    
    print("\n🎉 Exercise completed successfully!")
    print("\nKey concepts demonstrated:")
    print("✅ State management with TypedDict")
    print("✅ Node creation and execution")
    print("✅ Edge connections (normal and conditional)")
    print("✅ Graph compilation and execution")
    print("✅ Input validation and categorization")
    print("✅ Text processing and output formatting")
    print("✅ Graph visualization")
    print("✅ Conditional routing based on content")
    
    print("\n📝 Summary:")
    print("This solution demonstrates the fundamental building blocks")
    print("of LangGraph applications, showing how to create stateful,")
    print("multi-step workflows with conditional routing and proper")
    print("error handling. The advanced example shows how to implement")
    print("sensitive content detection and appropriate routing.")


if __name__ == "__main__":
    main()