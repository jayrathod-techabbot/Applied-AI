# Concepts: Building Blocks of LangGraph

## State Management Deep Dive

### Advanced State Schema Design

State schemas define the structure and types of data flowing through your graph. Effective schema design is crucial for maintainable applications.

#### Best Practices for State Design

```python
from typing import TypedDict, List, Optional, Union
from datetime import datetime

class AdvancedState(TypedDict):
    """Comprehensive state schema for complex applications."""
    # Core identification
    session_id: str
    user_id: Optional[str]
    timestamp: datetime
    
    # Input and processing
    input_text: str
    processed_data: dict
    validation_errors: List[str]
    
    # Workflow tracking
    current_step: str
    completed_steps: List[str]
    next_actions: List[str]
    
    # Results and outputs
    intermediate_results: List[dict]
    final_output: Optional[str]
    confidence_score: Optional[float]
    
    # Metadata and context
    context: dict
    metadata: dict
    debug_info: dict
```

#### State Validation Patterns

```python
from typing import get_type_hints
import jsonschema

def validate_state(state: dict, schema: dict) -> bool:
    """Validate state against JSON schema."""
    try:
        jsonschema.validate(state, schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"State validation error: {e}")
        return False

def create_state_validator(state_class: type) -> callable:
    """Create a validator function for a TypedDict class."""
    type_hints = get_type_hints(state_class)
    
    def validator(state: dict) -> bool:
        for key, expected_type in type_hints.items():
            if key not in state:
                print(f"Missing required key: {key}")
                return False
            
            value = state[key]
            if not isinstance(value, expected_type):
                print(f"Type mismatch for {key}: expected {expected_type}, got {type(value)}")
                return False
        return True
    
    return validator

# Usage
state_validator = create_state_validator(AdvancedState)

def safe_node(state: AdvancedState) -> AdvancedState:
    """Node with state validation."""
    if not state_validator(state):
        raise ValueError("Invalid state structure")
    
    # Node logic here
    return state
```

### State Persistence Strategies

```python
import json
import pickle
from typing import Any

class StatePersistence:
    """Handle state saving and loading."""
    
    @staticmethod
    def save_state(state: dict, file_path: str, format: str = 'json') -> None:
        """Save state to file."""
        if format == 'json':
            with open(file_path, 'w') as f:
                json.dump(state, f, default=str, indent=2)
        elif format == 'pickle':
            with open(file_path, 'wb') as f:
                pickle.dump(state, f)
    
    @staticmethod
    def load_state(file_path: str, format: str = 'json') -> dict:
        """Load state from file."""
        if format == 'json':
            with open(file_path, 'r') as f:
                return json.load(f)
        elif format == 'pickle':
            with open(file_path, 'rb') as f:
                return pickle.load(f)
    
    @staticmethod
    def serialize_state(state: dict) -> str:
        """Serialize state to string for database storage."""
        return json.dumps(state, default=str)

# Usage in nodes
def save_checkpoint(state: AdvancedState) -> AdvancedState:
    """Save state checkpoint."""
    StatePersistence.save_state(state, f"checkpoint_{state['session_id']}.json")
    return state
```

### Memory Optimization Techniques

```python
class StateOptimizer:
    """Optimize state for memory efficiency."""
    
    @staticmethod
    def compress_state(state: dict, max_size_mb: int = 10) -> dict:
        """Compress state if it exceeds size limit."""
        import sys
        
        # Calculate state size
        state_size = sys.getsizeof(str(state))
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if state_size > max_size_bytes:
            # Remove debug info and metadata
            compressed = {
                k: v for k, v in state.items() 
                if k not in ['debug_info', 'metadata']
            }
            return compressed
        
        return state
    
    @staticmethod
    def cleanup_state(state: dict, cleanup_keys: List[str]) -> dict:
        """Remove specified keys from state."""
        return {k: v for k, v in state.items() if k not in cleanup_keys}

# Usage in graph
def optimize_memory(state: AdvancedState) -> AdvancedState:
    """Optimize state memory usage."""
    optimized = StateOptimizer.compress_state(state)
    return StateOptimizer.cleanup_state(optimized, ['debug_info'])
```

