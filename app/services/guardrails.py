import re
from typing import Dict, Any, Tuple, List

class GuardrailEngine:
    """Security and compliance guardrails for inputs and outputs."""

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s*prompt",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"jailbreak",
        r"override\s+policy",
        r"act\s+as\s+an\s+unfiltered",
        r"bypass\s+security",
        r"delete\s+from\s+customers",
        r"drop\s+table",
    ]

    CREDIT_CARD_REGEX = r"\b(?:\d{4}[ -]?){3}\d{4}\b"
    API_KEY_LEAK_REGEX = r"\b(sk_[a-zA-Z0-9_-]{20,})\b"
    EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

    def evaluate_input(self, text: str) -> Dict[str, Any]:
        """Scans input for prompt injections, malicious payloads, and PII."""
        injections_found: List[str] = []
        for pat in self.INJECTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                injections_found.append(pat)

        has_cc = bool(re.search(self.CREDIT_CARD_REGEX, text))
        has_secret_leak = bool(re.search(self.API_KEY_LEAK_REGEX, text))

        safety_score = 1.0
        violations = []

        if injections_found:
            safety_score -= 0.6
            violations.append(f"Prompt injection pattern detected: {len(injections_found)} matched")

        if has_cc:
            safety_score -= 0.3
            violations.append("Raw payment card number detected in payload")

        if has_secret_leak:
            safety_score -= 0.4
            violations.append("Plaintext secret key exposure detected")

        safety_score = max(0.0, safety_score)

        # Redact PII for safe downstream processing
        sanitized_text = re.sub(self.CREDIT_CARD_REGEX, "[REDACTED_CC]", text)
        sanitized_text = re.sub(self.API_KEY_LEAK_REGEX, "[REDACTED_API_KEY]", sanitized_text)

        return {
            "is_safe": safety_score >= 0.7,
            "safety_score": round(safety_score, 2),
            "sanitized_text": sanitized_text,
            "violations": violations,
            "has_pii": has_cc or has_secret_leak,
            "is_injection": len(injections_found) > 0
        }

    def evaluate_output(self, response_text: str) -> Dict[str, Any]:
        """Validates that output doesn't leak secrets or system prompt."""
        has_secret = bool(re.search(r"sk-[a-zA-Z0-9]{32,}", response_text))
        has_system_leak = "SYSTEM INSTRUCTIONS" in response_text or "You are a technical support resolution agent" in response_text

        violations = []
        if has_secret:
            violations.append("API secret leak in generated response")
        if has_system_leak:
            violations.append("System prompt verbatim reproduction detected")

        return {
            "passed": len(violations) == 0,
            "violations": violations
        }

guardrail_engine = GuardrailEngine()
