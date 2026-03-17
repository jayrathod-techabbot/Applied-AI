"""
Exercise: Introduction to Generative AI

This exercise introduces you to basic LLM interactions using the OpenAI API.
"""

import os
from openai import OpenAI

# Load API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_completion(prompt: str, model: str = "gpt-4", temperature: float = 0.7) -> str:
    """
    Get a completion from the OpenAI API.

    Args:
        prompt: The input prompt
        model: The model to use
        temperature: Controls randomness (0-2)

    Returns:
        The model's response
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content


# Exercise 1: Basic text generation
print("=" * 50)
print("Exercise 1: Basic Text Generation")
print("=" * 50)

prompt1 = "Explain what Generative AI is in simple terms."
response1 = get_completion(prompt1)
print(f"Prompt: {prompt1}")
print(f"Response: {response1}\n")

# Exercise 2: Using temperature to control creativity
print("=" * 50)
print("Exercise 2: Temperature Effect")
print("=" * 50)

prompt2 = "Write a short story about a robot."

print("\nLow temperature (0.2) - More focused:")
response_low = get_completion(prompt2, temperature=0.2)
print(response_low)

print("\nHigh temperature (1.0) - More creative:")
response_high = get_completion(prompt2, temperature=1.0)
print(response_high)

# Exercise 3: Few-shot learning
print("=" * 50)
print("Exercise 3: Few-shot Learning")
print("=" * 50)

few_shot_prompt = """Convert the following to JSON format:

Apple - Red Fruit - Delicious
Orange - Orange Fruit - Tangy

Banana -"""
response3 = get_completion(few_shot_prompt, temperature=0.3)
print(f"Prompt:\n{few_shot_prompt}")
print(f"\nResponse:\n{response3}")

# Exercise 4: Chain of thought
print("=" * 50)
print("Exercise 4: Chain of Thought")
print("=" * 50)

cot_prompt = """Solve this step by step:
If a train travels 60 mph for 2 hours, how far does it go?"""
response4 = get_completion(cot_prompt)
print(f"Prompt: {cot_prompt}")
print(f"\nResponse:\n{response4}")

print("\n" + "=" * 50)
print("Exercises completed!")
print("=" * 50)