## Node Creation and Execution

### Different Types of Nodes

#### Synchronous Nodes

```python
def sync_node(state: AdvancedState) -> AdvancedState:
    """Standard synchronous node."""
    # Process data synchronously
    result = expensive_computation(state['input_text'])
    
    return {
        **state,
        'processed_data': result,
        'current_step': 'sync_processing',
        'completed_steps': state['completed_steps'] + ['sync_processing']
    }
```

#### Asynchronous Nodes

```python
import asyncio
from typing import Awaitable

async def async_node(state: AdvancedState) -> AdvancedState:
    """Asynchronous node for I/O operations."""
    # Perform async operations
    result = await fetch_external_data(state['input_text'])
    
    return {
        **state,
        'processed_data': result,
        'current_step': 'async_processing',
        'completed_steps': state['completed_steps'] + ['async_processing']
    }
```

#### Conditional Nodes

```python
def conditional_node(state: AdvancedState) -> AdvancedState:
    """Node that makes decisions based on state."""
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
```

### Node Composition and Chaining

```python
def compose_nodes(*nodes):
    """Compose multiple nodes into a single node."""
    def composed_node(state: AdvancedState) -> AdvancedState:
        current_state = state
        for node in nodes:
            current_state = node(current_state)
        return current_state
    return composed_node

# Example usage
validation_chain = compose_nodes(
    validate_input_node,
    normalize_input_node,
    sanitize_data_node
)

processing_chain = compose_nodes(
    extract_features_node,
    analyze_data_node,
    generate_insights_node
)
```

### Error Handling in Nodes

```python
from typing import Optional

def robust_node(state: AdvancedState) -> AdvancedState:
    """Node with comprehensive error handling."""
    try:
        # Validate inputs
        if not state['input_text'] or not state['input_text'].strip():
            raise ValueError("Input text cannot be empty")
        
        # Perform main processing
        result = process_data(state['input_text'])
        
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
```

### Performance Optimization for Nodes

```python
import time
from functools import lru_cache

class NodePerformance:
    """Performance optimization utilities for nodes."""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def cached_computation(input_data: str) -> dict:
        """Cache expensive computations."""
        # Expensive computation here
        return expensive_operation(input_data)
    
    @staticmethod
    def timed_node(node_func):
        """Decorator to measure node execution time."""
        def wrapper(state: AdvancedState) -> AdvancedState:
            start_time = time.time()
            result = node_func(state)
            execution_time = time.time() - start_time
            
            # Add timing info to debug
            result['debug_info']['execution_time'] = execution_time
            return result
        return wrapper

@NodePerformance.timed_node
def optimized_node(state: AdvancedState) -> AdvancedState:
    """Optimized node with caching and timing."""
    # Use cached computation for repeated inputs
    result = NodePerformance.cached_computation(state['input_text'])
    
    return {
        **state,
        'processed_data': result,
        'current_step': 'optimized_processing'
    }
```

## Edge Types and Routing

### Normal vs Conditional Edges

```python
from langgraph.graph import StateGraph, END

def create_routing_graph():
    """Create a graph with different edge types."""
    graph = StateGraph(AdvancedState)
    
    # Add nodes
    graph.add_node("validate", validate_node)
    graph.add_node("process", process_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("finalize", finalize_node)
    graph.add_node("error_handler", error_handler_node)
    graph.add_node("retry_handler", retry_handler_node)
    
    # Set entry point
    graph.set_entry_point("validate")
    
    # Normal edges (always execute)
    graph.add_edge("validate", "process")
    graph.add_edge("process", "analyze")
    graph.add_edge("finalize", END)
    
    # Conditional edges (based on state)
    def route_after_validation(state: AdvancedState) -> str:
        if state['validation_errors']:
            return "error_handler"
        return "process"
    
    def route_after_processing(state: AdvancedState) -> str:
        if state['confidence_score'] and state['confidence_score'] < 0.5:
            return "retry_handler"
        return "analyze"
    
    def route_after_analysis(state: AdvancedState) -> str:
        if state['intermediate_results'] and len(state['intermediate_results']) > 0:
            return "finalize"
        return "error_handler"
    
    # Add conditional edges
    graph.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "error_handler": "error_handler",
            "process": "process"
        }
    )
    
    graph.add_conditional_edges(
        "process",
        route_after_processing,
        {
            "retry_handler": "retry_handler",
            "analyze": "analyze"
        }
    )
    
    graph.add_conditional_edges(
        "analyze",
        route_after_analysis,
        {
            "finalize": "finalize",
            "error_handler": "error_handler"
        }
    )
    
    # Error handling edges
    graph.add_edge("error_handler", END)
    graph.add_edge("retry_handler", "process")
    
    return graph.compile()
```

