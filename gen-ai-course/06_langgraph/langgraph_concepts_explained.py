#!/usr/bin/env python3
"""
LangGraph Concepts Explained - Comprehensive Guide

This file provides a detailed explanation of all LangGraph concepts with
comprehensive comments and practical examples. It serves as both a learning
resource and a reference implementation for understanding LangGraph.

Author: Applied AI Course
Purpose: Educational demonstration of LangGraph concepts
"""

# Import required modules
from typing import TypedDict, List, Optional, Dict, Any, Union, Callable
from langgraph.graph import StateGraph, END
import asyncio
import time
import json
from datetime import datetime


# ============================================================================
# 1. STATE MANAGEMENT - THE FOUNDATION OF LANGGRAPH
# ============================================================================

class BasicState(TypedDict):
    """
    Basic State Example:
    This is the simplest form of state - a dictionary-like structure that flows
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


class AdvancedState(TypedDict):
    """
    Advanced State Example:
    Shows a more comprehensive state structure suitable for production applications.
    
    Components:
    - Core identification: session tracking
    - Input and processing: main data flow
    - Workflow tracking: execution state
    - Results and outputs: final and intermediate results
    - Metadata and context: additional information
    """
    # Core identification - essential for multi-user applications
    session_id: str              # Unique session identifier
    user_id: Optional[str]       # User identification
    timestamp: datetime          # When state was created/updated
    
    # Input and processing - the main data being processed
    input_text: str              # Original user input
    processed_data: Dict[str, Any]  # Processed information
    validation_errors: List[str]    # Any validation issues
    
    # Workflow tracking - helps debug and monitor execution
    current_step: str            # Current execution step
    completed_steps: List[str]   # Steps that have been completed
    next_actions: List[str]      # Planned next steps
    
    # Results and outputs - both intermediate and final
    intermediate_results: List[Dict[str, Any]]  # Partial results
    final_output: Optional[str]   # Final result
    confidence_score: Optional[float]  # Quality/confidence of result
    
    # Metadata and context - additional information
    context: Dict[str, Any]      # Contextual information
    metadata: Dict[str, Any]     # Additional metadata
    debug_info: Dict[str, Any]   # Debugging information


# ============================================================================
# 2. NODES - THE COMPUTATIONAL UNITS
# ============================================================================

def basic_node_example(state: BasicState) -> BasicState:
    """
    Basic Node Example:
    
    Nodes are Python functions that:
    1. Take current state as input
    2. Process/transform the state
    3. Return updated state
    
    This simple node just converts text to uppercase and increments step count.
    """
    print(f"🔄 Executing basic_node with input: '{state['user_input']}'")
    
    # Process the input
    processed = state['user_input'].upper()
    
    # Return updated state
    return {
        'user_input': state['user_input'],      # Keep original input
        'processed_text': processed,            # Add processed text
        'step_count': state['step_count'] + 1   # Increment step counter
    }


def validation_node(state: AdvancedState) -> AdvancedState:
    """
    Validation Node Example:
    
    This node demonstrates input validation and error handling.
    It checks for common issues and adds validation errors to state.
    """
    print(f"✅ Validating input: '{state['input_text'][:50]}...'")
    
    validation_errors = []
    
    # Check for empty input
    if not state['input_text'] or not state['input_text'].strip():
        validation_errors.append("Input text cannot be empty")
    
    # Check input length
    if len(state['input_text']) > 10000:
        validation_errors.append("Input text too long (max 10000 characters)")
    
    # Check for sensitive information
    sensitive_keywords = ["password", "credit card", "ssn"]
    text_lower = state['input_text'].lower()
    if any(keyword in text_lower for keyword in sensitive_keywords):
        validation_errors.append("Input contains sensitive information")
    
    # Update state with validation results
    return {
        **state,  # Keep all existing state
        'validation_errors': validation_errors,
        'current_step': 'validation',
        'completed_steps': state['completed_steps'] + ['validation']
    }


def processing_node(state: AdvancedState) -> AdvancedState:
    """
    Processing Node Example:
    
    This node performs the main business logic. In a real application,
    this might call APIs, run ML models, or perform complex calculations.
    """
    print(f"⚙️  Processing input with {len(state['input_text'])} characters")
    
    # Simulate processing time
    time.sleep(0.1)
    
    # Simple text analysis
    word_count = len(state['input_text'].split())
    char_count = len(state['input_text'])
    
    # Calculate confidence based on input quality
    confidence = 0.8 if word_count > 5 else 0.5
    
    # Create processed data
    processed_data = {
        'word_count': word_count,
        'char_count': char_count,
        'analysis_timestamp': datetime.now().isoformat(),
        'processing_version': '1.0'
    }
    
    return {
        **state,
        'processed_data': processed_data,
        'confidence_score': confidence,
        'current_step': 'processing',
        'completed_steps': state['completed_steps'] + ['processing']
    }


async def async_node_example(state: AdvancedState) -> AdvancedState:
    """
    Async Node Example:
    
    LangGraph supports async nodes for I/O operations like API calls,
    database queries, or file operations. Use async/await syntax.
    """
    print(f"🌐 Making async request for: '{state['input_text'][:30]}...'")
    
    # Simulate async operation (e.g., API call)
    await asyncio.sleep(0.5)
    
    # Simulate external service response
    external_result = {
        'service_response': 'success',
        'data_enriched': True,
        'timestamp': datetime.now().isoformat()
    }
    
    return {
        **state,
        'processed_data': {
            **state['processed_data'],
            'external_service': external_result
        },
        'current_step': 'async_processing',
        'completed_steps': state['completed_steps'] + ['async_processing']
    }


def error_handling_node(state: AdvancedState) -> AdvancedState:
    """
    Error Handling Node Example:
    
    Demonstrates comprehensive error handling within nodes.
    Always return valid state, even when errors occur.
    """
    print(f"🛡️  Error handling node execution")
    
    try:
        # Simulate operation that might fail
        if state['confidence_score'] and state['confidence_score'] < 0.3:
            raise ValueError("Confidence score too low for processing")
        
        # Normal processing
        result = f"Processed successfully: {state['input_text'][:20]}..."
        
        return {
            **state,
            'processed_data': {
                **state['processed_data'],
                'error_handling_result': result
            },
            'current_step': 'error_handling_success',
            'completed_steps': state['completed_steps'] + ['error_handling_success']
        }
        
    except ValueError as e:
        # Handle specific validation errors
        return {
            **state,
            'validation_errors': state['validation_errors'] + [str(e)],
            'current_step': 'error_handling_failure',
            'completed_steps': state['completed_steps'] + ['error_handling_failure']
        }
        
    except Exception as e:
        # Handle unexpected errors
        return {
            **state,
            'validation_errors': state['validation_errors'] + [f"Unexpected error: {str(e)}"],
            'current_step': 'error_handling_exception',
            'completed_steps': state['completed_steps'] + ['error_handling_exception']
        }


# ============================================================================
# 3. EDGES - DEFINING WORKFLOW FLOW
# ============================================================================

def create_simple_graph():
    """
    Simple Graph Example:
    
    Demonstrates basic graph creation with normal edges (always execute).
    This is the simplest form of workflow definition.
    """
    print("🏗️  Creating simple graph...")
    
    # Create graph with state type
    graph = StateGraph(BasicState)
    
    # Add nodes to graph
    graph.add_node("input_processing", basic_node_example)
    
    # Set entry point - where execution starts
    graph.set_entry_point("input_processing")
    
    # Add edges - define execution flow
    # Note: Only one node, so it goes directly to END
    graph.add_edge("input_processing", END)
    
    # Compile graph - makes it executable
    return graph.compile()


def create_conditional_graph():
    """
    Conditional Graph Example:
    
    Demonstrates conditional edges that choose next node based on state.
    This enables dynamic workflow routing.
    """
    print("🔀 Creating conditional graph...")
    
    graph = StateGraph(AdvancedState)
    
    # Add nodes
    graph.add_node("validate", validation_node)
    graph.add_node("process", processing_node)
    graph.add_node("error_handler", error_handling_node)
    
    # Set entry point
    graph.set_entry_point("validate")
    
    # Add normal edge (always execute)
    graph.add_edge("validate", "process")
    
    # Add conditional edge - choose next based on validation
    def route_after_validation(state: AdvancedState) -> str:
        """
        Routing function determines next node based on state.
        
        Returns the name of the next node to execute.
        """
        if state['validation_errors']:
            return "error_handler"
        else:
            return "process"
    
    # Conditional edges require a routing function
    graph.add_conditional_edges(
        "validate",           # Source node
        route_after_validation,  # Routing function
        {
            "error_handler": "error_handler",  # If routing returns "error_handler"
            "process": "process"              # If routing returns "process"
        }
    )
    
    # Connect error handler to end
    graph.add_edge("error_handler", END)
    graph.add_edge("process", END)
    
    return graph.compile()


def create_complex_routing_graph():
    """
    Complex Routing Graph Example:
    
    Demonstrates sophisticated routing based on multiple conditions.
    Shows how to build decision trees and complex workflows.
    """
    print("🌳 Creating complex routing graph...")
    
    graph = StateGraph(AdvancedState)
    
    # Add all nodes
    graph.add_node("validate", validation_node)
    graph.add_node("process", processing_node)
    graph.add_node("async_enrichment", async_node_example)
    graph.add_node("quality_check", error_handling_node)
    graph.add_node("error_handler", error_handling_node)
    graph.add_node("retry_handler", lambda s: {**s, 'current_step': 'retry'})
    
    graph.set_entry_point("validate")
    
    # Complex routing logic
    def route_validation(state: AdvancedState) -> str:
        """Route based on validation results."""
        if state['validation_errors']:
            return "error_handler"
        return "process"
    
    def route_processing(state: AdvancedState) -> str:
        """Route based on processing confidence."""
        confidence = state.get('confidence_score', 0.0)
        if confidence > 0.8:
            return "async_enrichment"
        elif confidence > 0.5:
            return "quality_check"
        else:
            return "retry_handler"
    
    def route_quality_check(state: AdvancedState) -> str:
        """Route based on quality assessment."""
        errors = state.get('validation_errors', [])
        if errors:
            return "error_handler"
        return "async_enrichment"
    
    # Set up complex routing
    graph.add_conditional_edges("validate", route_validation, {
        "error_handler": "error_handler",
        "process": "process"
    })
    
    graph.add_conditional_edges("process", route_processing, {
        "async_enrichment": "async_enrichment",
        "quality_check": "quality_check",
        "retry_handler": "retry_handler"
    })
    
    graph.add_conditional_edges("quality_check", route_quality_check, {
        "error_handler": "error_handler",
        "async_enrichment": "async_enrichment"
    })
    
    # Connect remaining edges
    graph.add_edge("async_enrichment", END)
    graph.add_edge("retry_handler", "validate")  # Retry from beginning
    graph.add_edge("error_handler", END)
    
    return graph.compile()


# ============================================================================
# 4. GRAPH EXECUTION AND MONITORING
# ============================================================================

def execute_graph_example():
    """
    Graph Execution Example:
    
    Demonstrates how to execute compiled graphs with different input states.
    Shows both synchronous and streaming execution modes.
    """
    print("\n🚀 EXECUTING GRAPHS")
    print("=" * 50)
    
    # Create and execute simple graph
    simple_app = create_simple_graph()
    
    simple_input = {
        'user_input': 'hello world',
        'processed_text': '',
        'step_count': 0
    }
    
    print("📝 Simple Graph Execution:")
    simple_result = simple_app.invoke(simple_input)
    print(f"Result: {simple_result}")
    
    # Create and execute conditional graph
    conditional_app = create_conditional_graph()
    
    test_cases = [
        {
            'session_id': 'test1',
            'user_id': 'user123',
            'timestamp': datetime.now(),
            'input_text': 'This is a valid input',
            'processed_data': {},
            'validation_errors': [],
            'current_step': '',
            'completed_steps': [],
            'next_actions': [],
            'intermediate_results': [],
            'final_output': None,
            'confidence_score': None,
            'context': {},
            'metadata': {},
            'debug_info': {}
        },
        {
            'session_id': 'test2',
            'user_id': 'user456',
            'timestamp': datetime.now(),
            'input_text': '',  # Empty input to trigger validation error
            'processed_data': {},
            'validation_errors': [],
            'current_step': '',
            'completed_steps': [],
            'next_actions': [],
            'intermediate_results': [],
            'final_output': None,
            'confidence_score': None,
            'context': {},
            'metadata': {},
            'debug_info': {}
        }
    ]
    
    print("\n📝 Conditional Graph Execution:")
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        try:
            result = conditional_app.invoke(test_input)
            print(f"Success! Final step: {result.get('current_step')}")
            if result.get('validation_errors'):
                print(f"Validation errors: {result['validation_errors']}")
        except Exception as e:
            print(f"Error: {e}")


async def execute_async_graph_example():
    """
    Async Graph Execution Example:
    
    Demonstrates executing graphs with async nodes and streaming results.
    Shows how to handle long-running operations and real-time updates.
    """
    print("\n⚡ ASYNC GRAPH EXECUTION")
    print("=" * 50)
    
    # Create graph with async node
    complex_app = create_complex_routing_graph()
    
    async_input = {
        'session_id': 'async_test',
        'user_id': 'async_user',
        'timestamp': datetime.now(),
        'input_text': 'This input will trigger async processing',
        'processed_data': {},
        'validation_errors': [],
        'current_step': '',
        'completed_steps': [],
        'next_actions': [],
        'intermediate_results': [],
        'final_output': None,
        'confidence_score': 0.9,  # High confidence to trigger async path
        'context': {},
        'metadata': {},
        'debug_info': {}
    }
    
    print("📝 Streaming Execution:")
    print("This will show real-time state updates as the graph executes...")
    
    # Execute with streaming to see intermediate results
    try:
        async for chunk in complex_app.astream(async_input):
            print(f"🔄 State update: {chunk}")
    except Exception as e:
        print(f"Async execution error: {e}")


def performance_monitoring_example():
    """
    Performance Monitoring Example:
    
    Demonstrates how to monitor and measure graph execution performance.
    Shows timing, memory usage, and execution metrics.
    """
    print("\n📊 PERFORMANCE MONITORING")
    print("=" * 50)
    
    # Create graph for performance testing
    app = create_complex_routing_graph()
    
    # Test input
    test_input = {
        'session_id': 'perf_test',
        'user_id': 'perf_user',
        'timestamp': datetime.now(),
        'input_text': 'Performance test input with sufficient length to trigger processing',
        'processed_data': {},
        'validation_errors': [],
        'current_step': '',
        'completed_steps': [],
        'next_actions': [],
        'intermediate_results': [],
        'final_output': None,
        'confidence_score': 0.7,
        'context': {},
        'metadata': {},
        'debug_info': {}
    }
    
    # Measure execution time
    start_time = time.time()
    
    try:
        result = app.invoke(test_input)
        execution_time = time.time() - start_time
        
        print(f"✅ Execution completed successfully")
        print(f"⏱️  Execution time: {execution_time:.3f} seconds")
        print(f"📊 Final step: {result.get('current_step')}")
        print(f"📈 Steps completed: {len(result.get('completed_steps', []))}")
        print(f"🎯 Confidence score: {result.get('confidence_score')}")
        
        # Analyze performance
        if execution_time > 1.0:
            print("⚠️  Warning: Execution took longer than expected")
        else:
            print("✅ Performance is within acceptable range")
            
    except Exception as e:
        print(f"❌ Execution failed: {e}")


# ============================================================================
# 5. ERROR HANDLING AND BEST PRACTICES
# ============================================================================

class StateValidator:
    """
    State Validation Class:
    
    Provides utilities for validating state structure and data integrity.
    Essential for maintaining data quality in production applications.
    """
    
    @staticmethod
    def validate_state_structure(state: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that state contains all required fields.
        
        Args:
            state: The state dictionary to validate
            required_fields: List of field names that must be present
            
        Returns:
            bool: True if valid, False otherwise
        """
        missing_fields = [field for field in required_fields if field not in state]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print(f"✅ State structure validation passed")
        return True
    
    @staticmethod
    def validate_state_types(state: Dict[str, Any], type_schema: Dict[str, type]) -> bool:
        """
        Validate that state fields have correct types.
        
        Args:
            state: The state dictionary to validate
            type_schema: Dictionary mapping field names to expected types
            
        Returns:
            bool: True if valid, False otherwise
        """
        type_errors = []
        
        for field, expected_type in type_schema.items():
            if field in state:
                actual_type = type(state[field])
                if not issubclass(actual_type, expected_type):
                    type_errors.append(f"Field '{field}': expected {expected_type}, got {actual_type}")
        
        if type_errors:
            print(f"❌ Type validation errors: {type_errors}")
            return False
        
        print(f"✅ State type validation passed")
        return True


