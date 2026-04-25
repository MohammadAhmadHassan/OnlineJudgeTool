"""FastAPI judge service for running submitted code out of process."""
import hmac
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="Competition Judge Service")

WORKER_PATH = Path(__file__).with_name("worker.py")


class RunRequest(BaseModel):
    code: str = Field(default="", max_length=50000)
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    input_format: Optional[str] = None


class RunResponse(BaseModel):
    results: List[Dict[str, Any]]


def _setting_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _make_error_results(test_cases: List[Dict[str, Any]], message: str) -> List[Dict[str, Any]]:
    if not test_cases:
        test_cases = [{"input": "", "output": ""}]

    return [
        {
            "test_num": i + 1,
            "passed": False,
            "input": str(test.get("input", "")),
            "expected": str(test.get("output", "")),
            "output": "",
            "error": message,
        }
        for i, test in enumerate(test_cases)
    ]


def _verify_token(x_judge_token: Optional[str]) -> None:
    expected = os.environ.get("JUDGE_API_TOKEN", "").strip()
    if not expected:
        return

    provided = x_judge_token or ""
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid judge API token")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run_submission(payload: RunRequest, x_judge_token: Optional[str] = Header(default=None)) -> RunResponse:
    _verify_token(x_judge_token)

    max_tests = _setting_int("MAX_TEST_CASES", 100)
    if len(payload.test_cases) > max_tests:
        raise HTTPException(status_code=400, detail=f"Too many test cases. Max is {max_tests}.")

    timeout_seconds = _setting_int("MAX_SUBMISSION_SECONDS", 10)
    if hasattr(payload, "model_dump"):
        worker_payload = payload.model_dump()
    else:
        worker_payload = payload.dict()

    try:
        completed = subprocess.run(
            [sys.executable, str(WORKER_PATH)],
            input=json.dumps(worker_payload),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return RunResponse(results=_make_error_results(payload.test_cases, "Time limit exceeded"))

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "Judge worker failed").strip()
        return RunResponse(results=_make_error_results(payload.test_cases, message[:1000]))

    try:
        data = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return RunResponse(results=_make_error_results(payload.test_cases, "Judge returned invalid output"))

    results = data.get("results")
    if not isinstance(results, list):
        return RunResponse(results=_make_error_results(payload.test_cases, "Judge returned no results"))

    return RunResponse(results=results)
