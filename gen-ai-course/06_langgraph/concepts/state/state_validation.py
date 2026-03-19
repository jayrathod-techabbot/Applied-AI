#!/usr/bin/env python3
"""
State Validation - LangGraph Core Concept

This file demonstrates state validation techniques to ensure data integrity
and type safety in LangGraph applications.

Key Concepts:
- State structure validation
- Type checking
- Business rule validation
- Validation utilities
"""

from typing import TypedDict, List, Dict, Any, Union
from datetime import datetime


class ValidationState(TypedDict):
    """State for validation examples."""
    session_id: str
    user_input: str
    confidence_score: float
    validation_errors: List[str]


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
        
        if 'user_input' in state:
            if len(state['user_input']) > 10000:  # Max 10k characters
                errors.append("Input text too long (max 10000 characters)")
        
        return errors


def create_validation_example():
    """
    Create an example state for validation.
    
    Returns:
        ValidationState: Example state with validation issues
    """
    return ValidationState(
        session_id="test_session",
        user_input="This is a very long input text that exceeds the maximum allowed length by far",
        confidence_score=1.5,  # Invalid: > 1
        validation_errors=[]
    )


def demonstrate_state_validation():
    """
    Demonstrate state validation techniques.
    """
    print("🎯 State Validation Demonstration")
    print("=" * 35)
    
    # Create state with validation issues
    state = create_validation_example()
    print(f"State to validate: {state['session_id']}")
    
    # Validate required fields
    required_fields = ['session_id', 'user_input', 'confidence_score']
    missing = StateValidator.validate_required_fields(state, required_fields)
    print(f"Missing fields: {missing}")
    
    # Validate business rules
    business_errors = StateValidator.validate_business_rules(state)
    print(f"Business rule violations: {business_errors}")
    
    # Combine validation results
    state['validation_errors'] = missing + business_errors
    print(f"Total validation errors: {len(state['validation_errors'])}")
    print("✅ State validation demonstration completed")


if __name__ == "__main__":
    demonstrate_state_validation()