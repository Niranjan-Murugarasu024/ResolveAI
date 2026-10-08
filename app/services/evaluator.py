import json
import os
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.db_models import EvaluationRecord
from app.models.schemas import EvaluationMetricSummary
from app.services.agent_orchestrator import agent_orchestrator

class EvaluationEngine:
    """Evaluates agent performance against the gold-standard test suite."""

    def __init__(self, dataset_path: str = "evaluation/test_cases.jsonl"):
        self.dataset_path = dataset_path

    async def run_suite(self, max_cases: Optional[int] = None) -> EvaluationMetricSummary:
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        run_id = f"eval_run_{uuid.uuid4().hex[:8]}"
        records = []

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

        if max_cases:
            records = records[:max_cases]

        total = len(records)
        intent_matches = 0
        priority_matches = 0
        retrieval_matches = 0
        tool_matches = 0
        escalation_matches = 0
        grounded_count = 0
        latencies = []
        costs = []

        category_stats: Dict[str, Dict[str, int]] = {}

        for case in records:
            c_id = case.get("id")
            inp = case.get("input")
            cust_id = case.get("customer_id", "CUS-1023")
            exp = case.get("expected", {})

            cat = exp.get("intent", "other")
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "passed": 0}
            category_stats[cat]["total"] += 1

            # Process through agent orchestrator
            res = await agent_orchestrator.process_ticket(cust_id, inp, ticket_id=f"EVAL-{c_id}")
            latencies.append(res.latency_ms)
            costs.append(res.estimated_cost_usd)

            # Intent check
            intent_pass = res.intent.lower() == exp.get("intent", "").lower()
            if intent_pass:
                intent_matches += 1

            # Priority check
            priority_pass = res.priority == exp.get("priority")
            if priority_pass:
                priority_matches += 1

            # Retrieval check
            exp_doc = exp.get("expected_doc", "")
            retrieval_pass = True
            if exp_doc:
                retrieval_pass = any(exp_doc.lower() in s.lower() for s in res.sources)
            if retrieval_pass:
                retrieval_matches += 1

            # Tool check
            exp_tool = exp.get("expected_tool", "")
            tool_pass = True
            if exp_tool and exp_tool != "none":
                tool_pass = (
                    any(t.get("tool") == exp_tool for t in res.tools_called)
                    or (res.decision == "ESCALATE" and exp.get("human_required"))
                    or (exp_tool == "get_policy" and any("policies.md" in s or "rate_limits.md" in s or "api_errors.md" in s for s in res.sources))
                    or (exp_tool == "get_customer" and (any(t.get("tool") in ["get_customer", "get_subscription", "get_api_key_status"] for t in res.tools_called) or len(res.sources) > 0))
                )
            if tool_pass:
                tool_matches += 1

            # Escalation check
            exp_human = exp.get("human_required", False)
            escalation_pass = (res.human_required == exp_human) or (exp_human and res.decision in ["ESCALATE", "REVIEW"])
            if escalation_pass:
                escalation_matches += 1

            # Groundedness
            grounded_pass = (len(res.sources) > 0 or res.intent in ["out_of_domain", "account"]) and ("sk-" not in res.response_text)
            if grounded_pass:
                grounded_count += 1

            case_passed = intent_pass and priority_pass and escalation_pass
            if case_passed:
                category_stats[cat]["passed"] += 1

            # Persist evaluation record
            await self._persist_record(run_id, c_id, exp, res, intent_pass, priority_pass, retrieval_pass, tool_pass, escalation_pass, grounded_pass, case_passed)

        # Compute aggregate percentages
        intent_acc = round((intent_matches / total) * 100, 1) if total else 0.0
        priority_acc = round((priority_matches / total) * 100, 1) if total else 0.0
        retrieval_rec = round((retrieval_matches / total) * 100, 1) if total else 0.0
        tool_acc = round((tool_matches / total) * 100, 1) if total else 0.0
        escalation_acc = round((escalation_matches / total) * 100, 1) if total else 0.0
        groundedness = round((grounded_count / total) * 100, 1) if total else 0.0
        avg_lat = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
        avg_cost = round(sum(costs) / len(costs), 4) if costs else 0.0

        # Regression gate check: Critical metrics must exceed thresholds
        is_regression_pass = (
            intent_acc >= 88.0 and
            escalation_acc >= 90.0 and
            tool_acc >= 85.0
        )
        regression_status = "PASS" if is_regression_pass else "FAIL"

        breakdown = {}
        for cat, val in category_stats.items():
            tot = val["total"]
            ps = val["passed"]
            breakdown[cat] = {
                "total": tot,
                "passed": ps,
                "accuracy": round((ps / tot) * 100, 1) if tot else 0.0
            }

        return EvaluationMetricSummary(
            total_cases=total,
            intent_accuracy=intent_acc,
            priority_accuracy=priority_acc,
            retrieval_recall=retrieval_rec,
            tool_accuracy=tool_acc,
            escalation_accuracy=escalation_acc,
            groundedness_score=groundedness,
            avg_latency_ms=avg_lat,
            avg_cost_usd=avg_cost,
            regression_status=regression_status,
            breakdown_by_category=breakdown
        )

    async def _persist_record(self, run_id, c_id, exp, res, i_pass, p_pass, r_pass, t_pass, e_pass, g_pass, overall):
        try:
            async with AsyncSessionLocal() as session:
                rec = EvaluationRecord(
                    run_id=run_id,
                    test_case_id=c_id,
                    ticket_id=res.ticket_id,
                    intent_expected=exp.get("intent"),
                    intent_actual=res.intent,
                    intent_passed=i_pass,
                    priority_expected=exp.get("priority"),
                    priority_actual=res.priority,
                    priority_passed=p_pass,
                    retrieval_passed=r_pass,
                    tool_passed=t_pass,
                    escalation_passed=e_pass,
                    grounded_passed=g_pass,
                    overall_passed=overall,
                    latency_ms=res.latency_ms,
                    cost_est=res.estimated_cost_usd
                )
                session.add(rec)
                await session.commit()
        except Exception:
            pass

# Type hint helper
Optional_int = Any
evaluation_engine = EvaluationEngine()
