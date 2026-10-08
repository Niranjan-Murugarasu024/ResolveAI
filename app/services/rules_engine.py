import re
from typing import Optional, Dict, Any

class RulesEngine:
    """Deterministic rule evaluator running before agentic or generative paths."""

    SECURITY_TERMS = [
        "compromised", "stolen", "hacked", "leak", "leaked", "github repo",
        "changed my email", "unauthorized access", "breach", "hijack"
    ]

    HIGH_VALUE_REFUND_TERMS = [
        "refund", "chargeback", "charged twice", "double charge",
        "50000", "50,000", "500$", "$500", "500 dollars"
    ]

    PASSWORD_RESET_TERMS = [
        "reset my password", "reset password", "forgot password", "password reset link"
    ]

    OUT_OF_DOMAIN_TERMS = [
        "weather", "recipe", "write a poem", "who won", "president of", "capital of"
    ]

    def evaluate(self, message: str) -> Optional[Dict[str, Any]]:
        lower = message.lower()

        # 1. Critical Security Fast-Path (Must always escalate, 0 tokens wasted)
        if any(term in lower for term in self.SECURITY_TERMS):
            return {
                "matched_rule": "CRITICAL_SECURITY_TRIGGER",
                "intent": "security",
                "priority": "L1",
                "risk": "critical",
                "action": "ESCALATE",
                "human_required": True,
                "confidence": 1.0,
                "reason": "Security protocol: Suspected compromise or credential leak detected.",
                "response_text": (
                    "Security Alert: Your inquiry has been routed to our Senior Security Incident Response Team (Tier 1 Priority). "
                    "For your immediate safety, please navigate to your Security Settings to revoke all active API keys "
                    "and review recent session logins. An engineer will follow up shortly."
                ),
                "sources": ["security_incidents.md", "policies.md"],
                "tools_to_invoke": ["create_escalation"]
            }

        # 2. High-Risk Financial Action Fast-Path
        if any(term in lower for term in self.HIGH_VALUE_REFUND_TERMS):
            # Check if this requires human escalation per company policy
            is_high_value = bool(re.search(r"(50,?000|\$500|500\s*dollars|large)", lower))
            return {
                "matched_rule": "FINANCIAL_POLICY_TRIGGER",
                "intent": "billing",
                "priority": "L2" if is_high_value else "L3",
                "risk": "high" if is_high_value else "medium",
                "action": "ESCALATE" if is_high_value else "REVIEW",
                "human_required": is_high_value,
                "confidence": 0.98,
                "reason": f"Billing policy: Financial refund/chargeback review required (High value={is_high_value}).",
                "response_text": (
                    "Thank you for contacting billing. Your request regarding transaction adjustments/refunds "
                    "has been recorded. As per company financial compliance policy, refunds exceeding standard thresholds "
                    "undergo mandatory review by our Human Billing Specialist to safeguard account equity. "
                    "Your case has been prioritized."
                ),
                "sources": ["billing_and_refunds.md", "policies.md"],
                "tools_to_invoke": ["get_subscription", "create_escalation"] if is_high_value else ["get_subscription"]
            }

        # 3. Standard Account Self-Serve Fast-Path
        if any(term in lower for term in self.PASSWORD_RESET_TERMS):
            return {
                "matched_rule": "ACCOUNT_SELF_SERVE_TRIGGER",
                "intent": "account",
                "priority": "L4",
                "risk": "low",
                "action": "RESOLVE",
                "human_required": False,
                "confidence": 1.0,
                "reason": "Standard self-serve workflow: Password reset instructions.",
                "response_text": (
                    "To reset your account password, visit https://app.resolveai.io/reset-password, enter your registered "
                    "email address, and follow the verification link sent to your inbox. The reset link is valid for 15 minutes."
                ),
                "sources": ["policies.md"],
                "tools_to_invoke": []
            }

        # 4. Out of Domain
        if any(term in lower for term in self.OUT_OF_DOMAIN_TERMS):
            return {
                "matched_rule": "OUT_OF_DOMAIN_TRIGGER",
                "intent": "out_of_domain",
                "priority": "L4",
                "risk": "low",
                "action": "RESOLVE",
                "human_required": False,
                "confidence": 0.95,
                "reason": "Out of domain query detected.",
                "response_text": (
                    "ResolveAI is specialized in developer API support, authentication, rate limits, and platform billing. "
                    "We are unable to answer general knowledge or external queries. How can we assist with your ResolveAI integration?"
                ),
                "sources": [],
                "tools_to_invoke": []
            }

        return None

rules_engine = RulesEngine()
