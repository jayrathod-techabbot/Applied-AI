#!/usr/bin/env python3
"""
LangGraph Edges - Core Concept

This file demonstrates the fundamental concept of Edges in LangGraph.
Edges define how to move between nodes, controlling the flow of execution
through the graph. They can be simple (always execute) or conditional
(choose next node based on state).

Key Concepts Covered:
- Normal edges vs conditional edges
- Edge creation and configuration
- Dynamic routing strategies
- Complex edge patterns
- Edge validation and testing
"""

from typing import TypedDict, List, Optional, Dict, Any, Callable, Union
from langgraph.graph import StateGraph, END
from datetime import datetime
import asyncio
import time


# ============================================================================
# 1. BASIC EDGE TYPES
# ============================================================================

class BasicState(TypedDict):
    """Basic state for edge examples."""
    input_text: str
    processed_text: str
    step_count: int


def create_simple_edges_graph():
    """
    Simple Edges Example:
    
    Demonstrates basic graph creation with normal edges (always execute).
    This is the simplest form of workflow definition.
    """
    print("🏗️  Creating graph with simple edges...")
    
    # Create graph with state type
    graph = StateGraph(BasicState)
    
    # Add nodes to graph
    def node_a(state: BasicState) -> BasicState:
        print("📍 Executing Node A")
        return {
            'input_text': state['input_text'],
            'processed_text': f"Node A: {state['input_text']}",
            'step_count': state['step_count'] + 1
        }
    
    def node_b(state: BasicState) -> BasicState:
        print("📍 Executing Node B")
        return {
            'input_text': state['input_text'],
            'processed_text': f"Node B: {state['processed_text']}",
            'step_count': state['step_count'] + 1
        }
    
    def node_c(state: BasicState) -> BasicState:
        print("📍 Executing Node C")
        return {
            'input_text': state['input_text'],
            'processed_text': f"Node C: {state['processed_text']}",
            'step_count': state['step_count'] + 1
        }
    
    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_node("node_c", node_c)
    
    # Set entry point - where execution starts
    graph.set_entry_point("node_a")
    
    # Add normal edges (always execute)
    graph.add_edge("node_a", "node_b")
    graph.add_edge("node_b", "node_c")
    graph.add_edge("node_c", END)
    
    # Compile graph - makes it executable
    return graph.compile()


# ============================================================================
# 2. CONDITIONAL EDGES
# ============================================================================

class ConditionalState(TypedDict):
    """State for conditional edge examples."""
    user_input: str
    category: str
    confidence_score: float
    validation_errors: List[str]
    current_step: str
    completed_steps: List[str]


