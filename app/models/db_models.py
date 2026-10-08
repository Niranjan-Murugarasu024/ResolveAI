from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String(50), primary_key=True, index=True) # e.g. "CUS-1023"
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    plan = Column(String(50), default="pro") # free, pro, enterprise
    status = Column(String(50), default="active") # active, suspended, delinquent
    created_at = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False, index=True)
    plan = Column(String(50), nullable=False)
    status = Column(String(50), default="active") # active, past_due, canceled
    monthly_quota = Column(Integer, default=50000)
    used_quota = Column(Integer, default=12400)
    renewal_date = Column(DateTime, default=datetime.utcnow)

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False) # e.g. "key_prod_9a..."
    environment = Column(String(20), default="production") # production, test
    status = Column(String(20), default="active") # active, revoked, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(String(50), primary_key=True, index=True) # e.g. "TKT-1023"
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    
    # Classification
    intent = Column(String(50), nullable=True) # authentication, billing, rate_limit, technical, security, account
    sub_intent = Column(String(50), nullable=True)
    priority = Column(String(10), default="L3") # L1, L2, L3, L4
    risk = Column(String(20), default="low") # low, medium, high, critical
    
    # Decision Engine
    status = Column(String(30), default="INGESTED") # INGESTED, PROCESSING, RESOLVED, IN_REVIEW, ESCALATED
    decision = Column(String(30), nullable=True) # RESOLVE, REVIEW, ESCALATE
    confidence = Column(Float, default=0.0)
    decision_reason = Column(Text, nullable=True)
    
    # Grounded response & sources
    response_text = Column(Text, nullable=True)
    sources = Column(JSON, default=list)
    
    human_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(50), index=True, nullable=False)
    step = Column(String(50), nullable=False) # ingestion, classification, rules, rag, tool, decision, response
    event_type = Column(String(50), nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    latency_ms = Column(Float, default=0.0)
    cost_est = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), index=True, nullable=False)
    test_case_id = Column(String(50), nullable=False)
    ticket_id = Column(String(50), nullable=True)
    
    intent_expected = Column(String(50))
    intent_actual = Column(String(50))
    intent_passed = Column(Boolean, default=False)
    
    priority_expected = Column(String(10))
    priority_actual = Column(String(10))
    priority_passed = Column(Boolean, default=False)
    
    retrieval_passed = Column(Boolean, default=False)
    tool_passed = Column(Boolean, default=False)
    escalation_passed = Column(Boolean, default=False)
    grounded_passed = Column(Boolean, default=False)
    
    overall_passed = Column(Boolean, default=False)
    latency_ms = Column(Float, default=0.0)
    cost_est = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
