"""
FastAPI application exposing the OpenEnv REST API for Government Fraud Detection.
Endpoints: POST /reset, POST /step, GET /state, GET /health, GET /tasks
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import Action, Observation, Reward
from environment import GovFraudEnv

app = FastAPI(
    title="Government Fraud Detection — OpenEnv",
    description=(
        "AI agent training environment for government fraud detection. "
        "Simulates Medicare duplicate billing, shell company tracing, and FCA complaints."
    ),
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# One environment instance per session (stateful)
_envs: Dict[str, GovFraudEnv] = {}


def _get_env(session_id: str = "default") -> GovFraudEnv:
    if session_id not in _envs:
        raise HTTPException(status_code=400, detail="Call /reset first to initialize environment")
    return _envs[session_id]


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "duplicate_billing"
    session_id: str = "default"
    dynamic_data: bool = False
    seed: Optional[int] = None


class StepRequest(BaseModel):
    action: Action
    session_id: str = "default"


class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "env": "gov-fraud-detection", "version": "1.0.0"}


@app.get("/tasks")
def list_tasks():
    """List all available tasks with metadata."""
    from tasks.graders import TASKS
    return {
        task_id: {
            "difficulty": meta["difficulty"],
            "description": meta["description"][:200] + "...",
            "max_steps": meta["max_steps"],
            "num_documents": len(meta["document_ids"]),
        }
        for task_id, meta in TASKS.items()
    }


@app.post("/reset")
def reset(req: ResetRequest) -> Dict[str, Any]:
    """Initialize or restart the environment for a given task."""
    valid_tasks = ["duplicate_billing", "shell_company", "fca_complaint"]
    if req.task_id not in valid_tasks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_id. Choose from: {valid_tasks}"
        )
    env = GovFraudEnv(task_id=req.task_id, dynamic_data=req.dynamic_data, seed=req.seed)
    _envs[req.session_id] = env
    obs = env.reset()
    return obs.model_dump()


@app.post("/step")
def step(req: StepRequest) -> StepResponse:
    """Execute one action and return observation, reward, done, info."""
    env = _get_env(req.session_id)
    try:
        obs, reward, done, info = env.step(req.action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StepResponse(
        observation=obs.model_dump(),
        reward=reward,
        done=done,
        info=info,
    )


@app.get("/state")
def state(session_id: str = "default") -> Dict[str, Any]:
    """Return full internal state (for debugging and evaluation)."""
    env = _get_env(session_id)
    s = env.state()
    # Serialise sets
    s["flagged_pairs"] = [list(p) for p in s.get("flagged_pairs", set())]
    s["flagged_entities"] = list(s.get("flagged_entities", set()))
    s["traced_hops"] = [list(h) for h in s.get("traced_hops", set())]
    return s


@app.get("/validate")
def validate(dynamic_data: bool = False):
    """OpenEnv spec validation endpoint."""
    results = {}
    for task_id in ["duplicate_billing", "shell_company", "fca_complaint"]:
        env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data)
        obs = env.reset()
        assert obs.task_id == task_id
        action = Action(action_type="read_document", document_id=obs.available_documents[0].doc_id)
        o2, r, done, info = env.step(action)
        assert 0.0 <= r <= 1.0
        assert isinstance(done, bool)
        s = env.state()
        assert "steps_taken" in s
        results[task_id] = {"status": "pass", "initial_docs": len(obs.available_documents)}
    return {"validation": "passed", "tasks": results}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