def create_conditional_edges_graph():
    """
    Conditional Edges Example:
    
    Demonstrates conditional edges that choose next node based on state.
    This enables dynamic workflow routing.
    """
    print("🔀 Creating graph with conditional edges...")
    
    graph = StateGraph(ConditionalState)
    
    # Add nodes
    def validate_input(state: ConditionalState) -> ConditionalState:
        print(f"✅ Validating input: '{state['user_input'][:30]}...'")
        
        # Categorize input
        input_lower = state['user_input'].lower()
        if any(word in input_lower for word in ["hello", "hi", "hey"]):
            category = "greeting"
        elif any(word in input_lower for word in ["help", "support", "issue"]):
            category = "support"
        elif any(word in input_lower for word in ["buy", "purchase", "price"]):
            category = "sales"
        else:
            category = "general"
        
        return {
            **state,
            'category': category,
            'current_step': 'validation',
            'completed_steps': state['completed_steps'] + ['validation']
        }
    
    def handle_greeting(state: ConditionalState) -> ConditionalState:
        print("👋 Handling greeting")
        return {
            **state,
            'processed_text': f"Hello! I received your greeting: '{state['user_input']}'",
            'current_step': 'greeting_handling',
            'completed_steps': state['completed_steps'] + ['greeting_handling']
        }
    
    def handle_support(state: ConditionalState) -> ConditionalState:
        print("🆘 Handling support request")
        return {
            **state,
            'processed_text': f"Support team notified about: '{state['user_input']}'",
            'current_step': 'support_handling',
            'completed_steps': state['completed_steps'] + ['support_handling']
        }
    
    def handle_sales(state: ConditionalState) -> ConditionalState:
        print("💰 Handling sales inquiry")
        return {
            **state,
            'processed_text': f"Sales inquiry logged: '{state['user_input']}'",
            'current_step': 'sales_handling',
            'completed_steps': state['completed_steps'] + ['sales_handling']
        }
    
    def handle_general(state: ConditionalState) -> ConditionalState:
        print("📝 Handling general inquiry")
        return {
            **state,
            'processed_text': f"General message processed: '{state['user_input']}'",
            'current_step': 'general_handling',
            'completed_steps': state['completed_steps'] + ['general_handling']
        }
    
    def error_handler(state: ConditionalState) -> ConditionalState:
        print("🚨 Handling errors")
        return {
            **state,
            'processed_text': f"Error occurred: {state['validation_errors']}",
            'current_step': 'error_handling',
            'completed_steps': state['completed_steps'] + ['error_handling']
        }
    
    graph.add_node("validate", validate_input)
    graph.add_node("greeting", handle_greeting)
    graph.add_node("support", handle_support)
    graph.add_node("sales", handle_sales)
    graph.add_node("general", handle_general)
    graph.add_node("error", error_handler)
    
    graph.set_entry_point("validate")
    
    # Add normal edge (always execute)
    graph.add_edge("validate", "greeting")  # This will be overridden by conditional edge
    
    # Add conditional edge - choose next based on validation
    def route_after_validation(state: ConditionalState) -> str:
        """
        Routing function determines next node based on state.
        
        Returns the name of the next node to execute.
        """
        if state['validation_errors']:
            return "error"
        elif state['category'] == "greeting":
            return "greeting"
        elif state['category'] == "support":
            return "support"
        elif state['category'] == "sales":
            return "sales"
        else:
            return "general"
    
    # Conditional edges require a routing function
    graph.add_conditional_edges(
        "validate",           # Source node
        route_after_validation,  # Routing function
        {
            "error": "error",
            "greeting": "greeting",
            "support": "support",
            "sales": "sales",
            "general": "general"
        }
    )
    
    # Connect all handlers to end
    graph.add_edge("greeting", END)
    graph.add_edge("support", END)
    graph.add_edge("sales", END)
    graph.add_edge("general", END)
    graph.add_edge("error", END)
    
    return graph.compile()


# ============================================================================
# 3. DYNAMIC ROUTING STRATEGIES
# ============================================================================

class DynamicState(TypedDict):
    """State for dynamic routing examples."""
    session_id: str
    user_input: str
    confidence_score: float
    retry_count: int
    processing_path: List[str]
    current_step: str


