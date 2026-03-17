"""
Exercise: Data Analysis with Prompts

This exercise demonstrates using LLMs for data analysis tasks.
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

customer_reviews = [
    "This product is amazing! Best purchase ever.",
    "Terrible quality, broke after one week.",
    "It's okay, not great but not bad either.",
    "Absolutely love it! Would recommend to everyone.",
    "Very disappointed. Waste of money.",
    "Decent product for the price.",
    "Exceeded my expectations!",
    "Not worth the price. Returning it.",
]

print("=" * 60)
print("Data Analysis with Prompts - Exercises")
print("=" * 60)

# Exercise 1: Basic analysis
print("\n1. Basic Data Analysis")
print("-" * 40)
prompt1 = f"Analyze this sales data and identify trends:\n{sales_data.to_string()}"
response1 = analyze(prompt1)
print(response1)

# Exercise 2: Sentiment analysis
print("\n2. Sentiment Analysis")
print("-" * 40)
prompt2 = f"Analyze sentiment for each review. Return as list:\n{chr(10).join(customer_reviews)}"
response2 = analyze(prompt2)
print(response2)

# Exercise 3: Data transformation
print("\n3. Data Transformation")
print("-" * 40)
prompt3 = f"Convert this data to JSON with fields: product, sales, revenue, avg_price:\n{sales_data.to_string()}"
response3 = analyze(prompt3)
print(response3)

# Exercise 4: Insights extraction
print("\n4. Extracting Insights")
print("-" * 40)
prompt4 = (
    f"What business insights can you extract from this data?\n{sales_data.to_string()}"
)
response4 = analyze(prompt4)
print(response4)

# Exercise 5: Categorization
print("\n5. Data Categorization")
print("-" * 40)
categories = ["Electronics", "Accessories", "Services"]
products = ["Laptop", "Phone case", "Cloud storage", "Tablet", "Charger"]
prompt5 = f"Categorize these products: {products}\nInto: {categories}"
response5 = analyze(prompt5)
print(response5)

print("\n" + "=" * 60)
print("Exercises completed!")
print("=" * 60)
