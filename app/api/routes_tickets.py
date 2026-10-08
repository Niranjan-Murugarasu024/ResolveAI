from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import AsyncSessionLocal
from app.models.db_models import Ticket, AuditLog
from app.models.schemas import TicketCreateRequest, ResolutionResponse
from app.services.agent_orchestrator import agent_orchestrator

router = APIRouter(prefix="/tickets", tags=["Tickets"])

class TicketActionRequest(BaseModel):
    action: str # "APPROVE", "EDIT", "ESCALATE"
    edited_response: Optional[str] = None
    note: Optional[str] = None

@router.post("", response_model=ResolutionResponse)
async def create_and_resolve_ticket(payload: TicketCreateRequest):
    """Processes inbound ticket through Guardrails -> Classifier -> Rules -> RAG -> Tools -> Decision Engine."""
    response = await agent_orchestrator.process_ticket(
        customer_id=payload.customer_id,
        message=payload.message
    )
    return response

@router.get("")
async def list_tickets(limit: int = 50):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Ticket).order_by(Ticket.created_at.desc()).limit(limit))
        tickets = res.scalars().all()
        return [
            {
                "id": t.id,
                "customer_id": t.customer_id,
                "message": t.message,
                "intent": t.intent,
                "priority": t.priority,
                "risk": t.risk,
                "status": t.status,
                "decision": t.decision,
                "confidence": t.confidence,
                "decision_reason": t.decision_reason,
                "human_required": t.human_required,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in tickets
        ]

@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        t = res.scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return {
            "id": t.id,
            "customer_id": t.customer_id,
            "message": t.message,
            "intent": t.intent,
            "sub_intent": t.sub_intent,
            "priority": t.priority,
            "risk": t.risk,
            "status": t.status,
            "decision": t.decision,
            "confidence": t.confidence,
            "decision_reason": t.decision_reason,
            "response_text": t.response_text,
            "sources": t.sources,
            "human_required": t.human_required,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }

@router.get("/{ticket_id}/audit")
async def get_ticket_audit_trail(ticket_id: str):
    """Returns chronological audit events and tool trace for the ticket."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(AuditLog).where(AuditLog.ticket_id == ticket_id).order_by(AuditLog.timestamp.asc())
        )
        logs = res.scalars().all()
        return [
            {
                "step": l.step,
                "event_type": l.event_type,
                "input": l.input_payload,
                "output": l.output_payload,
                "latency_ms": l.latency_ms,
                "cost_est": l.cost_est,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None
            }
            for l in logs
        ]

@router.post("/{ticket_id}/action")
async def handle_human_action(ticket_id: str, action_req: TicketActionRequest):
    """Human-in-the-loop action: Approve draft, edit response, or escalate."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        t = res.scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if action_req.action == "APPROVE":
            t.status = "RESOLVED"
        elif action_req.action == "EDIT":
            t.status = "RESOLVED"
            if action_req.edited_response:
                t.response_text = action_req.edited_response
        elif action_req.action == "ESCALATE":
            t.status = "ESCALATED"
            t.human_required = True
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        await session.commit()
        return {"status": "SUCCESS", "ticket_id": ticket_id, "new_status": t.status}
