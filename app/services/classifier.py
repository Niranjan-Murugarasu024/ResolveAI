import json
import re
from typing import Dict, Any
from app.models.schemas import ClassificationResult
from app.services.llm_provider import llm_provider

class TicketClassifier:
    """Classifies inbound tickets into structured intent, priority, risk, and confidence."""

    SYSTEM_PROMPT = """You are an expert SaaS Technical Support Classifier for ResolveAI (an API and developer platform).
Your job is to classify inbound customer support tickets into precise structured metadata.

Categories (Choose the single best match):
- authentication: 401 Unauthorized, 403 Forbidden, API keys, Bearer tokens, JWT TTL, OAuth, scopes, credentials, IP allowlisting.
- rate_limiting: 429 Too Many Requests, rate limits, quota limits, request limits, throttling, burst traffic, Retry-After header.
- billing: invoices, duplicate charges, refund requests, payment updates, wire transfers, currency, subscriptions (upgrades, cancellations, proration).
- account: password reset, user profile, invite team member, administrator MFA, SSO/Okta configuration.
- technical: 500 Internal Server, 502/503/504 gateway errors, timeouts, webhook delivery failures, latency, Python SDK, idempotency keys.
- security: compromised account/key, token leaked on GitHub, suspicious IP access, data breach, extortion, adversarial attacks.
- out_of_domain: ONLY completely non-SaaS topics unrelated to our product (e.g. weather, recipes, poems, sports, world trivia). Any question about our API, docs, rate limits, plans, or SDK is IN-DOMAIN.

Priority (Company SLA Matrix):
- L1: Critical security breach, compromised API keys, platform outage.
- L2: Production blocking errors (401/403/429/500/502 on production), high-value financial refunds (>= ₹50,000 or >= $500), MFA admin lockout.
- L3: Standard developer questions, rate limit comparisons, documentation, billing inquiries, plan upgrades/cancellations, SDK questions.
- L4: Self-serve password reset, general feature requests, or out_of_domain.

Risk:
- critical: Leaked keys, security breaches, unauthorized access, prompt injection.
- high: High-value refund disputes (>= ₹50,000 or >= $500).
- medium: Production 401/403/429 errors.
- low: General documentation questions, plan comparisons, password reset.

Respond strictly with valid JSON:
{
  "intent": "authentication|rate_limiting|billing|account|technical|security|out_of_domain",
  "sub_intent": "string",
  "priority": "L1|L2|L3|L4",
  "risk": "low|medium|high|critical",
  "confidence": 0.0-1.0,
  "reasoning": "string"
}
"""

    async def classify(self, message: str) -> ClassificationResult:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Classify this support ticket:\n\"{message}\""}
        ]

        resp = await llm_provider.generate_chat_completion(
            messages=messages,
            temperature=0.0
        )

        content = resp.get("content", "").strip()
        # Clean any markdown code blocks
        if "```" in content:
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        try:
            parsed = json.loads(content)
            return ClassificationResult(**parsed)
        except Exception:
            # Deterministic heuristic fallback if JSON parsing fails
            return self._heuristic_fallback(message)

    def _heuristic_fallback(self, message: str) -> ClassificationResult:
        m = message.lower()
        if any(w in m for w in ["compromised", "hacked", "stolen", "leak"]):
            return ClassificationResult(
                intent="security",
                sub_intent="compromised_credentials",
                priority="L1",
                risk="critical",
                confidence=0.98,
                reasoning="Security compromise detected."
            )
        elif any(w in m for w in ["401", "unauthorized", "api key", "bearer", "403"]):
            return ClassificationResult(
                intent="authentication",
                sub_intent="invalid_api_key",
                priority="L2",
                risk="medium",
                confidence=0.94,
                reasoning="API authentication failure."
            )
        elif any(w in m for w in ["429", "rate limit", "too many requests", "quota"]):
            return ClassificationResult(
                intent="rate_limiting",
                sub_intent="quota_exceeded",
                priority="L2" if "prod" in m else "L3",
                risk="medium",
                confidence=0.93,
                reasoning="Rate limit or quota violation."
            )
        elif any(w in m for w in ["refund", "charge", "invoice", "payment", "billed"]):
            return ClassificationResult(
                intent="billing",
                sub_intent="refund_or_charge",
                priority="L2",
                risk="high" if "refund" in m else "medium",
                confidence=0.92,
                reasoning="Billing inquiry or dispute."
            )
        elif any(w in m for w in ["password", "mfa", "login", "reset"]):
            return ClassificationResult(
                intent="account",
                sub_intent="password_reset",
                priority="L4",
                risk="low",
                confidence=0.95,
                reasoning="Standard account access request."
            )
        else:
            return ClassificationResult(
                intent="technical",
                sub_intent="general_issue",
                priority="L3",
                risk="low",
                confidence=0.85,
                reasoning="General technical assistance required."
            )

ticket_classifier = TicketClassifier()
