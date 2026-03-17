"""
Exercise: Prompt Engineering Techniques

This exercise demonstrates various prompt engineering techniques.
"""

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_completion(prompt: str, **kwargs) -> str:
    response = client.chat.completions.create(
        model=kwargs.get("model", "gpt-4"),
        messages=[{"role": "user", "content": prompt}],
        temperature=kwargs.get("temperature", 0.7),
    )
    return response.choices[0].message.content


print("=" * 60)
print("Prompt Engineering Exercises")
print("=" * 60)

# Exercise 1: Zero-shot prompt
print("\n1. Zero-Shot Prompting")
print("-" * 40)
prompt1 = "Classify this sentiment: 'I absolutely love this product!'"
response1 = get_completion(prompt1)
print(f"Prompt: {prompt1}")
print(f"Response: {response1}\n")

# Exercise 2: Few-shot prompting
print("\n2. Few-Shot Prompting")
print("-" * 40)
prompt2 = """Convert to JSON with keys: name, role, company

John - Software Engineer - Google
Sarah - Product Manager - Meta
Michael -"""
response2 = get_completion(prompt2, temperature=0.3)
print(f"Prompt:\n{prompt2}")
print(f"Response:\n{response2}\n")

# Exercise 3: Chain of thought
print("\n3. Chain of Thought")
print("-" * 40)
prompt3 = """Solve step by step:
A store sells 3 items for $10. How much would 15 items cost?"""
response3 = get_completion(prompt3)
print(f"Prompt: {prompt3}")
print(f"Response:\n{response3}\n")

# Exercise 4: Role prompting
print("\n4. Role Prompting")
print("-" * 40)
prompt4 = (
    """You are a Python expert.
Explain what a decorator is in Python.""",
)
response4 = get_completion(prompt4[0])
print(f"Prompt: {prompt4[0]}")
print(f"Response:\n{response4}\n")

# Exercise 5: Structured output
print("\n5. Structured Output")
print("-" * 40)
prompt5 = (
    """List 3 programming languages.
Return as a markdown table with columns: Language, Paradigm, Year""",
)
response5 = get_completion(prompt5[0], temperature=0.5)
print(f"Prompt: {prompt5[0]}")
print(f"Response:\n{response5}\n")

# Exercise 6: Constrained prompting
print("\n6. Constrained Prompting")
print("-" * 40)
prompt6 = (
    """Write a haiku about artificial intelligence.
Requirements:
- Exactly 3 lines
- 5-7-5 syllable pattern
- Include the word 'intelligence'""",
)
response6 = get_completion(prompt6[0], temperature=0.8)
print(f"Prompt: {prompt6[0]}")
print(f"Response:\n{response6}\n")

print("=" * 60)
print("Exercises completed!")
print("=" * 60)
