#!/usr/bin/env python3
import asyncio
import sys
import os

# Add root project to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import engine, Base
from app.services.evaluator import evaluation_engine

async def main():
    print("=" * 65)
    print("ResolveAI — Evaluation & Regression Test Gate")
    print("Target Benchmark: Production Agentic Support System")
    print("=" * 65)
    
    # Ensure database schema is ready
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    print("\nRunning test cases from evaluation/test_cases.jsonl...")
    metrics = await evaluation_engine.run_suite()
    
    print("\n" + "-" * 65)
    print(f"EVALUATION RESULTS ({metrics.total_cases} Total Test Cases)")
    print("-" * 65)
    print(f"Intent Classification Accuracy:  {metrics.intent_accuracy:>5}%  (Gate: >= 88%)")
    print(f"Priority Alignment Accuracy:     {metrics.priority_accuracy:>5}%  (Gate: >= 85%)")
    print(f"Knowledge Retrieval Recall:      {metrics.retrieval_recall:>5}%  (Gate: >= 80%)")
    print(f"Tool Selection Accuracy:         {metrics.tool_accuracy:>5}%  (Gate: >= 85%)")
    print(f"Human Escalation Accuracy:       {metrics.escalation_accuracy:>5}%  (Gate: >= 90%)")
    print(f"Response Groundedness Score:     {metrics.groundedness_score:>5}%  (Gate: >= 90%)")
    print(f"Average Decision Latency:        {metrics.avg_latency_ms:>5} ms")
    print(f"Average Estimated Cost / Ticket: ${metrics.avg_cost_usd:.4f}")
    print("-" * 65)
    
    print("\nCategory Breakdown:")
    for cat, stat in metrics.breakdown_by_category.items():
        print(f"  • {cat.capitalize():<15} {stat['passed']}/{stat['total']} passed ({stat['accuracy']}%)")
        
    print("\n" + "=" * 65)
    if metrics.regression_status == "PASS":
        print("REGRESSION STATUS: [ PASS ] — Deployment safe.")
        print("=" * 65)
        sys.exit(0)
    else:
        print("REGRESSION STATUS: [ FAIL ] — Critical metrics below tolerance.")
        print("=" * 65)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
