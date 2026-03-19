#!/usr/bin/env python3
"""
LangGraph Graph Execution - Core Concept

This file demonstrates the fundamental concept of Graph Execution in LangGraph.
Graph execution is the process of running a compiled graph with input state,
producing output through the defined workflow. It includes various execution
modes, streaming, error handling, and performance monitoring.

Key Concepts Covered:
- Graph compilation and execution
- Synchronous vs asynchronous execution
- Streaming execution for real-time updates
- Error handling and recovery
- Performance monitoring and debugging
- State checkpointing and recovery
"""

from typing import TypedDict, List, Optional, Dict, Any, Union, Callable, Awaitable
from datetime import datetime
import asyncio
import time
import json
import pickle
from typing import get_type_hints


# ============================================================================
# 1. BASIC GRAPH EXECUTION
# ============================================================================

class BasicState(TypedDict):
    """Basic state for execution examples."""
    input_text: str
    processed_text: str
    step_count: int


def create_basic_execution_graph():
    """
    Basic Graph Execution Example:
    
    Demonstrates how to create and execute a simple graph.
    Shows the complete workflow from graph creation to execution.
    """
    print("🏗️  Creating basic execution graph...")
    
    # Import here to avoid issues
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        print("⚠️  LangGraph not available, using mock implementation")
        return create_mock_execution_graph()
    
    graph = StateGraph(BasicState)
    
    # Add nodes
    def start_node(state: BasicState) -> BasicState:
        print(f"🚀 Starting execution with: '{state['input_text']}'")
        return {
            'input_text': state['input_text'],
            'processed_text': f"Started: {state['input_text']}",
            'step_count': state['step_count'] + 1
        }
    
    def process_node(state: BasicState) -> BasicState:
        print(f"⚙️  Processing: '{state['processed_text']}'")
        return {
            'input_text': state['input_text'],
            'processed_text': f"Processed: {state['processed_text']}",
            'step_count': state['step_count'] + 1
        }
    
    def end_node(state: BasicState) -> BasicState:
        print(f"🏁 Ending execution: '{state['processed_text']}'")
        return {
            'input_text': state['input_text'],
            'processed_text': f"Completed: {state['processed_text']}",
            'step_count': state['step_count'] + 1
        }
    
    graph.add_node("start", start_node)
    graph.add_node("process", process_node)
    graph.add_node("end", end_node)
    
    # Set up execution flow
    graph.set_entry_point("start")
    graph.add_edge("start", "process")
    graph.add_edge("process", "end")
    graph.add_edge("end", END)
    
    # Compile graph
    return graph.compile()


def create_mock_execution_graph():
    """
    Mock Graph for demonstration when LangGraph is not available.
    """
    class MockGraph:
        def invoke(self, state: BasicState) -> BasicState:
            print(f"🚀 Starting execution with: '{state['input_text']}'")
            state['processed_text'] = f"Started: {state['input_text']}"
            state['step_count'] += 1
            
            print(f"⚙️  Processing: '{state['processed_text']}'")
            state['processed_text'] = f"Processed: {state['processed_text']}"
            state['step_count'] += 1
            
            print(f"🏁 Ending execution: '{state['processed_text']}'")
            state['processed_text'] = f"Completed: {state['processed_text']}"
            state['step_count'] += 1
            
            return state
        
        async def astream(self, state: BasicState):
            """Mock streaming execution."""
            yield {"step": "start", "message": f"Starting with: {state['input_text']}"}
            await asyncio.sleep(0.1)
            
            yield {"step": "process", "message": f"Processing: {state['input_text']}"}
            await asyncio.sleep(0.1)
            
            yield {"step": "end", "message": f"Completed: {state['input_text']}"}
    
    return MockGraph()


# ============================================================================
# 2. ASYNCHRONOUS EXECUTION
# ============================================================================

class AsyncState(TypedDict):
    """State for async execution examples."""
    session_id: str
    user_input: str
    processed_data: Dict[str, Any]
    async_operations: List[str]
    current_step: str


