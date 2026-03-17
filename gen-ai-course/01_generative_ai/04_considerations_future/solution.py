"""
Solution: Ethical AI & Future Considerations
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
print("Ethical AI - Solution Examples")
print("=" * 60)

# Example 1: Risk assessment framework
print("\n1. AI Risk Assessment Framework:")
print(
    get_completion(
        "Create a simple risk assessment checklist for deploying an AI chatbot. List 5 key items."
    )
)

# Example 2: Mitigation strategies
print("\n2. Bias Mitigation Strategies:")
print(get_completion("List 3 strategies to reduce bias in AI-generated content."))

# Example 3: Transparency guidelines
print("\n3. AI Transparency Guidelines:")
print(
    get_completion("What should an AI disclosure policy include? List 4 key elements.")
)

print("\n" + "=" * 60)
print("Solutions completed!")
print("=" * 60)
