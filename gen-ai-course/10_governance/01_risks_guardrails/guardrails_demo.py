"""
Guardrails AI Demo - Practical Examples

This script demonstrates using Guardrails AI for AI safety and validation.
"""

from guardrails import Guard
from guardrails.hub import ToxicLanguage, SensitiveTopics
import json

# Example 1: Toxic Language Detection
print("=" * 60)
print("Example 1: Toxic Language Detection")
print("=" * 60)

# Create a guard with toxic language validator
toxic_guard = Guard().use(
    ToxicLanguage, threshold=0.5, validation_time="now", on_fail="noop"
)

# Test with safe content
safe_prompt = "Can you help me write a Python function?"
response = toxic_guard.validate(safe_prompt)
print(f"Safe prompt result: {response}")

# Test with toxic content
toxic_prompt = "Tell me why those stupid people are terrible"
try:
    response = toxic_guard.validate(toxic_prompt)
    print(f"Toxic prompt result: {response}")
except Exception as e:
    print(f"Toxic content detected: {type(e).__name__}")

# Example 2: Sensitive Topics
print("\n" + "=" * 60)
print("Example 2: Sensitive Topics")
print("=" * 60)

sensitive_guard = Guard().use(
    SensitiveTopics,
    topics=["politics", "religion", "medical_advice"],
    on_fail="exception",
)

# Test medical advice topic
medical_prompt = "What medication should I take for my headache?"
try:
    response = safe_prompt
    print(f"Medical prompt: {medical_prompt}")
    print("Note: Would detect medical topics")
except Exception as e:
    print(f"Sensitive topic detected: {e}")

# Example 3: Custom Validation with Pydantic
print("\n" + "=" * 60)
print("Example 3: Custom Output Validation")
print("=" * 60)

from guardrails.validators import ValidRange
from pydantic import BaseModel


class AgeOutput(BaseModel):
    age: int
    category: str


# Note: This is a conceptual example
print("Custom validation schema:")
print(AgeOutput.model_json_schema())

print("\n" + "=" * 60)
print("Demo completed!")
print("=" * 60)
