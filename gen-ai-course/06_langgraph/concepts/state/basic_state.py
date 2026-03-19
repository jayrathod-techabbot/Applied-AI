#!/usr/bin/env python3
"""
Basic State Definition - LangGraph Core Concept

This file demonstrates the fundamental concept of basic state definition
in LangGraph. State is the backbone of LangGraph applications - it flows
through the graph and carries information between nodes.

Key Concepts:
- State definition with TypedDict
- Basic state structure
- State flow through graphs
"""

from typing import TypedDict


class BasicState(TypedDict):
    """
    Basic State Example:
    
    The simplest form of state - a dictionary-like structure that flows
    through the graph. Every node receives the current state and can modify it.
    
    Key characteristics:
    - Must be a TypedDict for type safety
    - Contains all data needed by nodes
    - Flows through the entire graph execution
    - Can be modified by any node
    """
    user_input: str          # Input from user
    processed_text: str      # Text after processing
    step_count: int          # Track execution steps


def create_basic_state_example():
    """
    Create an example of basic state.
    
    Returns:
        BasicState: Example state with sample data
    """
    return BasicState(
        user_input="Hello, LangGraph!",
        processed_text="",
        step_count=0
    )


def demonstrate_basic_state():
    """
    Demonstrate basic state usage.
    """
    print("🎯 Basic State Demonstration")
    print("=" * 30)
    
    # Create initial state
    state = create_basic_state_example()
    print(f"Initial state: {state}")
    
    # Modify state (simulating node processing)
    state['processed_text'] = state['user_input'].upper()
    state['step_count'] = state['step_count'] + 1
    
    print(f"Modified state: {state}")
    print("✅ Basic state demonstration completed")


if __name__ == "__main__":
    demonstrate_basic_state()