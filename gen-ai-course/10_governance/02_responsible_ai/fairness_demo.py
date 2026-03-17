"""
Responsible AI Demo - Fairness & Bias Detection

This script demonstrates implementing fairness metrics and bias detection.
"""

import json
from typing import List, Dict
from collections import Counter

# Example data: predictions by group
PREDICTIONS = {
    "group_a": [
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "positive", "actual": "negative", "true_positive": False},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "negative", "actual": "negative", "true_positive": True},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "negative", "actual": "positive", "true_positive": False},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "positive", "actual": "negative", "true_positive": False},
    ],
    "group_b": [
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "negative", "actual": "negative", "true_positive": True},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "negative", "actual": "negative", "true_positive": True},
        {"prediction": "positive", "actual": "negative", "true_positive": False},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "negative", "actual": "negative", "true_positive": True},
        {"prediction": "positive", "actual": "positive", "true_positive": True},
        {"prediction": "negative", "actual": "positive", "true_positive": False},
        {"prediction": "negative", "actual": "negative", "true_positive": True},
    ],
}


def calculate_demographic_parity(predictions: List[Dict]) -> float:
    """Calculate demographic parity (positive rate)."""
    positive_count = sum(1 for p in predictions if p["prediction"] == "positive")
    return positive_count / len(predictions)


def calculate_equalized_odds(predictions: List[Dict], actual_outcome: str) -> float:
    """Calculate true positive rate for a specific actual outcome."""
    relevant = [p for p in predictions if p["actual"] == actual_outcome]
    if not relevant:
        return 0.0
    true_positives = sum(1 for p in relevant if p["true_positive"])
    return true_positives / len(relevant)


def calculate_disparate_impact(
    predictions_a: List[Dict], predictions_b: List[Dict]
) -> float:
    """Calculate disparate impact ratio."""
    rate_a = calculate_demographic_parity(predictions_a)
    rate_b = calculate_demographic_parity(predictions_b)

    if rate_b == 0:
        return 0.0

    return min(rate_a, rate_b) / max(rate_a, rate_b)


# Demo execution
if __name__ == "__main__":
    print("=" * 60)
    print("Fairness Metrics Demo")
    print("=" * 60)

    # Calculate metrics
    rate_a = calculate_demographic_parity(PREDICTIONS["group_a"])
    rate_b = calculate_demographic_parity(PREDICTIONS["group_b"])

    print(f"\nDemographic Parity:")
    print(f"  Group A positive rate: {rate_a:.2%}")
    print(f"  Group B positive rate: {rate_b:.2%}")

    # Calculate disparate impact
    di = calculate_disparate_impact(PREDICTIONS["group_a"], PREDICTIONS["group_b"])
    print(f"\nDisparate Impact Ratio: {di:.2%}")

    # Check fairness (typically > 80% is considered fair)
    is_fair = di >= 0.8
    print(f"Passes 80% rule: {is_fair}")

    # Equalized odds
    tpr_a = calculate_equalized_odds(PREDICTIONS["group_a"], "positive")
    tpr_b = calculate_equalized_odds(PREDICTIONS["group_b"], "positive")

    print(f"\nTrue Positive Rates:")
    print(f"  Group A: {tpr_a:.2%}")
    print(f"  Group B: {tpr_b:.2%}")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
