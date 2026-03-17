"""
Solution: Data Analysis with Prompts
"""

import os
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}], temperature=0.3
    )
    return response.choices[0].message.content


# Sample data
sales_data = pd.DataFrame(
    {
        "product": ["Laptop", "Phone", "Tablet", "Headphones", "Watch"],
        "sales": [150, 200, 80, 120, 90],
        "revenue": [150000, 80000, 32000, 12000, 18000],
    }
)

print("=" * 60)
print("Data Analysis - Solutions")
print("=" * 60)

# Solution 1: Better structured analysis
print("\n1. Structured Analysis:")
prompt1 = (
    """Analyze and return as markdown table:
- Top performing product
- Total revenue
- Average sales per product
- Recommendation

Data:
"""
    + sales_data.to_string()
)
print(analyze(prompt1))

# Solution 2: Sentiment with scoring
print("\n2. Sentiment with Scores:")
reviews = ["Great product!", "Terrible.", "Average experience."]
prompt2 = "Rate each sentiment -5 to +5:\n" + "\n".join(reviews)
print(analyze(prompt2))

# Solution 3: Structured JSON output
print("\n3. JSON Output:")
prompt3 = f"""Create JSON array from:
{sales_data.to_string()}
Add calculated field: revenue_per_sale"""
print(analyze(prompt3))

print("\n" + "=" * 60)
print("Solutions completed!")
print("=" * 60)
