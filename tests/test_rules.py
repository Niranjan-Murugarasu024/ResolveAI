import pytest
from app.services.rules_engine import rules_engine

def test_security_compromise_fast_path():
    msg = "Emergency: our API keys were leaked on a public github repo and compromised."
    res = rules_engine.evaluate(msg)
    assert res is not None
    assert res["matched_rule"] == "CRITICAL_SECURITY_TRIGGER"
    assert res["intent"] == "security"
    assert res["priority"] == "L1"
    assert res["action"] == "ESCALATE"
    assert res["human_required"] is True

def test_high_value_refund_fast_path():
    msg = "Please issue a refund of 50,000 for unexpected charges on our invoice."
    res = rules_engine.evaluate(msg)
    assert res is not None
    assert res["matched_rule"] == "FINANCIAL_POLICY_TRIGGER"
    assert res["intent"] == "billing"
    assert res["action"] == "ESCALATE"
    assert res["human_required"] is True

def test_password_reset_self_serve():
    msg = "I need to reset my password for my account."
    res = rules_engine.evaluate(msg)
    assert res is not None
    assert res["matched_rule"] == "ACCOUNT_SELF_SERVE_TRIGGER"
    assert res["action"] == "RESOLVE"
    assert res["human_required"] is False

def test_non_matching_query_passes_to_agent():
    msg = "We are getting intermittent 401 Unauthorized errors on endpoint /v1/models."
    res = rules_engine.evaluate(msg)
    assert res is None # Must proceed to RAG and Agentic investigation
