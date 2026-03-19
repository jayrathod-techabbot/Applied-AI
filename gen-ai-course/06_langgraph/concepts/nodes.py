#!/usr/bin/env python3
"""
LangGraph Nodes - Core Concept

This file demonstrates the fundamental concept of Nodes in LangGraph.
Nodes are the computational units that process and transform state as it
flows through the graph. Every node receives the current state and can modify it.

Key Concepts Covered:
- Node definition and structure
- Synchronous vs asynchronous nodes
- Node composition and chaining
- Error handling in nodes
- Node performance optimization
- Node testing and validation
"""

from typing import TypedDict, List, Optional, Dict, Any, Callable, Awaitable
from datetime import datetime
import asyncio
import time
import functools
from typing import get_type_hints


# ============================================================================
# 1. BASIC NODE DEFINITION
# ============================================================================

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


# ============================================================================
# 2. NODE TYPES AND PATTERNS
# ============================================================================

class AdvancedState(TypedDict):
    """Advanced state for complex node examples."""
    session_id: str
    user_input: str
    processed_data: Dict[str, Any]
    validation_errors: List[str]
    current_step: str
    completed_steps: List[str]
    confidence_score: Optional[float]


def validation_node(state: AdvancedState) -> AdvancedState:
    """
    Validation Node Example:
    
    This node demonstrates input validation and error handling.
    It checks for common issues and adds validation errors to state.
    """
    print(f"✅ Validating input: '{state['user_input'][:50]}...'")
    
    validation_errors = []
    
    # Check for empty input
    if not state['user_input'] or not state['user_input'].strip():
        validation_errors.append("Input text cannot be empty")
    
    # Check input length
    if len(state['user_input']) > 10000:
        validation_errors.append("Input text too long (max 10000 characters)")
    
    # Check for sensitive information
    sensitive_keywords = ["password", "credit card", "ssn"]
    text_lower = state['user_input'].lower()
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
    print(f"⚙️  Processing input with {len(state['user_input'])} characters")
    
    # Simulate processing time
    time.sleep(0.1)
    
    # Simple text analysis
    word_count = len(state['user_input'].split())
    char_count = len(state['user_input'])
    
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
    print(f"🌐 Making async request for: '{state['user_input'][:30]}...'")
    
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


def conditional_node(state: AdvancedState) -> AdvancedState:
    """
    Conditional Node Example:
    
    Node that makes decisions based on state and routes accordingly.
    This demonstrates how nodes can implement business logic.
    """
    print(f"🔀 Conditional node execution")
    
    if state['confidence_score'] and state['confidence_score'] > 0.8:
        # High confidence path
        return {
            **state,
            'next_actions': ['finalize_output'],
            'current_step': 'high_confidence_processing'
        }
    else:
        # Low confidence path - need more processing
        return {
            **state,
            'next_actions': ['additional_analysis', 'validation'],
            'current_step': 'low_confidence_processing'
        }


# ============================================================================
# 3. NODE COMPOSITION AND CHAINING
# ============================================================================

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


def create_node_chain():
    """
    Create a chain of nodes for processing pipeline.
    
    Returns:
        Composed node function that executes the entire chain
    """
    # Create individual nodes
    validation_chain = compose_nodes(
        validation_node,
        lambda s: {**s, 'current_step': 'validation_complete'}
    )
    
    processing_chain = compose_nodes(
        processing_node,
        lambda s: {**s, 'current_step': 'processing_complete'}
    )
    
    # Create full pipeline
    full_pipeline = compose_nodes(
        validation_chain,
        processing_chain,
        lambda s: {**s, 'current_step': 'pipeline_complete'}
    )
    
    return full_pipeline


# ============================================================================
# 4. ERROR HANDLING IN NODES
# ============================================================================

