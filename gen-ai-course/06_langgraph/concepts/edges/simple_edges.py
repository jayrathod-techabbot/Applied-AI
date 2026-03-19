#!/usr/bin/env python3
"""
Simple Edges - LangGraph Core Concept

This file demonstrates simple (normal) edges in LangGraph, which always
execute and define the basic flow of execution through the graph.

Key Concepts:
- Normal edge creation
- Sequential execution
- Graph flow definition
- Entry point setup
"""

from typing import TypedDict


class SimpleState(TypedDict):
    """Basic state for simple edge examples."""
    input_text: str
    processed_text: str
    step_count: int


def create_simple_edges_example():
    """
    Create an example of simple edges.
    
    Returns:
        str: Description of the edge flow
    """
    # This demonstrates the concept of simple edges
    # In actual LangGraph, you would use StateGraph.add_edge()
    
    edge_flow = """
    Graph Flow with Simple Edges:
    Entry Point -> Node A -> Node B -> Node C -> END
    
    Each arrow (->) represents a simple edge that always executes.
    """
    
    return edge_flow


def demonstrate_simple_edges():
    """
    Demonstrate simple edge concepts.
    """
    print("🎯 Simple Edges Demonstration")
    print("=" * 29)
    
    # Show edge flow
    flow = create_simple_edges_example()
    print(flow)
    
    # Explain simple edges
    print("Simple Edge Characteristics:")
    print("• Always execute (no conditions)")
    print("• Define sequential flow")
    print("• Connect nodes in linear path")
    print("• Use StateGraph.add_edge() method")
    
    print("✅ Simple edges demonstration completed")


if __name__ == "__main__":
    demonstrate_simple_edges()