"""
Solution: Prompt Engineering Techniques
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


# Solution demonstrations
print("=" * 60)
print("Prompt Engineering Solutions")
print("=" * 60)

# Solution 1: Improved zero-shot
print("\n1. Zero-Shot with Better Formatting:")
print(
    get_completion(
        "Classify sentiment as Positive/Negative/Neutral: 'I absolutely love this product!'"
    )
)

# Solution 2: More structured few-shot
print("\n2. Few-Shot with Clearer Format:")
print(
    get_completion(
        """Convert to JSON:

Input: "Alice - Engineer - Google" → {"name": "Alice", "role": "Engineer", "company": "Google"}
Input: "Bob - Designer - Apple" → {"name": "Bob", "role": "Designer", "company": "Apple"}
Input: "Carol - Manager - Amazon" →""",
        temperature=0.3,
    )
)

# Solution 3: Clearer CoT
print("\n3. Chain of Thought - Explicit Steps:")
print(
    get_completion(
        """Calculate step by step:
- Item price: $10 for 3 items
- Price per item: ?
- Cost for 15 items: ?"""
    )
)

# Solution 4: Role with constraints
print("\n4. Role Prompting - Python Expert:")
print(
    get_completion(
        """You are a Python expert known for clear explanations.
Explain decorators in 2-3 sentences using a simple analogy."""
    )
)

# Solution 5: Structured output
print("\n5. Structured Output - Python List:")
print(get_completion("List Python, Java, Go. Format as: 1. Language (Year) - Paradigm"))

print("\n" + "=" * 60)
print("Solutions completed!")
print("=" * 60)