### Dynamic Routing Strategies

```python
def create_dynamic_router():
    """Create a router that adapts based on runtime conditions."""
    
    def dynamic_router(state: AdvancedState) -> str:
        """Route based on multiple dynamic conditions."""
        current_step = state.get('current_step', '')
        errors = state.get('validation_errors', [])
        confidence = state.get('confidence_score', 0.0)
        retry_count = len(state.get('completed_steps', []))
        
        # Priority routing logic
        if errors:
            return "error_path"
        elif confidence > 0.9:
            return "fast_path"
        elif retry_count > 3:
            return "fallback_path"
        elif current_step == "processing":
            return "analysis_path"
        else:
            return "default_path"
    
    # Create specialized paths
    def fast_path_node(state: AdvancedState) -> AdvancedState:
        return {**state, 'current_step': 'fast_processing'}
    
    def error_path_node(state: AdvancedState) -> AdvancedState:
        return {**state, 'current_step': 'error_resolution'}
    
    def fallback_path_node(state: AdvancedState) -> AdvancedState:
        return {**state, 'current_step': 'fallback_processing'}
    
    # Build dynamic graph
    graph = StateGraph(AdvancedState)
    graph.add_node("router", lambda s: s)  # Pass-through router
    graph.add_node("fast_path", fast_path_node)
    graph.add_node("error_path", error_path_node)
    graph.add_node("fallback_path", fallback_path_node)
    graph.add_node("default_path", lambda s: {**s, 'current_step': 'default_processing'})
    graph.add_node("end", lambda s: s)
    
    graph.set_entry_point("router")
    graph.add_conditional_edges("router", dynamic_router, {
        "fast_path": "fast_path",
        "error_path": "error_path",
        "fallback_path": "fallback_path",
        "default_path": "default_path"
    })
    graph.add_edge("fast_path", "end")
    graph.add_edge("error_path", "end")
    graph.add_edge("fallback_path", "end")
    graph.add_edge("default_path", "end")
    graph.add_edge("end", END)
    
    return graph.compile()
```

### Complex Routing Patterns

```python
def create_complex_routing_graph():
    """Create a graph with complex multi-step routing."""
    graph = StateGraph(AdvancedState)
    
    # Add all nodes
    nodes = [
        "input_validation", "data_preprocessing", "feature_extraction",
        "model_inference", "result_validation", "output_formatting",
        "quality_check", "retry_logic", "escalation_handler", "final_output"
    ]
    
    for node_name in nodes:
        graph.add_node(node_name, create_node_function(node_name))
    
    graph.set_entry_point("input_validation")
    
    # Complex routing logic
    def route_validation(state: AdvancedState) -> str:
        if state['validation_errors']:
            return "escalation_handler"
        return "data_preprocessing"
    
    def route_inference(state: AdvancedState) -> str:
        confidence = state.get('confidence_score', 0.0)
        if confidence > 0.8:
            return "result_validation"
        elif confidence > 0.5:
            return "retry_logic"
        else:
            return "escalation_handler"
    
    def route_quality_check(state: AdvancedState) -> str:
        quality_score = calculate_quality_score(state)
        if quality_score > 0.9:
            return "final_output"
        elif quality_score > 0.7:
            return "retry_logic"
        else:
            return "escalation_handler"
    
    # Set up complex routing
    graph.add_conditional_edges("input_validation", route_validation, {
        "escalation_handler": "escalation_handler",
        "data_preprocessing": "data_preprocessing"
    })
    
    graph.add_edge("data_preprocessing", "feature_extraction")
    graph.add_edge("feature_extraction", "model_inference")
    graph.add_conditional_edges("model_inference", route_inference, {
        "result_validation": "result_validation",
        "retry_logic": "retry_logic",
        "escalation_handler": "escalation_handler"
    })
    
    graph.add_edge("result_validation", "output_formatting")
    graph.add_edge("output_formatting", "quality_check")
    graph.add_conditional_edges("quality_check", route_quality_check, {
        "final_output": "final_output",
        "retry_logic": "retry_logic",
        "escalation_handler": "escalation_handler"
    })
    
    # Retry and escalation paths
    graph.add_edge("retry_logic", "data_preprocessing")
    graph.add_edge("escalation_handler", "final_output")
    graph.add_edge("final_output", END)
    
    return graph.compile()
```

