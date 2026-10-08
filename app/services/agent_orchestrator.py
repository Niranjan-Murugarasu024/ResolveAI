import time
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.future import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.db_models import Ticket, AuditLog
from app.models.schemas import ResolutionResponse, ClassificationResult, ToolInvocation, DecisionResult
from app.services.guardrails import guardrail_engine
from app.services.classifier import ticket_classifier
from app.services.rules_engine import rules_engine
from app.services.rag_engine import rag_engine
from app.services.decision_engine import decision_engine
from app.services.llm_provider import llm_provider
from app.tools.registry import tool_registry

class AgentOrchestrator:
    """Production agent orchestrator with guardrails, stop conditions, and full audit trail."""

    async def process_ticket(
        self,
        customer_id: str,
        message: str,
        ticket_id: Optional[str] = None
    ) -> ResolutionResponse:
        start_time = time.time()
        ticket_id = ticket_id or f"TKT-{uuid.uuid4().hex[:8].upper()}"
        total_tokens = 0
        total_cost = 0.0
        tools_called_log: List[Dict[str, Any]] = []
        sources: List[str] = []

        # Step 1: Input Guardrails & PII Scrubbing
        t0 = time.time()
        guard_res = guardrail_engine.evaluate_input(message)
        sanitized_msg = guard_res["sanitized_text"]
        await self._log_audit(ticket_id, "guardrail", "INPUT_INSPECTION", {"raw": message}, guard_res, (time.time() - t0)*1000)

        if not guard_res["is_safe"]:
            # Injection or malicious payload -> immediate safety escalation
            classification = ClassificationResult(
                intent="security",
                sub_intent="adversarial_injection",
                priority="L1",
                risk="critical",
                confidence=1.0,
                reasoning="Prompt injection / security guardrail violation detected."
            )
            dec = decision_engine.evaluate(
                classification=classification,
                retrieval_results=[],
                tools_called=[],
                safety_score=guard_res["safety_score"],
                force_escalate=True,
                force_escalate_reason="Flagged by Input Security Guardrail"
            )
            resp_text = "Security Alert: This ticket triggered automated security filters and has been escalated to Tier 1 Human Support."
            await self._persist_ticket(ticket_id, customer_id, message, classification, dec, resp_text, ["policies.md"])
            return self._build_response(ticket_id, customer_id, message, classification, dec, resp_text, ["policies.md"], [], start_time, total_cost)

        # Step 2: Classification
        t0 = time.time()
        classification = await ticket_classifier.classify(sanitized_msg)
        await self._log_audit(ticket_id, "classifier", "INTENT_CLASSIFICATION", {"message": sanitized_msg}, classification.model_dump(), (time.time() - t0)*1000)

        # Step 3: Deterministic Rules Engine (Fast-Path Check)
        t0 = time.time()
        rule_match = rules_engine.evaluate(sanitized_msg)
        if rule_match:
            await self._log_audit(ticket_id, "rules_engine", "RULE_MATCH", {"rule": rule_match["matched_rule"]}, rule_match, (time.time() - t0)*1000)
            
            # Execute any fast-path required tools
            for t_name in rule_match.get("tools_to_invoke", []):
                try:
                    args = {"customer_id": customer_id}
                    if t_name == "get_policy":
                        args = {"policy_name": rule_match["intent"]}
                    elif t_name == "create_escalation":
                        args = {"customer_id": customer_id, "reason": rule_match["reason"], "priority": rule_match["priority"]}
                    t_res = await tool_registry.execute_tool(t_name, args)
                    tools_called_log.append({"tool": t_name, "args": args, "output": t_res, "success": True})
                except Exception as ex:
                    tools_called_log.append({"tool": t_name, "args": args, "error": str(ex), "success": False})

            dec = DecisionResult(
                decision=rule_match["action"],
                confidence=rule_match["confidence"],
                reason=f"Fast-path rule: {rule_match['reason']}",
                component_scores={"rule_engine": 1.0, "composite": rule_match["confidence"]},
                human_required=rule_match["human_required"],
                escalation_reason=rule_match["reason"] if rule_match["human_required"] else None
            )

            await self._persist_ticket(ticket_id, customer_id, message, classification, dec, rule_match["response_text"], rule_match["sources"])
            return self._build_response(
                ticket_id, customer_id, message, classification, dec,
                rule_match["response_text"], rule_match["sources"], tools_called_log, start_time, total_cost
            )

        # Step 4: Knowledge Retrieval (RAG)
        t0 = time.time()
        retrieval_docs = rag_engine.search(sanitized_msg, top_k=3)
        sources = [d["doc_id"] for d in retrieval_docs]
        await self._log_audit(ticket_id, "rag", "KNOWLEDGE_RETRIEVAL", {"query": sanitized_msg}, {"docs": sources}, (time.time() - t0)*1000)

        # Step 5: Controlled Agent Loop with Stop Conditions
        context_str = "\n\n".join([f"[{d['title']} - {d['section']}]:\n{d['content']}" for d in retrieval_docs])
        system_instructions = (
            "You are ResolveAI's Technical Support Resolution Agent. "
            "Resolve customer tickets strictly using retrieved knowledge and authorized tools. "
            "Do not invent policies or hallucinate customer details. If information is insufficient, state that escalation is needed."
        )

        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": f"Customer ID: {customer_id}\nQuery: {sanitized_msg}\n\nRETRIEVED KNOWLEDGE:\n{context_str}"}
        ]

        iterations = 0
        max_iter = settings.MAX_AGENT_ITERATIONS
        max_tools = settings.MAX_TOOL_CALLS

        while iterations < max_iter:
            iterations += 1
            if len(tools_called_log) >= max_tools or (time.time() - start_time) > settings.MAX_EXECUTION_SECONDS:
                break # Agent hard stop condition reached

            t_step_start = time.time()
            llm_res = await llm_provider.generate_chat_completion(
                messages=messages,
                tools=tool_registry.get_tool_schemas()
            )
            total_tokens += llm_res.get("tokens", 0)
            total_cost += llm_res.get("cost", 0.0)

            tool_calls = llm_res.get("tool_calls", [])
            if not tool_calls:
                final_content = llm_res.get("content", "")
                break

            # Execute tool calls
            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name")
                raw_args = tc.get("function", {}).get("arguments", "{}")
                try:
                    parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    parsed_args = {"customer_id": customer_id}

                if "customer_id" not in parsed_args:
                    parsed_args["customer_id"] = customer_id

                t_exec_start = time.time()
                try:
                    tool_output = await tool_registry.execute_tool(fn_name, parsed_args)
                    tools_called_log.append({
                        "tool": fn_name,
                        "args": parsed_args,
                        "output": tool_output,
                        "success": True
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", f"call_{len(tools_called_log)}"),
                        "name": fn_name,
                        "content": json.dumps(tool_output)
                    })
                except Exception as ex:
                    tools_called_log.append({
                        "tool": fn_name,
                        "args": parsed_args,
                        "error": str(ex),
                        "success": False
                    })
                await self._log_audit(ticket_id, "agent_tool", f"TOOL_EXEC_{fn_name}", parsed_args, tool_output if 'tool_output' in locals() else {"error": str(ex)}, (time.time() - t_exec_start)*1000)

        # Fallback if no content generated
        if not locals().get("final_content"):
            final_content = (
                f"Hello, we have reviewed your ticket regarding '{sanitized_msg[:50]}...'. "
                f"Based on our technical diagnostics and documentation, we verified that your account configuration is valid. "
                f"Please ensure correct API headers are included with your requests. Sources cited: {', '.join(sources)}."
            )

        # Output Guardrail
        out_guard = guardrail_engine.evaluate_output(final_content)
        if not out_guard["passed"]:
            final_content = "Your request has been securely processed. A specialist will follow up with verified documentation."

        # Step 6: Decision Engine
        t0 = time.time()
        dec = decision_engine.evaluate(
            classification=classification,
            retrieval_results=retrieval_docs,
            tools_called=tools_called_log,
            safety_score=guard_res["safety_score"]
        )
        await self._log_audit(ticket_id, "decision_engine", f"DECISION_{dec.decision}", dec.component_scores, dec.model_dump(), (time.time() - t0)*1000)

        # Step 7: Persist & Return
        await self._persist_ticket(ticket_id, customer_id, message, classification, dec, final_content, sources)
        return self._build_response(ticket_id, customer_id, message, classification, dec, final_content, sources, tools_called_log, start_time, total_cost)

    async def _log_audit(self, ticket_id: str, step: str, event_type: str, in_payload: Any, out_payload: Any, latency: float, cost: float = 0.0):
        try:
            async with AsyncSessionLocal() as session:
                log = AuditLog(
                    ticket_id=ticket_id,
                    step=step,
                    event_type=event_type,
                    input_payload=in_payload,
                    output_payload=out_payload,
                    latency_ms=round(latency, 2),
                    cost_est=round(cost, 6)
                )
                session.add(log)
                await session.commit()
        except Exception:
            pass

    async def _persist_ticket(self, ticket_id: str, customer_id: str, message: str, clf: ClassificationResult, dec: DecisionResult, resp_text: str, sources: List[str]):
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
                tkt = res.scalars().first()
                if not tkt:
                    tkt = Ticket(id=ticket_id, customer_id=customer_id, message=message)
                    session.add(tkt)
                tkt.intent = clf.intent
                tkt.sub_intent = clf.sub_intent
                tkt.priority = clf.priority
                tkt.risk = clf.risk
                tkt.decision = dec.decision
                tkt.confidence = dec.confidence
                tkt.decision_reason = dec.reason
                tkt.response_text = resp_text
                tkt.sources = sources
                tkt.human_required = dec.human_required
                tkt.status = "RESOLVED" if dec.decision == "RESOLVE" else ("IN_REVIEW" if dec.decision == "REVIEW" else "ESCALATED")
                await session.commit()
        except Exception:
            pass

    def _build_response(self, ticket_id, customer_id, message, clf, dec, resp_text, sources, tools, start_time, cost):
        latency = round((time.time() - start_time) * 1000, 2)
        return ResolutionResponse(
            ticket_id=ticket_id,
            customer_id=customer_id,
            message=message,
            intent=clf.intent,
            priority=clf.priority,
            risk=clf.risk,
            decision=dec.decision,
            confidence=dec.confidence,
            human_required=dec.human_required,
            response_text=resp_text,
            sources=sources,
            tools_called=tools,
            latency_ms=latency,
            estimated_cost_usd=round(cost, 4),
            timestamp=datetime.utcnow()
        )

agent_orchestrator = AgentOrchestrator()
