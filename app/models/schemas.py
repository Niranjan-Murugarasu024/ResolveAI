from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TicketCreateRequest(BaseModel):
    customer_id: str = Field(..., json_schema_extra={"example": "CUS-1023"})
    message: str = Field(..., json_schema_extra={"example": "My production API returns 401 Unauthorized since this morning."})

class ClassificationResult(BaseModel):
    intent: str = Field(..., description="authentication, rate_limiting, billing, account, technical, security, out_of_domain")
    sub_intent: Optional[str] = None
    priority: str = Field(..., description="L1, L2, L3, L4")
    risk: str = Field(..., description="low, medium, high, critical")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None

class ToolInvocation(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None

class DecisionResult(BaseModel):
    decision: str = Field(..., description="RESOLVE, REVIEW, ESCALATE")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    component_scores: Dict[str, float]
    human_required: bool = False
    escalation_reason: Optional[str] = None

class ResolutionResponse(BaseModel):
    ticket_id: str
    customer_id: str
    message: str
    intent: str
    priority: str
    risk: str
    decision: str
    confidence: float
    human_required: bool
    response_text: str
    sources: List[str] = []
    tools_called: List[Dict[str, Any]] = []
    latency_ms: float
    estimated_cost_usd: float
    timestamp: datetime

class EvaluationCase(BaseModel):
    id: str
    input: str
    customer_id: Optional[str] = "CUS-1023"
    expected: Dict[str, Any] # intent, priority, action, human_required, expected_tools, expected_doc

class EvaluationMetricSummary(BaseModel):
    total_cases: int
    intent_accuracy: float
    priority_accuracy: float
    retrieval_recall: float
    tool_accuracy: float
    escalation_accuracy: float
    groundedness_score: float
    avg_latency_ms: float
    avg_cost_usd: float
    regression_status: str # PASS or FAIL
    breakdown_by_category: Dict[str, Dict[str, float]] = {}