async def create_async_execution_graph():
    """
    Async Graph Execution Example:
    
    Demonstrates executing graphs with async nodes and streaming results.
    Shows how to handle long-running operations and real-time updates.
    """
    print("⚡ Creating async execution graph...")
    
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return create_mock_async_graph()
    
    graph = StateGraph(AsyncState)
    
    # Add async nodes
    async def async_input_processor(state: AsyncState) -> AsyncState:
        print(f"📥 Async input processing: '{state['user_input'][:20]}...'")
        await asyncio.sleep(0.2)  # Simulate async processing
        
        return {
            **state,
            'processed_data': {'input_length': len(state['user_input'])},
            'async_operations': state['async_operations'] + ['input_processing'],
            'current_step': 'async_input_processing'
        }
    
    async def async_data_enricher(state: AsyncState) -> AsyncState:
        print(f" enriching data...")
        await asyncio.sleep(0.3)  # Simulate async API call
        
        return {
            **state,
            'processed_data': {
                **state['processed_data'],
                'enrichment_result': 'success',
                'enrichment_timestamp': datetime.now().isoformat()
            },
            'async_operations': state['async_operations'] + ['data_enrichment'],
            'current_step': 'async_data_enrichment'
        }
    
    async def async_output_generator(state: AsyncState) -> AsyncState:
        print(f"🎯 Async output generation...")
        await asyncio.sleep(0.1)  # Simulate async output generation
        
        return {
            **state,
            'processed_data': {
                **state['processed_data'],
                'final_output': f"Processed: {state['user_input'][:30]}..."
            },
            'async_operations': state['async_operations'] + ['output_generation'],
            'current_step': 'async_output_generation'
        }
    
    graph.add_node("input_processor", async_input_processor)
    graph.add_node("data_enricher", async_data_enricher)
    graph.add_node("output_generator", async_output_generator)
    
    graph.set_entry_point("input_processor")
    graph.add_edge("input_processor", "data_enricher")
    graph.add_edge("data_enricher", "output_generator")
    graph.add_edge("output_generator", END)
    
    return graph.compile()


def create_mock_async_graph():
    """Mock async graph for demonstration."""
    class MockAsyncGraph:
        async def invoke(self, state: AsyncState) -> AsyncState:
            print(f"📥 Async input processing: '{state['user_input'][:20]}...'")
            await asyncio.sleep(0.2)
            
            state['processed_data'] = {'input_length': len(state['user_input'])}
            state['async_operations'] = state['async_operations'] + ['input_processing']
            state['current_step'] = 'async_input_processing'
            
            print(f" enriching data...")
            await asyncio.sleep(0.3)
            
            state['processed_data']['enrichment_result'] = 'success'
            state['processed_data']['enrichment_timestamp'] = datetime.now().isoformat()
            state['async_operations'] = state['async_operations'] + ['data_enrichment']
            state['current_step'] = 'async_data_enrichment'
            
            print(f"🎯 Async output generation...")
            await asyncio.sleep(0.1)
            
            state['processed_data']['final_output'] = f"Processed: {state['user_input'][:30]}..."
            state['async_operations'] = state['async_operations'] + ['output_generation']
            state['current_step'] = 'async_output_generation'
            
            return state
        
        async def astream(self, state: AsyncState):
            """Mock streaming execution."""
            yield {"step": "input_processing", "status": "started"}
            await asyncio.sleep(0.2)
            
            yield {"step": "input_processing", "status": "completed"}
            yield {"step": "data_enrichment", "status": "started"}
            await asyncio.sleep(0.3)
            
            yield {"step": "data_enrichment", "status": "completed"}
            yield {"step": "output_generation", "status": "started"}
            await asyncio.sleep(0.1)
            
            yield {"step": "output_generation", "status": "completed"}
    
    return MockAsyncGraph()


# ============================================================================
# 3. STREAMING EXECUTION
# ============================================================================

class StreamingState(TypedDict):
    """State for streaming execution examples."""
    session_id: str
    user_input: str
    stream_progress: List[Dict[str, Any]]
    current_chunk: str
    total_chunks: int
    current_step: str


