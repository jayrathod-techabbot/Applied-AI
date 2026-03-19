#!/usr/bin/env python3
"""
Basic Node Definition - LangGraph Core Concept

This file demonstrates the fundamental concept of basic node definition
in LangGraph. Nodes are the computational units that process and transform
state as it flows through the graph.

Key Concepts:
- Node function signature
- State input/output
- Simple node examples
- Node execution flow
"""

from typing import TypedDict


class BasicState(TypedDict):
    """Basic state for node examples."""
    input_text: str
    processed_text: str
    step_count: int


def basic_node_example(state: BasicState) -> BasicState:
    """
    Basic Node Example:
    
    Nodes are Python functions that:
    1. Take current state as input
    2. Process/transform the state
    3. Return updated state
    
    This simple node just converts text to uppercase and increments step count.
    """
    print(f"🔄 Executing basic_node with input: '{state['input_text']}'")
    
    # Process the input
    processed = state['input_text'].upper()
    
    # Return updated state
    return {
        'input_text': state['input_text'],      # Keep original input
        'processed_text': processed,            # Add processed text
        'step_count': state['step_count'] + 1   # Increment step counter
    }


def create_basic_node_example():
    """
    Create an example of basic node execution.
    
    Returns:
        BasicState: Example state after node execution
    """
    # Create initial state
    initial_state = BasicState(
        input_text="hello world",
        processed_text="",
        step_count=0
    )
    
    # Execute node
    result_state = basic_node_example(initial_state)
    
    return result_state


def demonstrate_basic_node():
    """
    Demonstrate basic node usage.
    """
    print("🎯 Basic Node Demonstration")
    print("=" * 28)
    
    # Execute basic node
    result = create_basic_node_example()
    print(f"Result: {result}")
    
    # Show the transformation
    print(f"Input: '{result['input_text']}' -> Output: '{result['processed_text']}'")
    print(f"Step count: {result['step_count']}")
    print("✅ Basic node demonstration completed")


if __name__ == "__main__":
    demonstrate_basic_node()