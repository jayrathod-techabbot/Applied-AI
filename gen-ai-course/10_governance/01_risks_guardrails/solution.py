"""
Solution: AI Risks & Guardrails
"""

import re
from enum import Enum


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Guardrail:
    """Base guardrail class."""

    def check(self, input_text: str) -> tuple[bool, str]:
        raise NotImplementedError


class KeywordGuardrail(Guardrail):
    """Keyword-based guardrail."""

    def __init__(self, keywords: list[str], block: bool = True):
        self.keywords = keywords
        self.block = block

    def check(self, input_text: str) -> tuple[bool, str]:
        for keyword in self.keywords:
            if keyword.lower() in input_text.lower():
                msg = f"Blocked: contains '{keyword}'"
                return self.block, msg
        return False, ""


class OutputGuardrail:
    """Output filtering guardrail."""

    def __init__(self):
        self.filters = [
            KeywordGuardrail(["harmful", "dangerous"], block=True),
            KeywordGuardrail(["illegal"], block=True),
        ]

    def filter(self, output: str) -> str:
        for f in self.filters:
            blocked, msg = f.check(output)
            if blocked:
                return f"FILTERED: {msg}"
        return output


# Example usage
print("=" * 60)
print("Guardrail Solution Examples")
print("=" * 60)

# Test keyword guardrail
guardrail = KeywordGuardrail(["hack", "exploit"])
blocked, msg = guardrail.check("How to hack a system")
print(f"\nTest 1 - Blocked: {blocked}, Message: {msg}")

blocked, msg = guardrail.check("Explain programming")
print(f"Test 2 - Blocked: {blocked}, Message: {msg}")

# Test output guardrail
output_filter = OutputGuardrail()
result = output_filter.filter("This is dangerous content")
print(f"\nOutput filter result: {result}")

print("\n" + "=" * 60)
print("Solutions completed!")
print("=" * 60)
