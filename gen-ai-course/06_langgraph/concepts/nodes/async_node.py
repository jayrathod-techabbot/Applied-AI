#!/usr/bin/env python3
"""
Async Node Definition - LangGraph Core Concept

This file demonstrates asynchronous nodes in LangGraph, which are essential
for I/O operations like API calls, database queries, or file operations.

Key Concepts:
- Async node function signature
- Await syntax usage
- Async/await patterns
- I/O bound operations
"""

from typing import TypedDict, Dict, Any
import asyncio
from datetime import datetime


class AsyncState(TypedDict):
    """State for async node examples."""
    session_id: str
    user_input: str
    processed_data: Dict[str, Any]
    current_step: str


async def async_node_example(state: AsyncState) -> AsyncState:
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
        'current_step': 'async_processing'
    }


async def create_async_node_example():
    """
    Create an example of async node execution.
    
    Returns:
        AsyncState: Example state after async node execution
    """
    # Create initial state
    initial_state = AsyncState(
        session_id="async_session_001",
        user_input="Async processing test",
        processed_data={},
        current_step=""
    )
    
    # Execute async node
    result_state = await async_node_example(initial_state)
    
    return result_state


async def demonstrate_async_node():
    """
    Demonstrate async node usage.
    """
    print("🎯 Async Node Demonstration")
    print("=" * 28)
    
    # Execute async node
    result = await create_async_node_example()
    print(f"Async node completed: {result['current_step']}")
    print(f"External service result: {result['processed_data']['external_service']['service_response']}")
    print("✅ Async node demonstration completed")


if __name__ == "__main__":
    asyncio.run(demonstrate_async_node())