from typing import Dict, Any, List, Optional
from app.models.schemas import DecisionResult, ClassificationResult
from app.core.config import settings

class DecisionEngine:
    """Multi-signal decision engine evaluating confidence, risk, policy, and safety."""

    def evaluate(
        self,
        classification: ClassificationResult,
        retrieval_results: List[Dict[str, Any]],
        tools_called: List[Dict[str, Any]],
        safety_score: float,
        policy_violation: bool = False,
        force_escalate: bool = False,
        force_escalate_reason: Optional[str] = None
    ) -> DecisionResult:
        # 1. Classification Signal (0.25)
        c_score = classification.confidence

        # 2. Retrieval Signal (0.25)
        if retrieval_results:
            top_rel = max(r.get("relevance_score", 0.0) for r in retrieval_results)
            r_score = min(1.0, top_rel)
        else:
            r_score = 0.5 if classification.intent == "account" else 0.2

        # 3. Tool Execution Signal (0.20)
        if tools_called:
            successes = sum(1 for t in tools_called if t.get("success", True))
            t_score = successes / len(tools_called)
        else:
            # If no tools were required and issue is straightforward, neutral score
            t_score = 0.9

        # 4. Policy Match Signal (0.15)
        p_score = 0.0 if policy_violation else 1.0

        # 5. Safety Guardrail Signal (0.15)
        s_score = safety_score

        # Composite Decision Score
        composite_score = round(
            (0.25 * c_score) +
            (0.25 * r_score) +
            (0.20 * t_score) +
            (0.15 * p_score) +
            (0.15 * s_score),
            3
        )

        component_scores = {
            "classification_confidence": round(c_score, 3),
            "retrieval_relevance": round(r_score, 3),
            "tool_success_rate": round(t_score, 3),
            "policy_compliance": round(p_score, 3),
            "safety_guardrail": round(s_score, 3),
            "composite": composite_score
        }

        # Human-in-the-loop Triggers
        if force_escalate:
            return DecisionResult(
                decision="ESCALATE",
                confidence=composite_score,
                reason=force_escalate_reason or "Mandatory escalation triggered by policy or security rule.",
                component_scores=component_scores,
                human_required=True,
                escalation_reason=force_escalate_reason
            )

        if classification.risk in ["critical", "high"] or classification.intent == "security":
            return DecisionResult(
                decision="ESCALATE",
                confidence=composite_score,
                reason=f"High risk ({classification.risk}) detected for intent '{classification.intent}'. Requires human specialist review.",
                component_scores=component_scores,
                human_required=True,
                escalation_reason=f"Risk level: {classification.risk}"
            )

        # Confidence Threshold Routing
        if composite_score >= settings.RESOLVE_THRESHOLD:
            return DecisionResult(
                decision="RESOLVE",
                confidence=composite_score,
                reason="High multi-signal confidence with verified documentation and tools.",
                component_scores=component_scores,
                human_required=False
            )
        elif composite_score >= settings.REVIEW_THRESHOLD:
            return DecisionResult(
                decision="REVIEW",
                confidence=composite_score,
                reason="Moderate confidence: Response drafted for human supervisor review.",
                component_scores=component_scores,
                human_required=True,
                escalation_reason="Confidence below autonomous threshold."
            )
        else:
            return DecisionResult(
                decision="ESCALATE",
                confidence=composite_score,
                reason="Low multi-signal confidence or insufficient documentation. Routed to Tier 2 engineering.",
                component_scores=component_scores,
                human_required=True,
                escalation_reason="Low multi-signal confidence score."
            )

decision_engine = DecisionEngine()
