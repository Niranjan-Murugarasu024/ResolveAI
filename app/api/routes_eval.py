from fastapi import APIRouter
from typing import Optional
from app.models.schemas import EvaluationMetricSummary
from app.services.evaluator import evaluation_engine

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])

_last_evaluation_result: Optional[EvaluationMetricSummary] = None

@router.post("", response_model=EvaluationMetricSummary)
async def run_evaluation(max_cases: Optional[int] = None):
    """Executes the full evaluation suite and updates regression metrics."""
    global _last_evaluation_result
    result = await evaluation_engine.run_suite(max_cases=max_cases)
    _last_evaluation_result = result
    return result

@router.get("/results", response_model=EvaluationMetricSummary)
async def get_evaluation_results():
    """Retrieves the latest evaluation run summary, running it if not yet cached."""
    global _last_evaluation_result
    if _last_evaluation_result is None:
        _last_evaluation_result = await evaluation_engine.run_suite(max_cases=20)
    return _last_evaluation_result
