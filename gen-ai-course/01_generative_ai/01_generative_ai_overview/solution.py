"""
Solution: Introduction to Generative AI

This is the solution file showing expected outputs.
"""

import os
from openai import OpenAI

# Load API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_completion(prompt: str, model: str = "gpt-4", temperature: float = 0.7) -> str:
    """
    Get a completion from the OpenAI API.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content


# Solution demonstrations
print("=" * 50)
print("Solution Examples")
print("=" * 50)

# Example 1: Basic explanation
print("\n1. Basic Generative AI Explanation:")
print(get_completion("Explain what Generative AI is in simple terms."))

# Example 2: Temperature comparison
print("\n2. Temperature = 0.2 (Focused):")
print(get_completion("Write a haiku about technology.", temperature=0.2))

print("\n3. Temperature = 1.0 (Creative):")
print(get_completion("Write a haiku about technology.", temperature=1.0))

# Example 3: Structured output
print("\n4. JSON Format Output:")
print(
    get_completion(
        """Create a JSON object with:
- name: "Python"
- type: "Programming Language"
- year: 1991
Add one more: name: "JavaScript", type: "Programming Language", year: 1995""",
        temperature=0.3,
    )
)

print("\n" + "=" * 50)
print("Solutions completed!")
print("=" * 50)
