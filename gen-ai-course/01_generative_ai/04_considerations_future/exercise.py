"""
Exercise: Ethical AI & Future Considerations

This exercise explores ethical considerations and responsible AI practices.
"""

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_completion(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}], temperature=0.3
    )
    return response.choices[0].message.content


print("=" * 60)
print("Ethical AI & Future Considerations - Exercises")
print("=" * 60)

# Exercise 1: Identifying potential harms
print("\n1. Identifying Potential Harms")
print("-" * 40)
prompt1 = """What are the potential risks of using AI to generate
product reviews at scale? Consider ethical implications."""
response1 = get_completion(prompt1)
print(response1)

# Exercise 2: Bias detection
print("\n2. Bias Detection")
print("-" * 40)
prompt2 = """How might an AI model show bias in hiring decisions?
What are ways to detect and mitigate this?"""
response2 = get_completion(prompt2)
print(response2)

# Exercise 3: Responsible AI practices
print("\n3. Responsible AI Practices")
print("-" * 40)
prompt3 = """What best practices should organizations follow when
deploying AI systems for customer service?"""
response3 = get_completion(prompt3)
print(response3)

# Exercise 4: Hallucination handling
print("\n4. Handling Hallucinations")
print("-" * 40)
prompt4 = """What strategies can be used to detect and prevent
AI hallucinations in factual reporting?"""
response4 = get_completion(prompt4)
print(response4)

# Exercise 5: Future implications
print("\n5. Future Implications")
print("-" * 40)
prompt5 = """What are three emerging trends in generative AI that
will impact businesses in the next 5 years?"""
response5 = get_completion(prompt5)
print(response5)

print("\n" + "=" * 60)
print("Exercises completed!")
print("=" * 60)