## Graph Compilation and Execution

### Compilation Process and Validation

```python
def compile_with_validation(graph_def, state_schema):
    """Compile graph with comprehensive validation."""
    try:
        # Validate state schema
        if not is_valid_state_schema(state_schema):
            raise ValueError("Invalid state schema")
        
        # Validate node functions
        for node_name, node_func in graph_def.nodes.items():
            if not is_valid_node_function(node_func, state_schema):
                raise ValueError(f"Invalid node function: {node_name}")
        
        # Validate edges
        if not is_valid_edge_configuration(graph_def):
            raise ValueError("Invalid edge configuration")
        
        # Compile graph
        compiled_graph = graph_def.compile()
        
        # Validate compiled graph
        if not is_valid_compiled_graph(compiled_graph):
            raise ValueError("Invalid compiled graph")
        
        return compiled_graph
        
    except Exception as e:
        print(f"Compilation error: {e}")
        return None

def is_valid_state_schema(schema):
    """Validate state schema structure."""
    required_keys = ['session_id', 'input_text', 'current_step']
    return all(key in schema for key in required_keys)

def is_valid_node_function(node_func, state_schema):
    """Validate node function signature and behavior."""
    # Check if function accepts and returns state
    import inspect
    sig = inspect.signature(node_func)
    params = list(sig.parameters.keys())
    return_value = sig.return_annotation
    
    return (
        len(params) == 1 and  # Single parameter (state)
        params[0] == 'state' and  # Parameter named 'state'
        return_value == state_schema  # Returns state schema type
    )
```

### Execution Modes and Streaming

```python
def execute_with_streaming(app, input_state, stream_mode='values'):
    """Execute graph with different streaming modes."""
    try:
        if stream_mode == 'values':
            # Stream state updates
            for chunk in app.stream(input_state, stream_mode='values'):
                print(f"State update: {chunk}")
                yield chunk
                
        elif stream_mode == 'updates':
            # Stream node updates
            for chunk in app.stream(input_state, stream_mode='updates'):
                print(f"Node update: {chunk}")
                yield chunk
                
        elif stream_mode == 'debug':
            # Stream debug information
            for chunk in app.stream(input_state, stream_mode='debug'):
                print(f"Debug info: {chunk}")
                yield chunk
                
        elif stream_mode == 'messages':
            # Stream messages (for chat applications)
            for chunk in app.stream(input_state, stream_mode='messages'):
                print(f"Message: {chunk}")
                yield chunk
                
    except Exception as e:
        print(f"Execution error: {e}")
        yield {"error": str(e)}

def execute_with_callbacks(app, input_state, callbacks=None):
    """Execute graph with callback support."""
    if callbacks is None:
        callbacks = {}
    
    try:
        # Set up callbacks
        config = {"callbacks": callbacks}
        
        # Execute with callbacks
        result = app.invoke(input_state, config=config)
        return result
        
    except Exception as e:
        if 'error_callback' in callbacks:
            callbacks['error_callback'](e)
        raise
```

### Performance Considerations