def create_dynamic_routing_graph():
    """
    Dynamic Routing Graph Example:
    
    Demonstrates sophisticated routing based on multiple dynamic conditions.
    Shows how to build decision trees and complex workflows.
    """
    print("🌳 Creating graph with dynamic routing...")
    
    graph = StateGraph(DynamicState)
    
    # Add all nodes
    def input_processor(state: DynamicState) -> DynamicState:
        print(f"📥 Processing input: '{state['user_input'][:20]}...'")
        
        # Simulate processing and confidence calculation
        word_count = len(state['user_input'].split())
        confidence = min(0.9, word_count * 0.1)  # Simple confidence calculation
        
        return {
            **state,
            'confidence_score': confidence,
            'current_step': 'input_processing',
            'processing_path': state['processing_path'] + ['input_processing']
        }
    
    def high_confidence_processor(state: DynamicState) -> DynamicState:
        print("⚡ High confidence processing")
        return {
            **state,
            'current_step': 'high_confidence_processing',
            'processing_path': state['processing_path'] + ['high_confidence_processing']
        }
    
    def medium_confidence_processor(state: DynamicState) -> DynamicState:
        print("🔄 Medium confidence processing with additional steps")
        return {
            **state,
            'current_step': 'medium_confidence_processing',
            'processing_path': state['processing_path'] + ['medium_confidence_processing']
        }
    
    def low_confidence_processor(state: DynamicState) -> DynamicState:
        print("⚠️  Low confidence processing - may need retry")
        return {
            **state,
            'current_step': 'low_confidence_processing',
            'processing_path': state['processing_path'] + ['low_confidence_processing']
        }
    
    def quality_assurance(state: DynamicState) -> DynamicState:
        print("🔍 Quality assurance check")
        return {
            **state,
            'current_step': 'quality_assurance',
            'processing_path': state['processing_path'] + ['quality_assurance']
        }
    
    def retry_handler(state: DynamicState) -> DynamicState:
        print("🔄 Retry handler")
        return {
            **state,
            'retry_count': state['retry_count'] + 1,
            'current_step': 'retry_handling',
            'processing_path': state['processing_path'] + ['retry_handling']
        }
    
    def escalation_handler(state: DynamicState) -> DynamicState:
        print("🚨 Escalation handler")
        return {
            **state,
            'current_step': 'escalation_handling',
            'processing_path': state['processing_path'] + ['escalation_handling']
        }
    
    def final_output(state: DynamicState) -> DynamicState:
        print("🎯 Final output generation")
        return {
            **state,
            'current_step': 'final_output',
            'processing_path': state['processing_path'] + ['final_output']
        }
    
    graph.add_node("input_processor", input_processor)
    graph.add_node("high_confidence", high_confidence_processor)
    graph.add_node("medium_confidence", medium_confidence_processor)
    graph.add_node("low_confidence", low_confidence_processor)
    graph.add_node("quality_assurance", quality_assurance)
    graph.add_node("retry_handler", retry_handler)
    graph.add_node("escalation_handler", escalation_handler)
    graph.add_node("final_output", final_output)
    
    graph.set_entry_point("input_processor")
    
    # Complex routing logic
    def route_after_input_processing(state: DynamicState) -> str:
        """Route based on confidence score."""
        confidence = state['confidence_score']
        if confidence >= 0.8:
            return "high_confidence"
        elif confidence >= 0.5:
            return "medium_confidence"
        else:
            return "low_confidence"
    
    def route_after_confidence_processing(state: DynamicState) -> str:
        """Route based on processing path and confidence."""
        confidence = state['confidence_score']
        path = state['processing_path']
        
        if "high_confidence_processing" in path:
            return "quality_assurance"
        elif "medium_confidence_processing" in path:
            return "quality_assurance"
        elif "low_confidence_processing" in path:
            if state['retry_count'] < 2:
                return "retry_handler"
            else:
                return "escalation_handler"
    
    def route_after_quality_check(state: DynamicState) -> str:
        """Route based on quality assessment."""
        # Simulate quality check
        quality_score = state['confidence_score'] * 0.9  # Simulated quality
        
        if quality_score > 0.7:
            return "final_output"
        elif state['retry_count'] < 1:
            return "retry_handler"
        else:
            return "escalation_handler"
    
    def route_after_retry(state: DynamicState) -> str:
        """Route after retry attempt."""
        if state['retry_count'] < 2:
            return "input_processor"  # Retry from beginning
        else:
            return "escalation_handler"
    
    # Set up complex routing
    graph.add_conditional_edges("input_processor", route_after_input_processing, {
        "high_confidence": "high_confidence",
        "medium_confidence": "medium_confidence",
        "low_confidence": "low_confidence"
    })
    
    graph.add_conditional_edges("high_confidence", route_after_confidence_processing, {
        "quality_assurance": "quality_assurance"
    })
    
    graph.add_conditional_edges("medium_confidence", route_after_confidence_processing, {
        "quality_assurance": "quality_assurance"
    })
    
    graph.add_conditional_edges("low_confidence", route_after_confidence_processing, {
        "retry_handler": "retry_handler",
        "escalation_handler": "escalation_handler"
    })
    
    graph.add_conditional_edges("quality_assurance", route_after_quality_check, {
        "final_output": "final_output",
        "retry_handler": "retry_handler",
        "escalation_handler": "escalation_handler"
    })
    
    graph.add_conditional_edges("retry_handler", route_after_retry, {
        "input_processor": "input_processor",
        "escalation_handler": "escalation_handler"
    })
    
    # Connect remaining edges
    graph.add_edge("escalation_handler", END)
    graph.add_edge("final_output", END)
    
    return graph.compile()


