"""
Exercise: Responsible AI Implementation

This exercise demonstrates implementing responsible AI practices.
"""

from typing import List, Dict
from collections import Counter

print("=" * 60)
print("Responsible AI - Exercises")
print("=" * 60)

# Exercise 1: Bias Detection
print("\n1. Simple Bias Detection")
print("-" * 40)

# Sample data with potential bias
outputs = [
    {"text": "The engineer is skilled", "gender": "neutral"},
    {"text": "The nurse is caring", "gender": "neutral"},
    {"text": "The CEO is ambitious", "gender": "male"},
    {"text": "The secretary is organized", "gender": "female"},
    {"text": "The doctor is competent", "gender": "neutral"},
]

# Check for gender associations
gender_associations = {}
for item in outputs:
    print(f"Text: {item['text']}")

# Exercise 2: Fairness Metrics
print("\n2. Calculating Fairness Metrics")
print("-" * 40)

# Simulated predictions
group_a_results = {"positive": 80, "total": 100}
group_b_results = {"positive": 70, "total": 100}

# Calculate demographic parity
rate_a = group_a_results["positive"] / group_a_results["total"]
rate_b = group_b_results["positive"] / group_b_results["total"]

print(f"Group A positive rate: {rate_a:.2%}")
print(f"Group B positive rate: {rate_b:.2%}")
print(f"Parity ratio: {min(rate_a, rate_b) / max(rate_a, rate_b):.2f}")

# Exercise 3: Transparency Checklist
print("\n3. Transparency Checklist")
print("-" * 40)

checklist = [
    "Model purpose and capabilities documented",
    "Limitations clearly stated",
    "Decision rationale available",
    "Human oversight available",
    "Data sources documented",
    "Performance metrics published",
]

for i, item in enumerate(checklist, 1):
    print(f"{i}. {item}")

# Exercise 4: Bias Mitigation Strategy
print("\n4. Bias Mitigation Strategy")
print("-" * 40)

strategies = [
    ("Data Collection", "Use diverse, representative data"),
    ("Pre-processing", "Reweight or resample data"),
    ("In-processing", "Add fairness constraints"),
    ("Post-processing", "Adjust thresholds"),
    ("Monitoring", "Track fairness metrics"),
]

print("Strategy | Approach")
print("-" * 40)
for strategy, approach in strategies:
    print(f"{strategy:15} | {approach}")

# Exercise 5: Creating an AI disclosure
print("\n5. AI Disclosure Template")
print("-" * 40)

disclosure = """
AI ASSISTANT DISCLOSURE

- This response was generated using AI technology
- Human review is available upon request
- AI may produce inaccurate information
- Contact [email] for concerns

Last updated: [Date]
"""
print(disclosure)

print("\n" + "=" * 60)
print("Exercises completed!")
print("=" * 60)