```python
import time
import psutil
from contextlib import contextmanager

class PerformanceMonitor:
    """Monitor graph execution performance."""
    
    def __init__(self):
        self.metrics = {}
    
    @contextmanager
    def monitor_execution(self, operation_name: str):
        """Context manager for monitoring operation performance."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            self.metrics[operation_name] = {
                'execution_time': execution_time,
                'memory_delta': memory_delta,
                'peak_memory': end_memory
            }
    
    def get_performance_report(self) -> dict:
        """Get performance metrics report."""
        total_time = sum(m['execution_time'] for m in self.metrics.values())
        total_memory = sum(m['memory_delta'] for m in self.metrics.values())
        
        return {
            'total_execution_time': total_time,
            'total_memory_usage': total_memory,
            'operation_metrics': self.metrics,
            'recommendations': self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> list:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        for operation, metrics in self.metrics.items():
            if metrics['execution_time'] > 1.0:  # > 1 second
                recommendations.append(f"Optimize {operation}: took {metrics['execution_time']:.2f}s")
            
            if metrics['memory_delta'] > 100:  # > 100MB
                recommendations.append(f"Reduce memory usage in {operation}: +{metrics['memory_delta']:.2f}MB")
        
        return recommendations

# Usage example
def execute_with_monitoring(app, input_state):
    """Execute graph with performance monitoring."""
    monitor = PerformanceMonitor()
    
    with monitor.monitor_execution('graph_execution'):
        result = app.invoke(input_state)
    
    report = monitor.get_performance_report()
    print("Performance Report:", report)
    
    return result, report
```

### Debugging Compiled Graphs

```python
def debug_graph_execution(app, input_state, debug_level='verbose'):
    """Debug graph execution with detailed information."""
    
    def debug_node(state, node_name):
        """Debug wrapper for nodes."""
        print(f"\n🔍 Executing node: {node_name}")
        print(f"Input state keys: {list(state.keys())}")
        print(f"Current step: {state.get('current_step', 'unknown')}")
        
        # Execute node
        result = state  # In real implementation, this would call the actual node
        
        print(f"Output state keys: {list(result.keys())}")
        print(f"Updated step: {result.get('current_step', 'unknown')}")
        
        return result
    
    if debug_level == 'verbose':
        # Enable verbose debugging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        # Wrap nodes with debug functionality
        for node_name in app.get_graph().nodes:
            original_node = app.get_graph().nodes[node_name]
            app.get_graph().nodes[node_name] = lambda s, name=node_name: debug_node(original_node(s), name)
    
    # Execute with debugging
    result = app.invoke(input_state)
    
    # Print execution trace
    print("\n📋 Execution Trace:")
    for i, step in enumerate(app.get_execution_trace()):
        print(f"{i+1}. {step['node_name']} -> {step['state_change']}")
    
    return result
```

## Error Handling and Validation

### State Validation Patterns

```python
class StateValidator:
    """Comprehensive state validation utilities."""
    
    @staticmethod
    def validate_required_fields(state: dict, required_fields: list) -> list:
        """Validate that all required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in state or state[field] is None:
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_field_types(state: dict, type_schema: dict) -> list:
        """Validate field types according to schema."""
        errors = []
        for field, expected_type in type_schema.items():
            if field in state:
                actual_type = type(state[field])
                if not issubclass(actual_type, expected_type):
                    errors.append(f"Field '{field}': expected {expected_type}, got {actual_type}")
        return errors
    
    @staticmethod
    def validate_business_rules(state: dict) -> list:
        """Validate business-specific rules."""
        errors = []
        
        # Example business rules
        if 'confidence_score' in state:
            confidence = state['confidence_score']
            if confidence is not None and (confidence < 0 or confidence > 1):
                errors.append("Confidence score must be between 0 and 1")
        
        if 'input_text' in state:
            if len(state['input_text']) > 10000:  # Max 10k characters
                errors.append("Input text too long (max 10000 characters)")
        
        return errors
    
    @staticmethod
    def validate_state_completeness(state: dict) -> bool:
        """Validate overall state completeness."""
        required_fields = ['session_id', 'input_text', 'current_step']
        type_schema = {
            'session_id': str,
            'input_text': str,
            'current_step': str,
            'confidence_score': (float, type(None))
        }
        
        missing_fields = StateValidator.validate_required_fields(state, required_fields)
        type_errors = StateValidator.validate_field_types(state, type_schema)
        business_errors = StateValidator.validate_business_rules(state)
        
        all_errors = missing_fields + type_errors + business_errors
        
        if all_errors:
            print(f"State validation errors: {all_errors}")
            return False
        
        return True

# Usage in nodes
def validated_node(state: AdvancedState) -> AdvancedState:
    """Node with comprehensive state validation."""
    if not StateValidator.validate_state_completeness(state):
        raise ValueError("Invalid state structure")
    
    # Node processing logic
    return state
```