def robust_node_example(state: AdvancedState) -> AdvancedState:
    """
    Robust Node Example:
    
    Demonstrates comprehensive error handling within nodes.
    Always return valid state, even when errors occur.
    """
    print(f"🛡️  Robust node execution")
    
    try:
        # Validate inputs
        if not state['user_input'] or not state['user_input'].strip():
            raise ValueError("Input text cannot be empty")
        
        # Perform main processing
        result = process_data(state['user_input'])
        
        # Update state
        return {
            **state,
            'processed_data': result,
            'validation_errors': [],
            'current_step': 'robust_processing'
        }
        
    except ValueError as e:
        # Handle specific validation errors
        return {
            **state,
            'validation_errors': state['validation_errors'] + [str(e)],
            'current_step': 'error_handling'
        }
        
    except Exception as e:
        # Handle unexpected errors
        return {
            **state,
            'validation_errors': state['validation_errors'] + [f"Unexpected error: {str(e)}"],
            'current_step': 'error_handling'
        }


def process_data(input_text: str) -> Dict[str, Any]:
    """
    Simulate data processing that might fail.
    
    Args:
        input_text: Text to process
        
    Returns:
        Processed data dictionary
    """
    if len(input_text) < 3:
        raise ValueError("Input too short for processing")
    
    return {
        'processed_text': input_text.upper(),
        'length': len(input_text),
        'timestamp': datetime.now().isoformat()
    }


class NodeErrorHandler:
    """
    Node Error Handler Class:
    
    Provides utilities for handling errors in node execution.
    """
    
    @staticmethod
    def retry_with_backoff(node_func: Callable, max_retries: int = 3, backoff_factor: float = 2.0) -> Callable:
        """
        Retry node execution with exponential backoff.
        
        Args:
            node_func: The node function to wrap
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for delay between retries
            
        Returns:
            Wrapped node function with retry logic
        """
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            delay = 1.0
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return node_func(state)
                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:  # Last attempt
                        raise e
                    
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
            
            raise last_error
        
        return wrapper
    
    @staticmethod
    def graceful_degradation(node_func: Callable, fallback_func: Callable) -> Callable:
        """
        Execute fallback if main function fails.
        
        Args:
            node_func: Primary node function
            fallback_func: Fallback function to use on failure
            
        Returns:
            Wrapped node function with fallback logic
        """
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return node_func(state)
            except Exception as e:
                print(f"Main function failed: {e}. Using fallback.")
                return fallback_func(state)
        
        return wrapper
    
    @staticmethod
    def circuit_breaker(node_func: Callable, failure_threshold: int = 5, recovery_timeout: int = 60) -> Callable:
        """
        Implement circuit breaker pattern for node execution.
        
        Args:
            node_func: The node function to wrap
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            
        Returns:
            Wrapped node function with circuit breaker logic
        """
        failures = 0
        last_failure_time = 0
        
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal failures, last_failure_time
            
            current_time = time.time()
            
            # Check if circuit should be open
            if failures >= failure_threshold:
                if current_time - last_failure_time < recovery_timeout:
                    raise Exception("Circuit breaker is open - service unavailable")
                else:
                    # Reset circuit
                    failures = 0
            
            try:
                result = node_func(state)
                failures = 0  # Reset on success
                return result
            except Exception as e:
                failures += 1
                last_failure_time = current_time
                raise e
        
        return wrapper


# ============================================================================
# 5. NODE PERFORMANCE OPTIMIZATION
# ============================================================================

