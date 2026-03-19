#!/usr/bin/env python3
"""
Node Composition - LangGraph Core Concept

This file demonstrates node composition, which allows building complex
functionality from simple components by chaining multiple nodes together.

Key Concepts:
- Node composition patterns
- Function chaining
- Modular node design
- Pipeline creation
"""

from typing import TypedDict, Callable, Dict, Any


class CompositionState(TypedDict):
    """State for composition examples."""
    input_text: str
    processed_text: str
    step_count: int


def compose_nodes(*nodes: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Node Composition Example:
    
    Compose multiple nodes into a single node.
    This enables building complex functionality from simple components.
    
    Args:
        *nodes: Variable number of node functions to compose
        
    Returns:
        A single composed node function
    """
    def composed_node(state: Dict[str, Any]) -> Dict[str, Any]:
        current_state = state
        for node in nodes:
            current_state = node(current_state)
        return current_state
    
    return composed_node


def validation_node(state: CompositionState) -> CompositionState:
    """Simple validation node."""
    print(f"✅ Validating: '{state['input_text']}'")
    return {
        **state,
        'step_count': state['step_count'] + 1
    }


def processing_node(state: CompositionState) -> CompositionState:
    """Simple processing node."""
    print(f"⚙️  Processing: '{state['input_text']}'")
    return {
        **state,
        'processed_text': state['input_text'].upper(),
        'step_count': state['step_count'] + 1
    }


def create_composed_pipeline():
    """
    Create a composed pipeline of nodes.
    
    Returns:
        Callable: Composed node function
    """
    # Create composed pipeline
    pipeline = compose_nodes(
        validation_node,
        processing_node
    )
    
    return pipeline


def demonstrate_node_composition():
    """
    Demonstrate node composition usage.
    """
    print("🎯 Node Composition Demonstration")
    print("=" * 33)
    
    # Create pipeline
    pipeline = create_composed_pipeline()
    
    # Create initial state
    initial_state = CompositionState(
        input_text="hello composition",
        processed_text="",
        step_count=0
    )
    
    # Execute composed pipeline
    result = pipeline(initial_state)
    print(f"Result: {result}")
    print(f"Final text: '{result['processed_text']}'")
    print(f"Total steps: {result['step_count']}")
    print("✅ Node composition demonstration completed")


if __name__ == "__main__":
    demonstrate_node_composition()