### Node Error Handling Strategies

```python
class NodeErrorHandler:
    """Handle errors in node execution."""
    
    @staticmethod
    def retry_with_backoff(node_func, max_retries: int = 3, backoff_factor: float = 2.0):
        """Retry node execution with exponential backoff."""
        def wrapper(state: dict) -> dict:
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
    def graceful_degradation(node_func, fallback_func):
        """Execute fallback if main function fails."""
        def wrapper(state: dict) -> dict:
            try:
                return node_func(state)
            except Exception as e:
                print(f"Main function failed: {e}. Using fallback.")
                return fallback_func(state)
        
        return wrapper
    
    @staticmethod
    def circuit_breaker(node_func, failure_threshold: int = 5, recovery_timeout: int = 60):
        """Implement circuit breaker pattern for node execution."""
        failures = 0
        last_failure_time = 0
        
        def wrapper(state: dict) -> dict:
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

# Usage examples
@NodeErrorHandler.retry_with_backoff(max_retries=3)
def unreliable_node(state: AdvancedState) -> AdvancedState:
    """Node that might fail and needs retrying."""
    # Simulate occasional failure
    import random
    if random.random() < 0.3:
        raise Exception("Simulated failure")
    
    return {**state, 'processed': True}

@NodeErrorHandler.graceful_degradation(
    fallback_func=lambda s: {**s, 'processed': False, 'fallback_used': True}
)
def primary_node(state: AdvancedState) -> AdvancedState:
    """Primary node with fallback."""
    # Primary processing logic that might fail
    return {**state, 'processed': True, 'fallback_used': False}
```

### Graph-Level Error Handling

```python
def create_error_handling_graph():
    """Create a graph with comprehensive error handling."""
    graph = StateGraph(AdvancedState)
    
    # Add nodes with error handling
    graph.add_node("input_validation", NodeErrorHandler.retry_with_backoff(validate_node))
    graph.add_node("data_processing", NodeErrorHandler.circuit_breaker(process_node))
    graph.add_node("result_generation", NodeErrorHandler.graceful_degradation(generate_node))
    graph.add_node("error_handler", error_handler_node)
    graph.add_node("recovery_handler", recovery_handler_node)
    graph.add_node("final_output", final_output_node)
    
    graph.set_entry_point("input_validation")
    
    # Define routing with error handling
    def route_with_error_handling(state: AdvancedState) -> str:
        """Route based on state and error conditions."""
        if state.get('validation_errors'):
            return "error_handler"
        elif state.get('processing_failed'):
            return "recovery_handler"
        else:
            return "result_generation"
    
    def route_after_generation(state: AdvancedState) -> str:
        """Route after result generation."""
        if state.get('generation_failed'):
            return "error_handler"
        else:
            return "final_output"
    
    # Set up edges with error handling
    graph.add_conditional_edges(
        "input_validation",
        route_with_error_handling,
        {
            "error_handler": "error_handler",
            "recovery_handler": "recovery_handler",
            "result_generation": "result_generation"
        }
    )
    
    graph.add_conditional_edges(
        "result_generation",
        route_after_generation,
        {
            "error_handler": "error_handler",
            "final_output": "final_output"
        }
    )
    
    # Error handling paths
    graph.add_edge("error_handler", "recovery_handler")
    graph.add_edge("recovery_handler", "input_validation")  # Retry from beginning
    graph.add_edge("final_output", END)
    
    return graph.compile()

def error_handler_node(state: AdvancedState) -> AdvancedState:
    """Handle errors and prepare for recovery."""
    error_info = {
        'error_time': time.time(),
        'error_details': state.get('validation_errors', []) + state.get('processing_errors', []),
        'recovery_attempts': state.get('recovery_attempts', 0) + 1
    }
    
    return {
        **state,
        'error_info': error_info,
        'processing_failed': True,
        'current_step': 'error_handling'
    }

def recovery_handler_node(state: AdvancedState) -> AdvancedState:
    """Attempt to recover from errors."""
    recovery_attempts = state.get('recovery_attempts', 0)
    
    if recovery_attempts > 3:
        # Too many recovery attempts - fail permanently
        return {
            **state,
            'permanent_failure': True,
            'current_step': 'permanent_failure'
        }
    else:
        # Attempt recovery
        return {
            **state,
            'recovery_attempts': recovery_attempts,
            'processing_failed': False,
            'validation_errors': [],  # Clear validation errors for retry
            'current_step': 'recovery'
        }
```

