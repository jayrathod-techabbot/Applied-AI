#!/usr/bin/env python3
"""
Advanced State Schemas - LangGraph Core Concept

This file demonstrates advanced state schemas suitable for production
applications. Shows how to structure state for complex workflows and
multi-user applications.

Key Concepts:
- Advanced state schemas
- Session management
- Workflow tracking
- Domain-specific state
"""

from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime


class UserSessionState(TypedDict):
    """
    User Session State Example:
    
    A comprehensive state structure suitable for multi-user applications.
    Includes session tracking, user identification, and workflow management.
    """
    # Session identification
    session_id: str              # Unique session identifier
    user_id: Optional[str]       # User identification
    session_start: datetime      # When session started
    
    # Input and processing
    input_text: str              # Original user input
    processed_data: Dict[str, Any]  # Processed information
    validation_errors: List[str]    # Any validation issues
    
    # Workflow tracking
    current_step: str            # Current execution step
    completed_steps: List[str]   # Steps that have been completed
    next_actions: List[str]      # Planned next steps


class ECommerceState(TypedDict):
    """
    E-commerce State Example:
    
    Domain-specific state for an e-commerce application.
    Shows how to structure state for specific business domains.
    """
    # Customer information
    customer_id: str
    customer_name: str
    customer_email: str
    customer_preferences: Dict[str, Any]
    
    # Order information
    order_id: str
    items: List[Dict[str, Any]]  # Product details
    subtotal: float
    tax: float
    shipping_cost: float
    total_amount: float
    
    # Processing state
    order_status: str            # pending, processing, shipped, delivered
    payment_status: str          # pending, paid, failed, refunded


def create_session_state_example():
    """
    Create an example of user session state.
    
    Returns:
        UserSessionState: Example session state
    """
    return UserSessionState(
        session_id="session_001",
        user_id="user_123",
        session_start=datetime.now(),
        input_text="Hello, how can I help you?",
        processed_data={},
        validation_errors=[],
        current_step="initial",
        completed_steps=[],
        next_actions=[]
    )


def demonstrate_advanced_state():
    """
    Demonstrate advanced state usage.
    """
    print("🎯 Advanced State Demonstration")
    print("=" * 35)
    
    # Create session state
    session_state = create_session_state_example()
    print(f"Session state: {session_state['session_id']}")
    
    # Update workflow tracking
    session_state['current_step'] = 'processing'
    session_state['completed_steps'].append('initial')
    session_state['next_actions'] = ['validate_input', 'process_request']
    
    print(f"Updated workflow: {session_state['current_step']}")
    print("✅ Advanced state demonstration completed")


if __name__ == "__main__":
    demonstrate_advanced_state()