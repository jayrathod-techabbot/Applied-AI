#!/usr/bin/env python3
"""
LangGraph State Management - Core Concept

This file demonstrates the fundamental concept of State Management in LangGraph.
State is the backbone of LangGraph applications - it flows through the graph
and carries information between nodes.

Key Concepts Covered:
- State definition with TypedDict
- State validation and type safety
- State persistence strategies
- Memory optimization techniques
- State lifecycle management
"""

from typing import TypedDict, List, Optional, Dict, Any, Union
from datetime import datetime
import json
import pickle


# ============================================================================
# 1. BASIC STATE DEFINITION
# ============================================================================

class SimpleState(TypedDict):
    """
    Basic State Example:
    
    The simplest form of state - a dictionary-like structure that flows
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


# ============================================================================
# 2. ADVANCED STATE SCHEMAS
# ============================================================================

class UserSessionState(TypedDict):
    """
    User Session State Example:
    
    A more comprehensive state structure suitable for multi-user applications.
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
    
    # Results and outputs
    intermediate_results: List[Dict[str, Any]]  # Partial results
    final_output: Optional[str]   # Final result
    confidence_score: Optional[float]  # Quality/confidence of result


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
    validation_errors: List[str]
    
    # Workflow tracking
    processing_steps: List[str]
    current_step: str
    estimated_completion: Optional[datetime]


# ============================================================================
# 3. STATE VALIDATION
# ============================================================================

