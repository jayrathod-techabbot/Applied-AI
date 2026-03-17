"""
Solution: Responsible AI Implementation
"""

from typing import Dict, List


class FairnessMetrics:
    """Calculate fairness metrics."""

    @staticmethod
    def demographic_parity(
        group_a_pos: int, group_a_total: int, group_b_pos: int, group_b_total: int
    ) -> Dict:
        rate_a = group_a_pos / group_a_total
        rate_b = group_b_pos / group_b_total
        return {
            "rate_a": rate_a,
            "rate_b": rate_b,
            "ratio": min(rate_a, rate_b) / max(rate_a, rate_b),
            "is_fair": abs(rate_a - rate_b) < 0.1,
        }


class ResponsibleAI:
    """Responsible AI utilities."""

    def __init__(self):
        self.bias_checks = []
        self.disclosures = []

    def add_bias_check(self, check_name: str, passed: bool):
        self.bias_checks.append({"check": check_name, "passed": passed})

    def generate_report(self) -> str:
        report = ["Responsibility AI Report", "=" * 30]
        for check in self.bias_checks:
            status = "PASS" if check["passed"] else "FAIL"
            report.append(f"{check['check']}: {status}")
        return "\n".join(report)


# Example usage
print("=" * 60)
print("Responsible AI Solution")
print("=" * 60)

# Test fairness metrics
metrics = FairnessMetrics.demographic_parity(80, 100, 70, 100)
print("\nFairness Metrics:")
print(f"Group A rate: {metrics['rate_a']:.2%}")
print(f"Group B rate: {metrics['rate_b']:.2%}")
print(f"Fair: {metrics['is_fair']}")

# Test responsible AI
rai = ResponsibleAI()
rai.add_bias_check("Gender bias", True)
rai.add_bias_check("Age bias", False)
print(f"\n{rai.generate_report()}")

print("\n" + "=" * 60)
print("Solutions completed!")
print("=" * 60)