def robust_node_execution_example():
    """
    Robust Node Execution Example:
    
    Demonstrates best practices for writing robust nodes that handle
    errors gracefully and maintain data integrity.
    """
    print("\n🛡️  ROBUST NODE EXECUTION")
    print("=" * 50)
    
    def robust_node(state: AdvancedState) -> AdvancedState:
        """
        Example of a robust node implementation.
        
        Best practices demonstrated:
        1. Input validation
        2. Error handling with specific exceptions
        3. Graceful degradation
        4. Comprehensive logging
        5. State integrity preservation
        """
        print(f"🔧 Executing robust node...")
        
        try:
            # 1. Validate inputs
            if not StateValidator.validate_state_structure(state, ['input_text', 'session_id']):
                raise ValueError("Invalid state structure")
            
            # 2. Perform main processing with error handling
            input_text = state['input_text']
            
            if not input_text or not input_text.strip():
                raise ValueError("Input text is empty or whitespace")
            
            # 3. Core business logic with potential failure points
            processed_length = len(input_text)
            
            if processed_length > 50000:
                print("⚠️  Warning: Input text is very long")
                # Graceful degradation - truncate instead of failing
                input_text = input_text[:50000]
            
            # 4. Create result
            result_data = {
                'processed_length': processed_length,
                'timestamp': datetime.now().isoformat(),
                'node_version': '2.0'
            }
            
            # 5. Return updated state
            return {
                **state,
                'processed_data': {
                    **state.get('processed_data', {}),
                    'robust_node_result': result_data
                },
                'current_step': 'robust_processing',
                'completed_steps': state.get('completed_steps', []) + ['robust_processing']
            }
            
        except ValueError as e:
            # Handle specific validation errors
            print(f"❌ Validation error: {e}")
            return {
                **state,
                'validation_errors': state.get('validation_errors', []) + [str(e)],
                'current_step': 'robust_processing_error',
                'completed_steps': state.get('completed_steps', []) + ['robust_processing_error']
            }
            
        except Exception as e:
            # Handle unexpected errors
            print(f"🚨 Unexpected error: {e}")
            return {
                **state,
                'validation_errors': state.get('validation_errors', []) + [f"Unexpected error: {str(e)}"],
                'current_step': 'robust_processing_exception',
                'completed_steps': state.get('completed_steps', []) + ['robust_processing_exception']
            }
    
    # Test the robust node
    test_state = {
        'session_id': 'robust_test',
        'user_id': 'robust_user',
        'timestamp': datetime.now(),
        'input_text': 'Test input for robust processing',
        'processed_data': {},
        'validation_errors': [],
        'current_step': '',
        'completed_steps': [],
        'next_actions': [],
        'intermediate_results': [],
        'final_output': None,
        'confidence_score': None,
        'context': {},
        'metadata': {},
        'debug_info': {}
    }
    
    result = robust_node(test_state)
    print(f"✅ Robust node execution completed")
    print(f"📊 Final step: {result.get('current_step')}")
    print(f"⚠️  Validation errors: {result.get('validation_errors')}")