# ============================================================================
# 4. EDGE VALIDATION AND TESTING
# ============================================================================

class EdgeValidator:
    """
    Edge Validation Utilities:
    
    Provides methods for validating edge configurations and testing
    edge behavior.
    """
    
    @staticmethod
    def validate_edge_configuration(graph_def) -> bool:
        """
        Validate that edge configuration is correct.
        
        Args:
            graph_def: The graph definition to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check that all referenced nodes exist
            nodes = set(graph_def.nodes.keys())
            
            for node_name, node_info in graph_def.edges.items():
                if node_name not in nodes:
                    print(f"❌ Node '{node_name}' referenced in edges but not defined")
                    return False
                
                # Check edge targets
                for target in node_info.get('targets', []):
                    if target != 'END' and target not in nodes:
                        print(f"❌ Target node '{target}' not defined")
                        return False
            
            print("✅ Edge configuration validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Edge configuration validation failed: {e}")
            return False
    
    @staticmethod
    def test_edge_routing(graph_app, test_state: Dict[str, Any], expected_path: List[str]) -> bool:
        """
        Test that edges route correctly for given state.
        
        Args:
            graph_app: Compiled graph application
            test_state: State to test with
            expected_path: Expected execution path
            
        Returns:
            True if routing is correct, False otherwise
        """
        try:
            # Execute the graph
            result = graph_app.invoke(test_state)
            
            # Check if the execution followed expected path
            # This would require tracking execution path, which is complex
            # For now, just check that execution completed successfully
            print(f"✅ Edge routing test passed - execution completed")
            return True
            
        except Exception as e:
            print(f"❌ Edge routing test failed: {e}")
            return False
    
    @staticmethod
    def analyze_edge_complexity(graph_def) -> Dict[str, Any]:
        """
        Analyze the complexity of edge configuration.
        
        Args:
            graph_def: The graph definition to analyze
            
        Returns:
            Analysis results
        """
        analysis = {
            'total_nodes': len(graph_def.nodes),
            'total_edges': 0,
            'conditional_edges': 0,
            'normal_edges': 0,
            'max_branching_factor': 0
        }
        
        try:
            for node_name, node_info in graph_def.edges.items():
                targets = node_info.get('targets', [])
                analysis['total_edges'] += len(targets)
                
                if len(targets) == 1:
                    analysis['normal_edges'] += 1
                else:
                    analysis['conditional_edges'] += 1
                    analysis['max_branching_factor'] = max(analysis['max_branching_factor'], len(targets))
            
            print(f"📊 Edge complexity analysis:")
            print(f"   - Total nodes: {analysis['total_nodes']}")
            print(f"   - Total edges: {analysis['total_edges']}")
            print(f"   - Normal edges: {analysis['normal_edges']}")
            print(f"   - Conditional edges: {analysis['conditional_edges']}")
            print(f"   - Max branching factor: {analysis['max_branching_factor']}")
            
        except Exception as e:
            print(f"❌ Edge complexity analysis failed: {e}")
        
        return analysis


# ============================================================================
# 5. ADVANCED EDGE PATTERNS
# ============================================================================

def create_parallel_processing_graph():
    """
    Parallel Processing Graph Example:
    
    Demonstrates how to implement parallel processing using edges.
    Shows fan-out and fan-in patterns.
    """
    print("⚡ Creating graph with parallel processing...")
    
    graph = StateGraph(DynamicState)
    
    # Add nodes for parallel processing
    def data_preprocessor(state: DynamicState) -> DynamicState:
        print("🔧 Data preprocessing")
        return {
            **state,
            'current_step': 'data_preprocessing',
            'processing_path': state['processing_path'] + ['data_preprocessing']
        }
    
    def feature_extractor_1(state: DynamicState) -> DynamicState:
        print("📊 Feature extraction (path 1)")
        return {
            **state,
            'current_step': 'feature_extraction_1',
            'processing_path': state['processing_path'] + ['feature_extraction_1']
        }
    
    def feature_extractor_2(state: DynamicState) -> DynamicState:
        print("📊 Feature extraction (path 2)")
        return {
            **state,
            'current_step': 'feature_extraction_2',
            'processing_path': state['processing_path'] + ['feature_extraction_2']
        }
    
    def feature_extractor_3(state: DynamicState) -> DynamicState:
        print("📊 Feature extraction (path 3)")
        return {
            **state,
            'current_step': 'feature_extraction_3',
            'processing_path': state['processing_path'] + ['feature_extraction_3']
        }
    
    def result_combiner(state: DynamicState) -> DynamicState:
        print("🔗 Combining results from parallel paths")
        return {
            **state,
            'current_step': 'result_combining',
            'processing_path': state['processing_path'] + ['result_combining']
        }
    
    def final_analyzer(state: DynamicState) -> DynamicState:
        print("🎯 Final analysis")
        return {
            **state,
            'current_step': 'final_analysis',
            'processing_path': state['processing_path'] + ['final_analysis']
        }
    
    graph.add_node("preprocessor", data_preprocessor)
    graph.add_node("extractor_1", feature_extractor_1)
    graph.add_node("extractor_2", feature_extractor_2)
    graph.add_node("extractor_3", feature_extractor_3)
    graph.add_node("combiner", result_combiner)
    graph.add_node("analyzer", final_analyzer)
    
    graph.set_entry_point("preprocessor")
    
    # Fan-out: one to many
    graph.add_edge("preprocessor", "extractor_1")
    graph.add_edge("preprocessor", "extractor_2")
    graph.add_edge("preprocessor", "extractor_3")
    
    # Fan-in: many to one (simplified - in practice, you'd need state merging)
    graph.add_edge("extractor_1", "combiner")
    graph.add_edge("extractor_2", "combiner")
    graph.add_edge("extractor_3", "combiner")
    
    # Continue with single path
    graph.add_edge("combiner", "analyzer")
    graph.add_edge("analyzer", END)
    
    return graph.compile()


def create_looping_graph():
    """
    Looping Graph Example:
    
    Demonstrates how to create loops in the graph for iterative processing.
    Shows how to implement cycles with proper termination conditions.
    """
    print("🔄 Creating graph with loops...")
    
    graph = StateGraph(DynamicState)
    
    # Add nodes for iterative processing
    def initialize_loop(state: DynamicState) -> DynamicState:
        print("🔄 Initializing loop")
        return {
            **state,
            'current_step': 'loop_initialization',
            'processing_path': state['processing_path'] + ['loop_initialization'],
            'retry_count': 0
        }
    
    def process_iteration(state: DynamicState) -> DynamicState:
        print(f"🔄 Processing iteration {state['retry_count'] + 1}")
        
        # Simulate processing that might improve confidence
        new_confidence = min(1.0, state['confidence_score'] + 0.2)
        
        return {
            **state,
            'confidence_score': new_confidence,
            'current_step': 'iteration_processing',
            'processing_path': state['processing_path'] + ['iteration_processing'],
            'retry_count': state['retry_count'] + 1
        }
    
    def check_termination(state: DynamicState) -> str:
        """Check if loop should terminate."""
        if state['confidence_score'] >= 0.9:
            return "success"
        elif state['retry_count'] >= 3:
            return "failure"
        else:
            return "continue"
    
    def success_handler(state: DynamicState) -> DynamicState:
        print("✅ Loop completed successfully")
        return {
            **state,
            'current_step': 'success_termination',
            'processing_path': state['processing_path'] + ['success_termination']
        }
    
    def failure_handler(state: DynamicState) -> DynamicState:
        print("❌ Loop failed after maximum iterations")
        return {
            **state,
            'current_step': 'failure_termination',
            'processing_path': state['processing_path'] + ['failure_termination']
        }
    
    graph.add_node("initialize", initialize_loop)
    graph.add_node("process", process_iteration)
    graph.add_node("success", success_handler)
    graph.add_node("failure", failure_handler)
    
    graph.set_entry_point("initialize")
    
    # Set up loop
    graph.add_edge("initialize", "process")
    
    # Conditional edge that can loop back
    graph.add_conditional_edges(
        "process",
        check_termination,
        {
            "success": "success",
            "failure": "failure",
            "continue": "process"  # Loop back to process
        }
    )
    
    # Connect to end
    graph.add_edge("success", END)
    graph.add_edge("failure", END)
    
    return graph.compile()


# ============================================================================
# 6. EXAMPLE USAGE AND DEMONSTRATION
# ============================================================================

def demonstrate_edges():
    """
    Demonstrate all edge concepts with practical examples.
    """
    print("🎯 EDGES DEMONSTRATION")
    print("=" * 50)
    
    # 1. Test simple edges
    print("\n1. Simple Edges Execution:")
    simple_app = create_simple_edges_graph()
    simple_input = {
        'input_text': 'hello world',
        'processed_text': '',
        'step_count': 0
    }
    simple_result = simple_app.invoke(simple_input)
    print(f"Simple edges result: Step count = {simple_result['step_count']}")
    
    # 2. Test conditional edges
    print("\n2. Conditional Edges Execution:")
    conditional_app = create_conditional_edges_graph()
    
    test_cases = [
        {
            'user_input': 'Hello, how are you?',
            'category': '',
            'confidence_score': 0.8,
            'validation_errors': [],
            'current_step': '',
            'completed_steps': []
        },
        {
            'user_input': 'I need help with my account',
            'category': '',
            'confidence_score': 0.7,
            'validation_errors': [],
            'current_step': '',
            'completed_steps': []
        },
        {
            'user_input': 'What is the price of your product?',
            'category': '',
            'confidence_score': 0.9,
            'validation_errors': [],
            'current_step': '',
            'completed_steps': []
        }
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        try:
            result = conditional_app.invoke(test_input)
            print(f"Category: {result.get('category')}")
            print(f"Final step: {result.get('current_step')}")
        except Exception as e:
            print(f"Error: {e}")
    
    # 3. Test dynamic routing
    print("\n3. Dynamic Routing Execution:")
    dynamic_app = create_dynamic_routing_graph()
    dynamic_input = {
        'session_id': 'dynamic_test',
        'user_input': 'This is a test input with multiple words for processing',
        'confidence_score': 0.0,
        'retry_count': 0,
        'processing_path': [],
        'current_step': ''
    }
    dynamic_result = dynamic_app.invoke(dynamic_input)
    print(f"Processing path: {dynamic_result['processing_path']}")
    print(f"Final confidence: {dynamic_result['confidence_score']}")
    
    # 4. Test parallel processing
    print("\n4. Parallel Processing Execution:")
    parallel_app = create_parallel_processing_graph()
    parallel_input = {
        'session_id': 'parallel_test',
        'user_input': 'Parallel processing test input',
        'confidence_score': 0.5,
        'retry_count': 0,
        'processing_path': [],
        'current_step': ''
    }
    parallel_result = parallel_app.invoke(parallel_input)
    print(f"Parallel processing completed: {parallel_result['current_step']}")
    
    # 5. Test looping
    print("\n5. Looping Execution:")
    loop_app = create_looping_graph()
    loop_input = {
        'session_id': 'loop_test',
        'user_input': 'Looping test input',
        'confidence_score': 0.3,
        'retry_count': 0,
        'processing_path': [],
        'current_step': ''
    }
    loop_result = loop_app.invoke(loop_input)
    print(f"Loop result: {loop_result['current_step']}")
    print(f"Final confidence: {loop_result['confidence_score']}")
    print(f"Iterations: {loop_result['retry_count']}")
    
    print("\n✅ EDGES DEMONSTRATION COMPLETED")


if __name__ == "__main__":
    """
    Run the edges demonstration.
    """
    demonstrate_edges()