class NodePerformance:
    """
    Node Performance Optimization:
    
    Performance optimization utilities for nodes.
    """
    
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def cached_computation(input_data: str) -> Dict[str, Any]:
        """
        Cache expensive computations.
        
        Args:
            input_data: Input data to compute on
            
        Returns:
            Computed result dictionary
        """
        # Simulate expensive computation
        time.sleep(0.1)
        return {
            'result': f"Computed: {input_data}",
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def timed_node(node_func: Callable) -> Callable:
        """
        Decorator to measure node execution time.
        
        Args:
            node_func: The node function to time
            
        Returns:
            Wrapped node function with timing
        """
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            start_time = time.time()
            result = node_func(state)
            execution_time = time.time() - start_time
            
            # Add timing info to debug
            if 'debug_info' not in result:
                result['debug_info'] = {}
            result['debug_info']['execution_time'] = execution_time
            
            return result
        
        return wrapper
    
    @staticmethod
    def memory_optimized_node(node_func: Callable) -> Callable:
        """
        Decorator to optimize memory usage in nodes.
        
        Args:
            node_func: The node function to optimize
            
        Returns:
            Wrapped node function with memory optimization
        """
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            # Clear debug info to save memory
            if 'debug_info' in state:
                state = {k: v for k, v in state.items() if k != 'debug_info'}
            
            result = node_func(state)
            
            # Limit state size
            import sys
            state_size = sys.getsizeof(str(result))
            if state_size > 1024 * 1024:  # 1MB limit
                print(f"⚠️  State size {state_size} bytes exceeds limit, cleaning up")
                result = {k: v for k, v in result.items() 
                         if k not in ['debug_info', 'intermediate_results']}
            
            return result
        
        return wrapper


@NodePerformance.timed_node
@NodePerformance.memory_optimized_node
def optimized_node(state: AdvancedState) -> AdvancedState:
    """
    Optimized Node Example:
    
    Node with caching, timing, and memory optimization.
    """
    print(f"⚡ Optimized node execution")
    
    # Use cached computation for repeated inputs
    result = NodePerformance.cached_computation(state['user_input'])
    
    return {
        **state,
        'processed_data': {
            **state['processed_data'],
            'optimized_result': result
        },
        'current_step': 'optimized_processing'
    }


# ============================================================================
# 6. NODE TESTING AND VALIDATION
# ============================================================================

class NodeTester:
    """
    Node Testing Utilities:
    
    Provides methods for testing and validating node functions.
    """
    
    @staticmethod
    def test_node_signature(node_func: Callable, state_class: type) -> bool:
        """
        Test that node function has correct signature.
        
        Args:
            node_func: The node function to test
            state_class: Expected state class
            
        Returns:
            True if signature is correct, False otherwise
        """
        import inspect
        
        sig = inspect.signature(node_func)
        params = list(sig.parameters.keys())
        return_value = sig.return_annotation
        
        # Check parameter count and name
        if len(params) != 1:
            print(f"❌ Node should have exactly 1 parameter, got {len(params)}")
            return False
        
        if params[0] != 'state':
            print(f"❌ Parameter should be named 'state', got '{params[0]}'")
            return False
        
        # Check return type annotation
        expected_type = state_class
        if return_value != expected_type:
            print(f"❌ Return type should be {expected_type}, got {return_value}")
            return False
        
        print(f"✅ Node signature validation passed")
        return True
    
    @staticmethod
    def test_node_execution(node_func: Callable, test_state: Dict[str, Any]) -> bool:
        """
        Test node execution with sample state.
        
        Args:
            node_func: The node function to test
            test_state: Sample state to test with
            
        Returns:
            True if execution is successful, False otherwise
        """
        try:
            result = node_func(test_state)
            
            # Check that result is a dictionary
            if not isinstance(result, dict):
                print(f"❌ Node should return a dictionary, got {type(result)}")
                return False
            
            # Check that result contains expected keys
            expected_keys = set(test_state.keys())
            result_keys = set(result.keys())
            
            if not expected_keys.issubset(result_keys):
                missing_keys = expected_keys - result_keys
                print(f"❌ Result missing keys: {missing_keys}")
                return False
            
            print(f"✅ Node execution test passed")
            return True
            
        except Exception as e:
            print(f"❌ Node execution failed: {e}")
            return False
    
    @staticmethod
    def test_node_error_handling(node_func: Callable, error_state: Dict[str, Any]) -> bool:
        """
        Test node error handling with problematic state.
        
        Args:
            node_func: The node function to test
            error_state: State that should trigger error handling
            
        Returns:
            True if error handling works correctly, False otherwise
        """
        try:
            result = node_func(error_state)
            
            # Check that result is still a valid state
            if not isinstance(result, dict):
                print(f"❌ Error handling should return a dictionary, got {type(result)}")
                return False
            
            # Check that errors are properly recorded
            if 'validation_errors' in result and len(result['validation_errors']) > 0:
                print(f"✅ Error handling test passed - errors recorded: {result['validation_errors']}")
                return True
            else:
                print(f"⚠️  Error handling test - no errors recorded in result")
                return True  # Still valid, just no errors
            
        except Exception as e:
            print(f"❌ Error handling failed: {e}")
            return False


# ============================================================================
# 7. EXAMPLE USAGE AND DEMONSTRATION
# ============================================================================

def demonstrate_nodes():
    """
    Demonstrate all node concepts with practical examples.
    """
    print("🎯 NODES DEMONSTRATION")
    print("=" * 50)
    
    # 1. Test basic node
    print("\n1. Basic Node Execution:")
    basic_state = {
        'input_text': 'hello world',
        'processed_text': '',
        'step_count': 0
    }
    basic_result = basic_node_example(basic_state)
    print(f"Basic node result: {basic_result}")
    
    # 2. Test validation node
    print("\n2. Validation Node Execution:")
    validation_state = {
        'session_id': 'test1',
        'user_input': 'This is a valid input',
        'processed_data': {},
        'validation_errors': [],
        'current_step': '',
        'completed_steps': []
    }
    validation_result = validation_node(validation_state)
    print(f"Validation result: {validation_result['validation_errors']}")
    
    # 3. Test async node
    print("\n3. Async Node Execution:")
    async def run_async_example():
        async_state = {
            'session_id': 'async_test',
            'user_input': 'Async processing test',
            'processed_data': {},
            'validation_errors': [],
            'current_step': '',
            'completed_steps': []
        }
        async_result = await async_node_example(async_state)
        print(f"Async node completed: {async_result['current_step']}")
        return async_result
    
    asyncio.run(run_async_example())
    
    # 4. Test node composition
    print("\n4. Node Composition:")
    composed_node = create_node_chain()
    composition_state = {
        'session_id': 'composition_test',
        'user_input': 'Composition test input',
        'processed_data': {},
        'validation_errors': [],
        'current_step': '',
        'completed_steps': []
    }
    composition_result = composed_node(composition_state)
    print(f"Composition result: {composition_result['current_step']}")
    
    # 5. Test error handling
    print("\n5. Error Handling Node:")
    error_state = {
        'session_id': 'error_test',
        'user_input': '',  # Empty input to trigger error
        'processed_data': {},
        'validation_errors': [],
        'current_step': '',
        'completed_steps': []
    }
    error_result = robust_node_example(error_state)
    print(f"Error handling result: {error_result['validation_errors']}")
    
    # 6. Test performance optimization
    print("\n6. Performance Optimized Node:")
    perf_state = {
        'session_id': 'perf_test',
        'user_input': 'Performance test input',
        'processed_data': {},
        'validation_errors': [],
        'current_step': '',
        'completed_steps': []
    }
    perf_result = optimized_node(perf_state)
    print(f"Performance result: {perf_result.get('debug_info', {}).get('execution_time', 'No timing info')}")
    
    # 7. Test node validation
    print("\n7. Node Testing:")
    NodeTester.test_node_signature(basic_node_example, BasicState)
    NodeTester.test_node_execution(basic_node_example, basic_state)
    NodeTester.test_node_error_handling(robust_node_example, error_state)
    
    print("\n✅ NODES DEMONSTRATION COMPLETED")


if __name__ == "__main__":
    """
    Run the nodes demonstration.
    """
    demonstrate_nodes()