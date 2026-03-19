#!/usr/bin/env python3
"""
Basic Graph Execution - LangGraph Core Concept

This file demonstrates basic graph execution in LangGraph, showing how
to run a compiled graph with input state and produce output.

Key Concepts:
- Graph compilation
- State input/output
- Basic execution flow
- Result processing
"""

from typing import TypedDict


class ExecutionState(TypedDict):
    """State for execution examples."""
    input_text: str
    processed_text: str
    step_count: int


def create_basic_execution_example():
    """
    Create an example of basic graph execution.
    
    Returns:
        ExecutionState: Example state after execution
    """
    # Simulate basic graph execution
    # In actual LangGraph, you would compile and invoke a graph
    
    initial_state = ExecutionState(
        input_text="hello execution",
        processed_text="",
        step_count=0
    )
    
    # Simulate node execution
    initial_state['processed_text'] = initial_state['input_text'].upper()
    initial_state['step_count'] = initial_state['step_count'] + 1
    
    return initial_state


def demonstrate_basic_execution():
    """
    Demonstrate basic execution concepts.
    """
    print("🎯 Basic Execution Demonstration")
    print("=" * 32)
    
    # Execute graph
    result = create_basic_execution_example()
    print(f"Execution result: {result}")
    
    # Show execution flow
    print("Basic Execution Flow:")
    print("1. Create initial state")
    print("2. Compile graph (StateGraph.compile())")
    print("3. Invoke graph with state (graph.invoke(state))")
    print("4. Process through nodes")
    print("5. Return final state")
    
    print("✅ Basic execution demonstration completed")


if __name__ == "__main__":
    demonstrate_basic_execution()