def create_streaming_execution_graph():
    """
    Streaming Execution Example:
    
    Demonstrates executing graphs with streaming results.
    Shows how to handle long-running operations and real-time updates.
    """
    print("🌊 Creating streaming execution graph...")
    
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return create_mock_streaming_graph()
    
    graph = StateGraph(StreamingState)
    
    # Add streaming nodes
    def stream_initializer(state: StreamingState) -> StreamingState:
        print(f"🌊 Initializing stream for: '{state['user_input'][:20]}...'")
        
        # Split input into chunks for streaming
        chunk_size = 10
        chunks = [state['user_input'][i:i+chunk_size] 
                 for i in range(0, len(state['user_input']), chunk_size)]
        
        return {
            **state,
            'stream_progress': [{'chunk': chunk, 'status': 'pending'} for chunk in chunks],
            'total_chunks': len(chunks),
            'current_step': 'stream_initialization'
        }
    
    def stream_processor(state: StreamingState) -> StreamingState:
        print(f"🌊 Processing stream (chunk {len([p for p in state['stream_progress'] if p['status'] == 'completed']) + 1}/{state['total_chunks']})")
        
        # Process next chunk
        pending_chunks = [i for i, chunk in enumerate(state['stream_progress']) 
                         if chunk['status'] == 'pending']
        
        if pending_chunks:
            chunk_index = pending_chunks[0]
            state['stream_progress'][chunk_index]['status'] = 'completed'
            state['stream_progress'][chunk_index]['processed'] = f"Processed: {state['stream_progress'][chunk_index]['chunk']}"
        
        return {
            **state,
            'current_step': 'stream_processing'
        }
    
    def stream_finalizer(state: StreamingState) -> StreamingState:
        print(f"🌊 Finalizing stream with {len(state['stream_progress'])} chunks")
        
        # Combine all processed chunks
        final_result = ''.join([chunk.get('processed', chunk['chunk']) 
                               for chunk in state['stream_progress']])
        
        return {
            **state,
            'current_chunk': final_result,
            'current_step': 'stream_finalization'
        }
    
    graph.add_node("stream_init", stream_initializer)
    graph.add_node("stream_process", stream_processor)
    graph.add_node("stream_finalize", stream_finalizer)
    
    graph.set_entry_point("stream_init")
    graph.add_edge("stream_init", "stream_process")
    graph.add_edge("stream_process", "stream_finalize")
    graph.add_edge("stream_finalize", END)
    
    return graph.compile()


