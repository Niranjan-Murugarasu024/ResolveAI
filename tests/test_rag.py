import pytest
from app.services.rag_engine import rag_engine

def test_rag_retrieves_relevant_authentication_doc():
    query = "Why am I getting 401 Unauthorized with my API key?"
    results = rag_engine.search(query, top_k=2)
    assert len(results) > 0
    top_doc = results[0]
    assert "authentication.md" in top_doc["doc_id"]
    assert top_doc["relevance_score"] > 0.5

def test_rag_retrieves_rate_limits_doc():
    query = "How to handle 429 Too Many Requests and rate limits?"
    results = rag_engine.search(query, top_k=2)
    assert len(results) > 0
    top_doc = results[0]
    assert "rate_limits.md" in top_doc["doc_id"]
