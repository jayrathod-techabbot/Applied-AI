"""
Exercise: AI Compliance Implementation

This exercise demonstrates implementing compliance measures.
"""

from enum import Enum


class RiskLevel(Enum):
    UNACCEPTABLE = "Unacceptable"
    HIGH = "High"
    LIMITED = "Limited"
    MINIMAL = "Minimal"


class AICompliance:
    """Simple compliance tracking."""

    def __init__(self):
        self.systems = []

    def classify_system(self, use_case: str) -> RiskLevel:
        """Classify AI system by risk."""
        high_risk = ["hiring", "credit", "healthcare", "law"]

        for risk in high_risk:
            if risk in use_case.lower():
                return RiskLevel.HIGH

        return RiskLevel.MINIMAL

    def get_requirements(self, risk_level: RiskLevel) -> list:
        """Get compliance requirements."""
        requirements = {
            RiskLevel.HIGH: [
                "Risk assessment",
                "Data governance",
                "Technical documentation",
                "Human oversight",
                "Accuracy testing",
            ],
            RiskLevel.LIMITED: [
                "Transparency disclosure",
                "Age verification (if applicable)",
            ],
            RiskLevel.MINIMAL: [],
        }
        return requirements.get(risk_level, [])


print("=" * 60)
print("AI Compliance - Exercises")
print("=" * 60)

# Exercise 1: Risk Classification
print("\n1. AI System Risk Classification")
print("-" * 40)

compliance = AICompliance()

use_cases = [
    "AI-powered hiring tool",
    "Customer service chatbot",
    "Product recommendation engine",
    "Credit scoring system",
]

for use_case in use_cases:
    risk = compliance.classify_system(use_case)
    print(f"{use_case}: {risk.value}")

# Exercise 2: Compliance Requirements
print("\n2. Compliance Requirements")
print("-" * 40)

for use_case in use_cases:
    risk = compliance.classify_system(use_case)
    reqs = compliance.get_requirements(risk)
    print(f"\n{use_case}:")
    for req in reqs:
        print(f"  - {req}")

# Exercise 3: GDPR Checklist
print("\n3. GDPR Compliance Checklist")
print("-" * 40)

gdpr_items = [
    "Lawful basis for processing",
    "Privacy notice published",
    "Data subject rights process",
    "Data protection impact assessment",
    "Security measures in place",
    "Data retention policy",
    "Breach notification procedure",
]

for i, item in enumerate(gdpr_items, 1):
    print(f"{i}. {item}")

# Exercise 4: Documentation Requirements
print("\n4. Documentation Requirements for High-Risk AI")
print("-" * 40)

docs = [
    "System purpose and scope",
    "Technical specifications",
    "Training data description",
    "Expected performance",
    "Known limitations",
    "Risk assessment",
    "Human oversight measures",
]

for doc in docs:
    print(f"- {doc}")

print("\n" + "=" * 60)
print("Exercises completed!")
print("=" * 60)