### Graceful Degradation Techniques

```python
class GracefulDegradation:
    """Implement graceful degradation for LangGraph applications."""
    
    @staticmethod
    def create_degraded_state(original_state: dict, degradation_level: str) -> dict:
        """Create a degraded version of the state."""
        if degradation_level == 'minimal':
            # Keep only essential fields
            return {
                'session_id': original_state.get('session_id', ''),
                'input_text': original_state.get('input_text', ''),
                'degraded': True,
                'degradation_level': 'minimal'
            }
        elif degradation_level == 'partial':
            # Keep essential and some processing fields
            return {
                **{k: v for k, v in original_state.items() if k in [
                    'session_id', 'input_text', 'current_step', 'processed_data'
                ]},
                'degraded': True,
                'degradation_level': 'partial'
            }
        else:
            return original_state
    
    @staticmethod
    def create_fallback_node(primary_node, fallback_node, degradation_levels=None):
        """Create a node that degrades gracefully."""
        if degradation_levels is None:
            degradation_levels = ['full', 'partial', 'minimal', 'none']
        
        def degraded_node(state: dict) -> dict:
            for level in degradation_levels:
                try:
                    if level == 'full':
                        return primary_node(state)
                    elif level == 'partial':
                        degraded_state = GracefulDegradation.create_degraded_state(state, 'partial')
                        return primary_node(degraded_state)
                    elif level == 'minimal':
                        degraded_state = GracefulDegradation.create_degraded_state(state, 'minimal')
                        return fallback_node(degraded_state)
                    else:
                        return fallback_node(state)
                except Exception as e:
                    print(f"Failed at degradation level {level}: {e}")
                    continue
            
            # If all levels fail, return minimal state
            return GracefulDegradation.create_degraded_state(state, 'minimal')
        
        return degraded_node

# Usage example
def create_resilient_graph():
    """Create a graph with graceful degradation."""
    graph = StateGraph(AdvancedState)
    
    # Create resilient nodes
    resilient_processing = GracefulDegradation.create_fallback_node(
        primary_node=complex_processing_node,
        fallback_node=simple_processing_node,
        degradation_levels=['full', 'partial', 'minimal']
    )
    
    resilient_analysis = GracefulDegradation.create_fallback_node(
        primary_node=advanced_analysis_node,
        fallback_node=basic_analysis_node,
        degradation_levels=['full', 'partial']
    )
    
    # Add nodes to graph
    graph.add_node("processing", resilient_processing)
    graph.add_node("analysis", resilient_analysis)
    graph.add_node("output", output_node)
    
    graph.set_entry_point("processing")
    graph.add_edge("processing", "analysis")
    graph.add_edge("analysis", "output")
    graph.add_edge("output", END)
    
    return graph.compile()
```

## Summary

This module covered the essential building blocks of LangGraph applications:

1. **State Management**: Advanced schema design, validation, persistence, and optimization
2. **Node Creation**: Different node types, composition, error handling, and performance optimization
3. **Edge Types**: Normal and conditional edges, dynamic routing, and complex patterns
4. **Graph Compilation**: Validation, execution modes, performance monitoring, and debugging
5. **Error Handling**: State validation, node error strategies, graph-level handling, and graceful degradation

These building blocks provide the foundation for creating robust, scalable, and maintainable LangGraph applications. Mastering these concepts enables you to build sophisticated multi-agent systems with proper error handling, performance optimization, and graceful degradation capabilities.