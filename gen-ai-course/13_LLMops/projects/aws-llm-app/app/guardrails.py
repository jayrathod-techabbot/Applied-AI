"""Input & output guardrails in a single module."""
import re
import logging
from dataclasses import dataclass, field
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── PII patterns ─────────────────────────────────────────────────────────────
_PII = {
    "email":       r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone":       r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn":         r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
}

# ── Prompt injection patterns ─────────────────────────────────────────────────
_INJECTIONS = [
    r"ignore (previous|all|above) instructions",
    r"forget (your|all) (instructions|context|prompt)",
    r"you are now",
    r"jailbreak",
    r"developer mode",
    r"(bypass|override|disregard) (your )?(safety|guidelines|rules)",
]

# ── Sensitive data that must never appear in output ───────────────────────────
_OUTPUT_SENSITIVE = {
    "api_key":        r"(sk-|AKIA)[A-Za-z0-9]{20,}",
    "private_key":    r"-----BEGIN (RSA )?PRIVATE KEY-----",
    "connection_str": r"(mongodb|postgresql|mysql)://\S+",
}


@dataclass
class GuardResult:
    passed: bool
    violations: list[str] = field(default_factory=list)
    sanitized: str = ""


def check_input(text: str) -> GuardResult:
    violations = []
    sanitized = text

    # Length
    if len(text) > settings.max_input_length:
        return GuardResult(passed=False, violations=["Input too long"], sanitized=text)

    # PII redaction
    if settings.enable_pii_detection:
        for pii_type, pattern in _PII.items():
            if re.search(pattern, sanitized, re.IGNORECASE):
                violations.append(f"PII redacted: {pii_type}")
                sanitized = re.sub(pattern, f"[{pii_type.upper()}]", sanitized, flags=re.IGNORECASE)

    # Prompt injection — block immediately
    for pattern in _INJECTIONS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning("Prompt injection detected", extra={"pattern": pattern})
            return GuardResult(passed=False, violations=["Prompt injection attempt detected"], sanitized=sanitized)

    return GuardResult(passed=True, violations=violations, sanitized=sanitized)


def check_output(text: str) -> GuardResult:
    violations = []
    sanitized = text

    # Sensitive data leak
    for data_type, pattern in _OUTPUT_SENSITIVE.items():
        if re.search(pattern, sanitized):
            violations.append(f"Sensitive data redacted: {data_type}")
            sanitized = re.sub(pattern, f"[REDACTED_{data_type.upper()}]", sanitized)

    # XSS
    if re.search(r"<script[\s>]", sanitized, re.IGNORECASE):
        violations.append("Script injection removed")
        sanitized = re.sub(r"<script[^>]*>.*?</script>", "[REMOVED]", sanitized, flags=re.IGNORECASE | re.DOTALL)

    passed = not any("redacted" in v.lower() for v in violations)
    return GuardResult(passed=passed, violations=violations, sanitized=sanitized if sanitized != text else text)