# ============================================================================
# 6. MAIN EXECUTION AND DEMONSTRATION
# ============================================================================

def main():
    """
    Main function that demonstrates all LangGraph concepts.
    
    This serves as both a learning tool and a test suite for the concepts.
    """
    print("🎯 LANGGRAPH CONCEPTS DEMONSTRATION")
    print("=" * 60)
    print("This file demonstrates all core LangGraph concepts with")
    print("comprehensive examples and detailed explanations.")
    print("=" * 60)
    
    try:
        # 1. Execute synchronous examples
        execute_graph_example()
        
        # 2. Execute performance monitoring
        performance_monitoring_example()
        
        # 3. Execute robust node example
        robust_node_execution_example()
        
        # 4. Execute async examples
        print("\n⚡ EXECUTING ASYNC EXAMPLES")
        print("=" * 50)
        asyncio.run(execute_async_graph_example())
        
        print("\n🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("\n📋 SUMMARY OF CONCEPTS COVERED:")
        print("✅ State Management - TypedDict schemas and validation")
        print("✅ Node Creation - Synchronous and asynchronous nodes")
        print("✅ Edge Types - Normal and conditional routing")
        print("✅ Graph Compilation - Creating executable workflows")
        print("✅ Error Handling - Robust error handling patterns")
        print("✅ Performance Monitoring - Execution metrics and timing")
        print("✅ Best Practices - Production-ready implementation patterns")
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        print("Please check the error above and ensure all dependencies are installed.")
        return False
    
    return True


if __name__ == "__main__":
    """
    Entry point for the LangGraph concepts demonstration.
    
    Run this file to see all concepts in action with detailed output.
    """
    success = main()
    
    if success:
        print("\n📖 NEXT STEPS:")
        print("1. Study the code comments to understand each concept")
        print("2. Modify the examples to experiment with different scenarios")
        print("3. Apply these patterns to your own LangGraph applications")
        print("4. Refer to the official LangGraph documentation for advanced features")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("If you encounter errors, check:")
        print("- LangGraph is installed: pip install langgraph")
        print("- All dependencies are available")
        print("- Python version compatibility")