def create_mock_streaming_graph():
    """Mock streaming graph for demonstration."""
    class MockStreamingGraph:
        def invoke(self, state: StreamingState) -> StreamingState:
            print(f"🌊 Initializing stream for: '{state['user_input'][:20]}...'")
            
            chunk_size = 10
            chunks = [state['user_input'][i:i+chunk_size] 
                     for i in range(0, len(state['user_input']), chunk_size)]
            
            state['stream_progress'] = [{'chunk': chunk, 'status': 'pending'} for chunk in chunks]
            state['total_chunks'] = len(chunks)
            state['current_step'] = 'stream_initialization'
            
            print(f"🌊 Processing stream (chunk 1/{state['total_chunks']})")
            state['stream_progress'][0]['status'] = 'completed'
            state['stream_progress'][0]['processed'] = f"Processed: {state['stream_progress'][0]['chunk']}"
            state['current_step'] = 'stream_processing'
            
            print(f"🌊 Finalizing stream with {len(state['stream_progress'])} chunks")
            final_result = ''.join([chunk.get('processed', chunk['chunk']) 
                                   for chunk in state['stream_progress']])
            state['current_chunk'] = final_result
            state['current_step'] = 'stream_finalization'
            
            return state
        
        async def astream(self, state: StreamingState):
            """Mock streaming execution."""
            yield {"event": "stream_init", "message": "Initializing stream"}
            
            chunk_size = 10
            chunks = [state['user_input'][i:i+chunk_size] 
                     for i in range(0, len(state['user_input']), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                yield {"event": "stream_chunk", "chunk_index": i, "chunk": chunk}
                await asyncio.sleep(0.1)
            
            yield {"event": "stream_complete", "message": "Stream processing complete"}
    
    return MockStreamingGraph()


# ============================================================================
# 4. ERROR HANDLING AND RECOVERY
# ============================================================================

class ErrorHandlingState(TypedDict):
    """State for error handling examples."""
    session_id: str
    user_input: str
    error_count: int
    retry_count: int
    error_history: List[Dict[str, Any]]
    current_step: str
    execution_status: str


def create_error_handling_graph():
    """
    Error Handling Graph Example:
    
    Demonstrates comprehensive error handling and recovery strategies.
    Shows how to handle failures gracefully and implement retry logic.
    """
    print("🛡️  Creating error handling graph...")
    
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return create_mock_error_graph()
    
    graph = StateGraph(ErrorHandlingState)
    
    # Add error handling nodes
    def safe_processor(state: ErrorHandlingState) -> ErrorHandlingState:
        print(f"🛡️  Safe processing: '{state['user_input'][:20]}...'")
        
        # Simulate potential failure
        if len(state['user_input']) < 5:
            raise ValueError("Input too short for processing")
        
        return {
            **state,
            'current_step': 'safe_processing',
            'execution_status': 'success'
        }
    
    def error_catcher(state: ErrorHandlingState, error: Exception) -> ErrorHandlingState:
        print(f"🚨 Error caught: {error}")
        
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'step': state['current_step']
        }
        
        return {
            **state,
            'error_count': state['error_count'] + 1,
            'error_history': state['error_history'] + [error_info],
            'current_step': 'error_handling',
            'execution_status': 'error_handled'
        }
    
    def retry_handler(state: ErrorHandlingState) -> ErrorHandlingState:
        print(f"🔄 Retry handler (attempt {state['retry_count'] + 1})")
        
        if state['retry_count'] >= 3:
            return {
                **state,
                'current_step': 'retry_exhausted',
                'execution_status': 'failed'
            }
        
        return {
            **state,
            'retry_count': state['retry_count'] + 1,
            'current_step': 'retry_handling',
            'execution_status': 'retrying'
        }
    
    def fallback_processor(state: ErrorHandlingState) -> ErrorHandlingState:
        print(f"🔄 Fallback processing for: '{state['user_input'][:20]}...'")
        
        return {
            **state,
            'current_step': 'fallback_processing',
            'execution_status': 'fallback_success'
        }
    
    graph.add_node("safe_processor", safe_processor)
    graph.add_node("error_catcher", error_catcher)
    graph.add_node("retry_handler", retry_handler)
    graph.add_node("fallback_processor", fallback_processor)
    
    graph.set_entry_point("safe_processor")
    graph.add_edge("safe_processor", "fallback_processor")
    graph.add_edge("error_catcher", "retry_handler")
    graph.add_edge("retry_handler", "safe_processor")  # Retry loop
    graph.add_edge("fallback_processor", END)
    
    return graph.compile()


def create_mock_error_graph():
    """Mock error handling graph for demonstration."""
    class MockErrorGraph:
        def invoke(self, state: ErrorHandlingState) -> ErrorHandlingState:
            print(f"🛡️  Safe processing: '{state['user_input'][:20]}...'")
            
            if len(state['user_input']) < 5:
                print(f"🚨 Error caught: Input too short for processing")
                
                error_info = {
                    'error_type': 'ValueError',
                    'error_message': 'Input too short for processing',
                    'timestamp': datetime.now().isoformat(),
                    'step': state['current_step']
                }
                
                state['error_count'] += 1
                state['error_history'] = state['error_history'] + [error_info]
                state['current_step'] = 'error_handling'
                state['execution_status'] = 'error_handled'
                
                print(f"🔄 Retry handler (attempt {state['retry_count'] + 1})")
                
                if state['retry_count'] >= 3:
                    state['current_step'] = 'retry_exhausted'
                    state['execution_status'] = 'failed'
                else:
                    state['retry_count'] += 1
                    state['current_step'] = 'retry_handling'
                    state['execution_status'] = 'retrying'
                    
                    # Retry processing
                    print(f"🛡️  Safe processing: '{state['user_input'][:20]}...'")
                    state['current_step'] = 'safe_processing'
                    state['execution_status'] = 'success'
            else:
                state['current_step'] = 'safe_processing'
                state['execution_status'] = 'success'
            
            print(f"🔄 Fallback processing for: '{state['user_input'][:20]}...'")
            state['current_step'] = 'fallback_processing'
            state['execution_status'] = 'fallback_success'
            
            return state
    
    return MockErrorGraph()


# ============================================================================
# 5. PERFORMANCE MONITORING
# ============================================================================

class PerformanceState(TypedDict):
    """State for performance monitoring examples."""
    session_id: str
    user_input: str
    performance_metrics: Dict[str, Any]
    execution_timeline: List[Dict[str, Any]]
    memory_usage: List[Dict[str, Any]]
    current_step: str


def create_performance_monitoring_graph():
    """
    Performance Monitoring Graph Example:
    
    Demonstrates how to monitor and measure graph execution performance.
    Shows timing, memory usage, and execution metrics.
    """
    print("📊 Creating performance monitoring graph...")
    
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return create_mock_performance_graph()
    
    graph = StateGraph(PerformanceState)
    
    # Add performance monitoring nodes
    def performance_monitor(state: PerformanceState) -> PerformanceState:
        print(f"📊 Performance monitoring: '{state['user_input'][:20]}...'")
        
        import sys
        import psutil
        
        # Capture performance metrics
        metrics = {
            'start_time': datetime.now().isoformat(),
            'input_size': len(state['user_input']),
            'memory_before': psutil.Process().memory_info().rss / 1024 / 1024,  # MB
            'cpu_before': psutil.Process().cpu_percent()
        }
        
        timeline_entry = {
            'step': 'performance_monitoring',
            'timestamp': datetime.now().isoformat(),
            'action': 'start_monitoring'
        }
        
        return {
            **state,
            'performance_metrics': metrics,
            'execution_timeline': state['execution_timeline'] + [timeline_entry],
            'current_step': 'performance_monitoring'
        }
    
    def heavy_computation(state: PerformanceState) -> PerformanceState:
        print(f"💻 Heavy computation starting...")
        
        # Simulate heavy computation
        start_time = time.time()
        result = sum(i * i for i in range(100000))
        computation_time = time.time() - start_time
        
        import psutil
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Update metrics
        state['performance_metrics']['computation_time'] = computation_time
        state['performance_metrics']['memory_after'] = memory_after
        state['performance_metrics']['memory_increase'] = memory_after - state['performance_metrics']['memory_before']
        
        timeline_entry = {
            'step': 'heavy_computation',
            'timestamp': datetime.now().isoformat(),
            'action': 'heavy_computation_complete',
            'computation_time': computation_time
        }
        
        memory_entry = {
            'step': 'heavy_computation',
            'timestamp': datetime.now().isoformat(),
            'memory_mb': memory_after
        }
        
        return {
            **state,
            'execution_timeline': state['execution_timeline'] + [timeline_entry],
            'memory_usage': state['memory_usage'] + [memory_entry],
            'current_step': 'heavy_computation'
        }
    
    def performance_reporter(state: PerformanceState) -> PerformanceState:
        print(f"📋 Generating performance report...")
        
        metrics = state['performance_metrics']
        computation_time = metrics.get('computation_time', 0)
        memory_increase = metrics.get('memory_increase', 0)
        
        report = {
            'total_execution_time': computation_time,
            'memory_efficiency': 'good' if memory_increase < 50 else 'poor',
            'performance_score': min(100, int(100 - (computation_time * 100)))
        }
        
        timeline_entry = {
            'step': 'performance_reporting',
            'timestamp': datetime.now().isoformat(),
            'action': 'report_generated',
            'report': report
        }
        
        return {
            **state,
            'performance_metrics': {**metrics, 'final_report': report},
            'execution_timeline': state['execution_timeline'] + [timeline_entry],
            'current_step': 'performance_reporting'
        }
    
    graph.add_node("performance_monitor", performance_monitor)
    graph.add_node("heavy_computation", heavy_computation)
    graph.add_node("performance_reporter", performance_reporter)
    
    graph.set_entry_point("performance_monitor")
    graph.add_edge("performance_monitor", "heavy_computation")
    graph.add_edge("heavy_computation", "performance_reporter")
    graph.add_edge("performance_reporter", END)
    
    return graph.compile()


def create_mock_performance_graph():
    """Mock performance monitoring graph for demonstration."""
    class MockPerformanceGraph:
        def invoke(self, state: PerformanceState) -> PerformanceState:
            print(f"📊 Performance monitoring: '{state['user_input'][:20]}...'")
            
            metrics = {
                'start_time': datetime.now().isoformat(),
                'input_size': len(state['user_input']),
                'memory_before': 50.0,  # Mock value
                'cpu_before': 10.0       # Mock value
            }
            
            timeline_entry = {
                'step': 'performance_monitoring',
                'timestamp': datetime.now().isoformat(),
                'action': 'start_monitoring'
            }
            
            state['performance_metrics'] = metrics
            state['execution_timeline'] = state['execution_timeline'] + [timeline_entry]
            state['current_step'] = 'performance_monitoring'
            
            print(f"💻 Heavy computation starting...")
            start_time = time.time()
            result = sum(i * i for i in range(100000))
            computation_time = time.time() - start_time
            
            memory_after = 75.0  # Mock value
            
            state['performance_metrics']['computation_time'] = computation_time
            state['performance_metrics']['memory_after'] = memory_after
            state['performance_metrics']['memory_increase'] = memory_after - metrics['memory_before']
            
            timeline_entry = {
                'step': 'heavy_computation',
                'timestamp': datetime.now().isoformat(),
                'action': 'heavy_computation_complete',
                'computation_time': computation_time
            }
            
            memory_entry = {
                'step': 'heavy_computation',
                'timestamp': datetime.now().isoformat(),
                'memory_mb': memory_after
            }
            
            state['execution_timeline'] = state['execution_timeline'] + [timeline_entry]
            state['memory_usage'] = state['memory_usage'] + [memory_entry]
            state['current_step'] = 'heavy_computation'
            
            print(f"📋 Generating performance report...")
            report = {
                'total_execution_time': computation_time,
                'memory_efficiency': 'good' if memory_increase < 50 else 'poor',
                'performance_score': min(100, int(100 - (computation_time * 100)))
            }
            
            timeline_entry = {
                'step': 'performance_reporting',
                'timestamp': datetime.now().isoformat(),
                'action': 'report_generated',
                'report': report
            }
            
            state['performance_metrics']['final_report'] = report
            state['execution_timeline'] = state['execution_timeline'] + [timeline_entry]
            state['current_step'] = 'performance_reporting'
            
            return state
    
    return MockPerformanceGraph()


# ============================================================================
# 6. STATE CHECKPOINTING AND RECOVERY
# ============================================================================

class CheckpointState(TypedDict):
    """State for checkpointing examples."""
    session_id: str
    user_input: str
    checkpoint_data: Dict[str, Any]
    recovery_points: List[Dict[str, Any]]
    current_step: str
    execution_phase: str


def create_checkpointing_graph():
    """
    State Checkpointing Graph Example:
    
    Demonstrates how to implement state checkpointing and recovery.
    Shows how to save state at key points and resume execution.
    """
    print("💾 Creating checkpointing graph...")
    
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return create_mock_checkpoint_graph()
    
    graph = StateGraph(CheckpointState)
    
    # Add checkpointing nodes
    def checkpoint_initializer(state: CheckpointState) -> CheckpointState:
        print(f"💾 Initializing checkpoint system...")
        
        checkpoint_data = {
            'initial_state': {
                'user_input': state['user_input'],
                'session_id': state['session_id'],
                'timestamp': datetime.now().isoformat()
            },
            'checkpoint_version': '1.0',
            'recovery_enabled': True
        }
        
        recovery_point = {
            'phase': 'initialization',
            'checkpoint_data': checkpoint_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            **state,
            'checkpoint_data': checkpoint_data,
            'recovery_points': state['recovery_points'] + [recovery_point],
            'current_step': 'checkpoint_initialization',
            'execution_phase': 'initialization'
        }
    
    def checkpoint_processor(state: CheckpointState) -> CheckpointState:
        print(f"💾 Processing with checkpointing...")
        
        # Simulate processing that might fail
        processed_data = {
            'input_length': len(state['user_input']),
            'processed_text': state['user_input'].upper(),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # Create checkpoint
        checkpoint_data = {
            'processed_data': processed_data,
            'processing_phase': 'main_processing',
            'checkpoint_timestamp': datetime.now().isoformat()
        }
        
        recovery_point = {
            'phase': 'main_processing',
            'checkpoint_data': checkpoint_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            **state,
            'checkpoint_data': checkpoint_data,
            'recovery_points': state['recovery_points'] + [recovery_point],
            'current_step': 'checkpoint_processing',
            'execution_phase': 'main_processing'
        }
    
    def checkpoint_finalizer(state: CheckpointState) -> CheckpointState:
        print(f"💾 Finalizing with checkpointing...")
        
        final_data = {
            'final_result': f"Final: {state['user_input']}",
            'execution_complete': True,
            'final_timestamp': datetime.now().isoformat()
        }
        
        checkpoint_data = {
            'final_data': final_data,
            'execution_phase': 'finalization',
            'checkpoint_timestamp': datetime.now().isoformat()
        }
        
        recovery_point = {
            'phase': 'finalization',
            'checkpoint_data': checkpoint_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            **state,
            'checkpoint_data': checkpoint_data,
            'recovery_points': state['recovery_points'] + [recovery_point],
            'current_step': 'checkpoint_finalization',
            'execution_phase': 'finalization'
        }
    
    graph.add_node("checkpoint_init", checkpoint_initializer)
    graph.add_node("checkpoint_process", checkpoint_processor)
    graph.add_node("checkpoint_finalize", checkpoint_finalizer)
    
    graph.set_entry_point("checkpoint_init")
    graph.add_edge("checkpoint_init", "checkpoint_process")
    graph.add_edge("checkpoint_process", "checkpoint_finalize")
    graph.add_edge("checkpoint_finalize", END)
    
    return graph.compile()


def create_mock_checkpoint_graph():
    """Mock checkpointing graph for demonstration."""
    class MockCheckpointGraph:
        def invoke(self, state: CheckpointState) -> CheckpointState:
            print(f"💾 Initializing checkpoint system...")
            
            checkpoint_data = {
                'initial_state': {
                    'user_input': state['user_input'],
                    'session_id': state['session_id'],
                    'timestamp': datetime.now().isoformat()
                },
                'checkpoint_version': '1.0',
                'recovery_enabled': True
            }
            
            recovery_point = {
                'phase': 'initialization',
                'checkpoint_data': checkpoint_data,
                'timestamp': datetime.now().isoformat()
            }
            
            state['checkpoint_data'] = checkpoint_data
            state['recovery_points'] = state['recovery_points'] + [recovery_point]
            state['current_step'] = 'checkpoint_initialization'
            state['execution_phase'] = 'initialization'
            
            print(f"💾 Processing with checkpointing...")
            processed_data = {
                'input_length': len(state['user_input']),
                'processed_text': state['user_input'].upper(),
                'processing_timestamp': datetime.now().isoformat()
            }
            
            checkpoint_data = {
                'processed_data': processed_data,
                'processing_phase': 'main_processing',
                'checkpoint_timestamp': datetime.now().isoformat()
            }
            
            recovery_point = {
                'phase': 'main_processing',
                'checkpoint_data': checkpoint_data,
                'timestamp': datetime.now().isoformat()
            }
            
            state['checkpoint_data'] = checkpoint_data
            state['recovery_points'] = state['recovery_points'] + [recovery_point]
            state['current_step'] = 'checkpoint_processing'
            state['execution_phase'] = 'main_processing'
            
            print(f"💾 Finalizing with checkpointing...")
            final_data = {
                'final_result': f"Final: {state['user_input']}",
                'execution_complete': True,
                'final_timestamp': datetime.now().isoformat()
            }
            
            checkpoint_data = {
                'final_data': final_data,
                'execution_phase': 'finalization',
                'checkpoint_timestamp': datetime.now().isoformat()
            }
            
            recovery_point = {
                'phase': 'finalization',
                'checkpoint_data': checkpoint_data,
                'timestamp': datetime.now().isoformat()
            }
            
            state['checkpoint_data'] = checkpoint_data
            state['recovery_points'] = state['recovery_points'] + [recovery_point]
            state['current_step'] = 'checkpoint_finalization'
            state['execution_phase'] = 'finalization'
            
            return state
    
    return MockCheckpointGraph()


# ============================================================================
# 7. EXAMPLE USAGE AND DEMONSTRATION
# ============================================================================

def demonstrate_graph_execution():
    """
    Demonstrate all graph execution concepts with practical examples.
    """
    print("🎯 GRAPH EXECUTION DEMONSTRATION")
    print("=" * 60)
    
    # 1. Test basic execution
    print("\n1. Basic Graph Execution:")
    basic_app = create_basic_execution_graph()
    basic_input = {
        'input_text': 'hello world',
        'processed_text': '',
        'step_count': 0
    }
    basic_result = basic_app.invoke(basic_input)
    print(f"Basic execution result: Step count = {basic_result['step_count']}")
    
    # 2. Test async execution
    print("\n2. Async Graph Execution:")
    async def run_async_example():
        async_app = await create_async_execution_graph()
        async_input = {
            'session_id': 'async_test',
            'user_input': 'Async processing test input',
            'processed_data': {},
            'async_operations': [],
            'current_step': ''
        }
        async_result = await async_app.invoke(async_input)
        print(f"Async execution completed: {async_result['current_step']}")
        print(f"Async operations: {async_result['async_operations']}")
        return async_result
    
    asyncio.run(run_async_example())
    
    # 3. Test streaming execution
    print("\n3. Streaming Graph Execution:")
    streaming_app = create_streaming_execution_graph()
    streaming_input = {
        'session_id': 'stream_test',
        'user_input': 'This is a test input for streaming processing',
        'stream_progress': [],
        'current_chunk': '',
        'total_chunks': 0,
        'current_step': ''
    }
    streaming_result = streaming_app.invoke(streaming_input)
    print(f"Streaming completed: {streaming_result['current_step']}")
    print(f"Total chunks: {streaming_result['total_chunks']}")
    
    # 4. Test error handling
    print("\n4. Error Handling Graph Execution:")
    error_app = create_error_handling_graph()
    error_input = {
        'session_id': 'error_test',
        'user_input': 'short',  # This will trigger an error
        'error_count': 0,
        'retry_count': 0,
        'error_history': [],
        'current_step': '',
        'execution_status': ''
    }
    error_result = error_app.invoke(error_input)
    print(f"Error handling result: {error_result['execution_status']}")
    print(f"Error count: {error_result['error_count']}")
    
    # 5. Test performance monitoring
    print("\n5. Performance Monitoring Graph Execution:")
    perf_app = create_performance_monitoring_graph()
    perf_input = {
        'session_id': 'perf_test',
        'user_input': 'Performance monitoring test input',
        'performance_metrics': {},
        'execution_timeline': [],
        'memory_usage': [],
        'current_step': ''
    }
    perf_result = perf_app.invoke(perf_input)
    print(f"Performance monitoring completed: {perf_result['current_step']}")
    if 'final_report' in perf_result['performance_metrics']:
        report = perf_result['performance_metrics']['final_report']
        print(f"Performance score: {report['performance_score']}")
    
    # 6. Test checkpointing
    print("\n6. State Checkpointing Graph Execution:")
    checkpoint_app = create_checkpointing_graph()
    checkpoint_input = {
        'session_id': 'checkpoint_test',
        'user_input': 'Checkpointing test input',
        'checkpoint_data': {},
        'recovery_points': [],
        'current_step': '',
        'execution_phase': ''
    }
    checkpoint_result = checkpoint_app.invoke(checkpoint_input)
    print(f"Checkpointing completed: {checkpoint_result['execution_phase']}")
    print(f"Recovery points: {len(checkpoint_result['recovery_points'])}")
    
    print("\n✅ GRAPH EXECUTION DEMONSTRATION COMPLETED")


if __name__ == "__main__":
    """
    Run the graph execution demonstration.
    """
    demonstrate_graph_execution()