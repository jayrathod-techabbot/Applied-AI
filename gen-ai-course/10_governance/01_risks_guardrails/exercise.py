"""
Exercise: AI Risks & Guardrails

This exercise demonstrates implementing AI safety guardrails.
"""

import os
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple guardrail functions

BLOCKED_KEYWORDS = ["hack", "exploit", "attack", "illegal", "harmful"]


def input_guardrail(user_input: str) -> tuple[bool, str]:
    """Check if input contains blocked content."""
    for keyword in BLOCKED_KEYWORDS:
        if keyword.lower() in user_input.lower():
            return True, f"Input blocked: contains blocked keyword '{keyword}'"
    return False, ""


def filter_guardrail(output: str) -> tuple[bool, str]:
    """Check if output contains unwanted content."""
    unwanted = ["harmful", "dangerous", "illegal"]
    for word in unwanted:
        if word.lower() in output.lower():
            return True, f"Output filtered: contains '{word}'"
    return False, ""


def get_completion_safe(prompt: str) -> str:
    """Safe completion with guardrails."""
    # Input guardrail
    blocked, message = input_guardrail(prompt)
    if blocked:
        return f"BLOCKED: {message}"

    # Call API
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}], temperature=0.3
    )
    output = response.choices[0].message.content

    # Output guardrail
    blocked, message = filter_guardrail(output)
    if blocked:
        return f"FILTERED: {message}"

    return output


print("=" * 60)
print("AI Risks & Guardrails - Exercises")
print("=" * 60)

# Exercise 1: Basic input guardrail
print("\n1. Testing Input Guardrail")
print("-" * 40)
test_input = "How to hack a computer?"
result = get_completion_safe(test_input)
print(f"Input: {test_input}")
print(f"Result: {result}")

# Exercise 2: Safe content
print("\n2. Safe Content Passes")
print("-" * 40)
test_input = "Explain how photosynthesis works"
result = get_completion_safe(test_input)
print(f"Input: {test_input}")
print(f"Result: {result[:200]}...")

# Exercise 3: Risk identification
print("\n3. Identifying Risks")
print("-" * 40)
risks = [
    "User asks for harmful instructions",
    "AI generates false medical advice",
    "Model reveals private information",
]
for risk in risks:
    print(f"- {risk}")

# Exercise 4: Implementing a risk matrix
print("\n4. Risk Assessment Matrix")
print("-" * 40)
risks = [
    ("Hallucinations", "Medium", "Verify with sources"),
    ("Bias in Output", "High", "Audit training data"),
    ("Privacy Leak", "Critical", "Input filtering"),
]
print("Risk | Severity | Mitigation")
print("-" * 40)
for risk, severity, mitigation in risks:
    print(f"{risk:15} | {severity:8} | {mitigation}")

print("\n" + "=" * 60)
print("Exercises completed!")
print("=" * 60)
