"""Input guardrails: PII detection, toxicity filtering, prompt injection detection."""
import re
import logging
from app.config import get_settings
from app.models import GuardrailResult

logger = logging.getLogger(__name__)
settings = get_settings()

# PII patterns
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"forget (previous|all|above|your) (instructions|context|prompt)",
    r"you are now",
    r"act as (a |an )?(different|new|unrestricted)",
    r"jailbreak",
    r"(disregard|bypass|override) (your )?(safety|guidelines|rules|restrictions)",
    r"do anything now",
    r"developer mode",
    r"<\|.*?\|>",  # Token injection attempt
    r"\[SYSTEM\]",  # System prompt injection
]

# Banned topics / high-risk keywords
BANNED_KEYWORDS = [
    "synthesize weapon", "make bomb", "create malware",
    "hack into", "steal credentials", "bypass authentication",
]


class InputGuardrail:
    """Validates and sanitizes LLM inputs."""

    def __init__(self):
        self.pii_patterns = {k: re.compile(v, re.IGNORECASE) for k, v in PII_PATTERNS.items()}
        self.injection_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    def check(self, text: str) -> GuardrailResult:
        violations = []
        redacted = text

        # 1. Length check
        if len(text) > settings.max_input_length:
            violations.append(f"Input exceeds maximum length of {settings.max_input_length} characters")
            return GuardrailResult(passed=False, violations=violations)

        # 2. PII detection & redaction
        if settings.enable_pii_detection:
            redacted, pii_violations = self._redact_pii(redacted)
            violations.extend(pii_violations)

        # 3. Prompt injection detection
        injection_violations = self._detect_prompt_injection(text)
        if injection_violations:
            violations.extend(injection_violations)
            logger.warning("Prompt injection attempt detected", extra={"violations": injection_violations})
            return GuardrailResult(passed=False, violations=violations, redacted_content=redacted)

        # 4. Banned content check
        banned_violations = self._check_banned_content(text)
        if banned_violations:
            violations.extend(banned_violations)
            return GuardrailResult(passed=False, violations=violations, redacted_content=redacted)

        # 5. Empty / gibberish check
        if self._is_gibberish(text):
            violations.append("Input appears to be gibberish or non-meaningful text")

        passed = len([v for v in violations if "PII" not in v]) == 0
        return GuardrailResult(
            passed=passed,
            violations=violations,
            redacted_content=redacted if redacted != text else None,
        )

    def _redact_pii(self, text: str) -> tuple[str, list[str]]:
        violations = []
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                violations.append(f"PII detected and redacted: {pii_type} ({len(matches)} instance(s))")
                text = pattern.sub(f"[REDACTED_{pii_type.upper()}]", text)
        return text, violations

    def _detect_prompt_injection(self, text: str) -> list[str]:
        violations = []
        for pattern in self.injection_patterns:
            if pattern.search(text):
                violations.append(f"Potential prompt injection detected: '{pattern.pattern}'")
        return violations

    def _check_banned_content(self, text: str) -> list[str]:
        violations = []
        text_lower = text.lower()
        for keyword in BANNED_KEYWORDS:
            if keyword in text_lower:
                violations.append(f"Banned content detected: '{keyword}'")
        return violations

    def _is_gibberish(self, text: str) -> bool:
        words = text.split()
        if not words:
            return True
        avg_word_len = sum(len(w) for w in words) / len(words)
        return avg_word_len > 20 or (len(words) == 1 and len(text) > 50)
