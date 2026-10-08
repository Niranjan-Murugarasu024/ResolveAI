import pytest
from app.services.decision_engine import decision_engine
from app.models.schemas import ClassificationResult

def test_decision_engine_high_confidence_resolves():
    clf = ClassificationResult(
        intent="authentication",
        priority="L2",
        risk="low",
        confidence=0.96,
        reasoning="Valid 401 resolution"
    )
    retrieval = [{"doc_id": "authentication.md", "relevance_score": 0.95}]
    tools = [{"tool": "get_api_key_status", "success": True}]
    
    dec = decision_engine.evaluate(clf, retrieval, tools, safety_score=1.0)
    assert dec.decision == "RESOLVE"
    assert dec.confidence >= 0.90
    assert dec.human_required is False

def test_decision_engine_critical_security_escalates():
    clf = ClassificationResult(
        intent="security",
        priority="L1",
        risk="critical",
        confidence=0.99,
        reasoning="Compromised credentials"
    )
    dec = decision_engine.evaluate(clf, [], [], safety_score=0.4, force_escalate=True)
    assert dec.decision == "ESCALATE"
    assert dec.human_required is True
