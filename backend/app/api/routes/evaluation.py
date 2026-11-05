"""Evaluation result endpoint.

Reads only a real, previously written metrics file. When the SciFact harness has
not been run, the endpoint returns an explicit `not_run` state so the UI cannot
mistake placeholder numbers for measured results.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.schemas.verification import EvaluationResponse

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

RESULTS_FILE = (
    Path(__file__).resolve().parents[4] / "experiments" / "results" / "scifact_test_metrics.json"
)


@router.get("", response_model=EvaluationResponse)
def get_evaluation() -> EvaluationResponse:
    if not RESULTS_FILE.exists():
        return EvaluationResponse(
            status="not_run",
            message=(
                "No SciFact benchmark has been executed. The evaluation harness, metrics, "
                "and dataset manifest are prepared, but no measured score is available."
            ),
        )
    try:
        results = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return EvaluationResponse(
            status="error",
            message="A metrics file exists but could not be read. Inspect experiments/results.",
        )
    return EvaluationResponse(
        status="completed",
        message="Metrics loaded from the executed SciFact evaluation run.",
        results=results,
    )
