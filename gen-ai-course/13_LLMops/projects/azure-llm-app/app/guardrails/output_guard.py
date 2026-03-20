"""Output guardrails: hallucination signals, toxicity, PII leakage, format validation."""
import re
import logging
from app.config import get_settings
from app.models import GuardrailResult

logger = logging.getLogger(__name__)
settings = get_settings()

# Signals of potential hallucination
HALLUCINATION_SIGNALS = [
    r"as of my (last|latest) (update|knowledge|training)",
    r"i (don't|do not) have (access|information) (about|on|to)",
    r"i (cannot|can't) (verify|confirm|guarantee)",
    r"i (may|might) be (wrong|incorrect|mistaken)",
]

# Sensitive info patterns that should never appear in output
OUTPUT_SENSITIVE_PATTERNS = {
    "api_key": r"(sk-|key-)[A-Za-z0-9]{20,}",
    "password": r"password\s*[:=]\s*\S+",
    "connection_string": r"(Server|Data Source)=.+;",
    "private_key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
}

# Toxicity keywords (simplified; use Azure Content Safety API in production)
TOXIC_KEYWORDS = [
    "hate speech placeholder",  # Replace with actual moderation in production
]


class OutputGuardrail:
    """Validates and sanitizes LLM outputs."""

    def __init__(self):
        self.hallucination_patterns = [re.compile(p, re.IGNORECASE) for p in HALLUCINATION_SIGNALS]
        self.sensitive_patterns = {
            k: re.compile(v, re.IGNORECASE) for k, v in OUTPUT_SENSITIVE_PATTERNS.items()
        }

    def check(self, text: str, original_query: str = "") -> GuardrailResult:
        violations = []
        redacted = text

        # 1. Length check
        if len(text) > settings.max_output_length:
            violations.append(f"Output exceeds maximum length of {settings.max_output_length} characters")
            text = text[:settings.max_output_length] + "...[TRUNCATED]"
            redacted = text

        # 2. Sensitive data in output
        redacted, sensitive_violations = self._check_sensitive_output(redacted)
        violations.extend(sensitive_violations)

        # 3. Hallucination signals (log as warning, don't block)
        hallucination_signals = self._detect_hallucination_signals(text)
        if hallucination_signals:
            logger.warning(
                "Possible hallucination signals in output",
                extra={"signals": hallucination_signals}
            )

        # 4. Refusal detection — log when model refuses
        if self._is_refusal(text):
            logger.info("Model issued a refusal response", extra={"query_preview": original_query[:100]})

        # 5. Code injection in output (when output is rendered in UI)
        if self._contains_script_injection(text):
            violations.append("Output contains potential script injection")
            redacted = self._sanitize_html(redacted)

        passed = len([v for v in violations if "sensitive" in v.lower()]) == 0
        return GuardrailResult(
            passed=passed,
            violations=violations,
            redacted_content=redacted if redacted != text else None,
        )

    def _check_sensitive_output(self, text: str) -> tuple[str, list[str]]:
        violations = []
        for data_type, pattern in self.sensitive_patterns.items():
            matches = pattern.findall(text)
            if matches:
                violations.append(f"Sensitive data ({data_type}) detected in output — redacting")
                text = pattern.sub(f"[REDACTED_{data_type.upper()}]", text)
        return text, violations

    def _detect_hallucination_signals(self, text: str) -> list[str]:
        signals = []
        for pattern in self.hallucination_patterns:
            match = pattern.search(text)
            if match:
                signals.append(match.group(0))
        return signals

    def _is_refusal(self, text: str) -> bool:
        refusal_phrases = [
            "i cannot", "i can't", "i'm unable to", "i am unable to",
            "i won't", "i will not", "that's not something i",
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in refusal_phrases)

    def _contains_script_injection(self, text: str) -> bool:
        return bool(re.search(r"<script[\s>]", text, re.IGNORECASE))

    def _sanitize_html(self, text: str) -> str:
        text = re.sub(r"<script[^>]*>.*?</script>", "[REMOVED]", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"javascript:", "[REMOVED]", text, flags=re.IGNORECASE)
        return text