class StateValidator:
    """
    State Validation Utilities:
    
    Provides methods for validating state structure and data integrity.
    Essential for maintaining data quality in production applications.
    """
    
    @staticmethod
    def validate_required_fields(state: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate that state contains all required fields.
        
        Args:
            state: The state dictionary to validate
            required_fields: List of field names that must be present
            
        Returns:
            List of missing field names
        """
        missing_fields = []
        for field in required_fields:
            if field not in state or state[field] is None:
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_field_types(state: Dict[str, Any], type_schema: Dict[str, type]) -> List[str]:
        """
        Validate that state fields have correct types.
        
        Args:
            state: The state dictionary to validate
            type_schema: Dictionary mapping field names to expected types
            
        Returns:
            List of type validation errors
        """
        errors = []
        for field, expected_type in type_schema.items():
            if field in state:
                actual_type = type(state[field])
                if not issubclass(actual_type, expected_type):
                    errors.append(f"Field '{field}': expected {expected_type}, got {actual_type}")
        return errors
    
    @staticmethod
    def validate_business_rules(state: Dict[str, Any]) -> List[str]:
        """
        Validate business-specific rules.
        
        Args:
            state: The state dictionary to validate
            
        Returns:
            List of business rule violations
        """
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
    def validate_state_completeness(state: Dict[str, Any]) -> bool:
        """
        Validate overall state completeness.
        
        Args:
            state: The state dictionary to validate
            
        Returns:
            True if state is valid, False otherwise
        """
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


# ============================================================================
# 4. STATE PERSISTENCE
# ============================================================================

class StatePersistence:
    """
    State Persistence Utilities:
    
    Handle saving and loading state for checkpointing, recovery,
    and long-running workflows.
    """
    
    @staticmethod
    def save_state_to_file(state: Dict[str, Any], file_path: str, format: str = 'json') -> None:
        """
        Save state to file.
        
        Args:
            state: The state to save
            file_path: Path to save the state
            format: Format to save in ('json' or 'pickle')
        """
        if format == 'json':
            with open(file_path, 'w') as f:
                json.dump(state, f, default=str, indent=2)
        elif format == 'pickle':
            with open(file_path, 'wb') as f:
                pickle.dump(state, f)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def load_state_from_file(file_path: str, format: str = 'json') -> Dict[str, Any]:
        """
        Load state from file.
        
        Args:
            file_path: Path to load the state from
            format: Format to load from ('json' or 'pickle')
            
        Returns:
            The loaded state dictionary
        """
        if format == 'json':
            with open(file_path, 'r') as f:
                return json.load(f)
        elif format == 'pickle':
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def serialize_state_for_database(state: Dict[str, Any]) -> str:
        """
        Serialize state to string for database storage.
        
        Args:
            state: The state to serialize
            
        Returns:
            JSON string representation of the state
        """
        return json.dumps(state, default=str)
    
    @staticmethod
    def deserialize_state_from_database(state_string: str) -> Dict[str, Any]:
        """
        Deserialize state from string retrieved from database.
        
        Args:
            state_string: JSON string representation of state
            
        Returns:
            The deserialized state dictionary
        """
        return json.loads(state_string)


# ============================================================================
# 5. STATE OPTIMIZATION
# ============================================================================

class StateOptimizer:
    """
    State Optimization Utilities:
    
    Optimize state for memory efficiency and performance.
    """
    
    @staticmethod
    def compress_state(state: Dict[str, Any], max_size_mb: int = 10) -> Dict[str, Any]:
        """
        Compress state if it exceeds size limit.
        
        Args:
            state: The state to potentially compress
            max_size_mb: Maximum size in megabytes
            
        Returns:
            Compressed state if needed, otherwise original state
        """
        import sys
        
        # Calculate state size
        state_size = sys.getsizeof(str(state))
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if state_size > max_size_bytes:
            # Remove debug info and metadata for compression
            compressed = {
                k: v for k, v in state.items() 
                if k not in ['debug_info', 'metadata', 'intermediate_results']
            }
            print(f"State compressed from {state_size} bytes to {sys.getsizeof(str(compressed))} bytes")
            return compressed
        
        return state
    
    @staticmethod
    def cleanup_state(state: Dict[str, Any], cleanup_keys: List[str]) -> Dict[str, Any]:
        """
        Remove specified keys from state to reduce memory usage.
        
        Args:
            state: The state to clean up
            cleanup_keys: List of keys to remove
            
        Returns:
            Cleaned up state
        """
        return {k: v for k, v in state.items() if k not in cleanup_keys}
    
    @staticmethod
    def create_checkpoint_state(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a checkpoint state with essential information only.
        
        Args:
            state: The current state
            
        Returns:
            Checkpoint state with minimal data
        """
        essential_keys = [
            'session_id', 'user_id', 'input_text', 'current_step',
            'completed_steps', 'final_output', 'confidence_score'
        ]
        
        checkpoint = {k: v for k, v in state.items() if k in essential_keys}
        checkpoint['checkpoint_time'] = datetime.now().isoformat()
        
        return checkpoint


# ============================================================================
# 6. STATE LIFECYCLE MANAGEMENT
# ============================================================================

class StateLifecycleManager:
    """
    State Lifecycle Management:
    
    Manage the complete lifecycle of state from creation to cleanup.
    """
    
    @staticmethod
    def create_initial_state(state_class: type, **kwargs) -> Dict[str, Any]:
        """
        Create initial state with default values.
        
        Args:
            state_class: The TypedDict class for the state
            **kwargs: Initial values to set
            
        Returns:
            Initial state dictionary
        """
        # Get default values from TypedDict
        import typing
        from typing import get_type_hints
        
        type_hints = get_type_hints(state_class)
        initial_state = {}
        
        for field, field_type in type_hints.items():
            if field in kwargs:
                initial_state[field] = kwargs[field]
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                initial_state[field] = []
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is dict:
                initial_state[field] = {}
            elif field_type is str:
                initial_state[field] = ""
            elif field_type is int:
                initial_state[field] = 0
            elif field_type is float:
                initial_state[field] = 0.0
            elif field_type is bool:
                initial_state[field] = False
            else:
                initial_state[field] = None
        
        return initial_state
    
    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely update state with new values.
        
        Args:
            state: Current state
            updates: Updates to apply
            
        Returns:
            Updated state
        """
        return {**state, **updates}
    
    @staticmethod
    def merge_states(state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two states, with state2 taking precedence.
        
        Args:
            state1: First state
            state2: Second state (higher priority)
            
        Returns:
            Merged state
        """
        merged = {**state1}
        
        for key, value in state2.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Deep merge dictionaries
                merged[key] = {**merged[key], **value}
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                # Concatenate lists
                merged[key] = merged[key] + value
            else:
                # Replace with new value
                merged[key] = value
        
        return merged


# ============================================================================
# 7. EXAMPLE USAGE AND DEMONSTRATION
# ============================================================================

def demonstrate_state_management():
    """
    Demonstrate all state management concepts with practical examples.
    """
    print("🎯 STATE MANAGEMENT DEMONSTRATION")
    print("=" * 50)
    
    # 1. Create initial state
    print("\n1. Creating Initial State:")
    initial_state = StateLifecycleManager.create_initial_state(
        UserSessionState,
        session_id="demo_session_001",
        user_id="user_123",
        session_start=datetime.now(),
        input_text="Hello, LangGraph!",
        current_step="initial"
    )
    print(f"Initial state: {initial_state}")
    
    # 2. Validate state
    print("\n2. Validating State:")
    is_valid = StateValidator.validate_state_completeness(initial_state)
    print(f"State validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # 3. Update state
    print("\n3. Updating State:")
    updated_state = StateLifecycleManager.update_state(
        initial_state,
        {
            'current_step': 'processing',
            'completed_steps': ['initial'],
            'confidence_score': 0.85
        }
    )
    print(f"Updated state step: {updated_state['current_step']}")
    
    # 4. Optimize state
    print("\n4. Optimizing State:")
    optimized_state = StateOptimizer.compress_state(updated_state, max_size_mb=1)
    print(f"State optimized: {len(str(updated_state))} -> {len(str(optimized_state))} characters")
    
    # 5. Save and load state
    print("\n5. State Persistence:")
    StatePersistence.save_state_to_file(optimized_state, "demo_state.json")
    loaded_state = StatePersistence.load_state_from_file("demo_state.json")
    print(f"State saved and loaded successfully: {loaded_state['session_id']}")
    
    # 6. Create checkpoint
    print("\n6. Creating Checkpoint:")
    checkpoint = StateOptimizer.create_checkpoint_state(loaded_state)
    print(f"Checkpoint created with {len(checkpoint)} keys")
    
    # 7. Demonstrate e-commerce state
    print("\n7. E-commerce State Example:")
    ecommerce_state = StateLifecycleManager.create_initial_state(
        ECommerceState,
        customer_id="cust_456",
        customer_name="John Doe",
        customer_email="john@example.com",
        order_id="order_789",
        items=[{"product_id": "prod_1", "quantity": 2, "price": 25.99}],
        subtotal=51.98,
        order_status="pending",
        payment_status="pending"
    )
    print(f"E-commerce state created: Order {ecommerce_state['order_id']} for {ecommerce_state['customer_name']}")
    
    print("\n✅ STATE MANAGEMENT DEMONSTRATION COMPLETED")


if __name__ == "__main__":
    """
    Run the state management demonstration.
    """
    demonstrate_state_management()