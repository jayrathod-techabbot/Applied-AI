#!/usr/bin/env python3
"""
Conditional Edges - LangGraph Core Concept

This file demonstrates conditional edges in LangGraph, which choose the
next node based on the current state, enabling dynamic workflow routing.

Key Concepts:
- Conditional edge creation
- Routing functions
- Dynamic workflow paths
- State-based decisions
"""

from typing import TypedDict


class ConditionalState(TypedDict):
    """State for conditional edge examples."""
    user_input: str
    category: str
    confidence_score: float


def route_after_validation(state: ConditionalState) -> str:
    """
    Routing Function Example:
    
    Determines next node based on state.
    
    Args:
        state: Current state
        
    Returns:
        str: Name of next node to execute
    """
    if state['confidence_score'] > 0.8:
        return "high_confidence_handler"
    elif state['confidence_score'] > 0.5:
        return "medium_confidence_handler"
    else:
        return "low_confidence_handler"


def create_conditional_edges_example():
    """
    Create an example of conditional edges.
    
    Returns:
        str: Description of conditional routing
    """
    # This demonstrates the concept of conditional edges
    # In actual LangGraph, you would use StateGraph.add_conditional_edges()
    
    routing_logic = """
    Conditional Edge Routing:
    
    if confidence_score > 0.8:
        -> high_confidence_handler
    elif confidence_score > 0.5:
        -> medium_confidence_handler  
    else:
        -> low_confidence_handler
    
    Routing function determines path based on state values.
    """
    
    return routing_logic


def demonstrate_conditional_edges():
    """
    Demonstrate conditional edge concepts.
    """
    print("🎯 Conditional Edges Demonstration")
    print("=" * 34)
    
    # Show routing logic
    logic = create_conditional_edges_example()
    print(logic)
    
    # Test routing function
    test_state = ConditionalState(
        user_input="Test input",
        category="test",
        confidence_score=0.7
    )
    
    next_node = route_after_validation(test_state)
    print(f"Test state routing: {next_node}")
    
    print("✅ Conditional edges demonstration completed")


if __name__ == "__main__":
    demonstrate_conditional_edges()