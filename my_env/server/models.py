"""
Pydantic models for Government Fraud Detection OpenEnv.
Implements the full OpenEnv typed spec: Observation, Action, Reward.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Action space
# ---------------------------------------------------------------------------

class Action(BaseModel):
    """Every action the agent can take."""

    action_type: Literal[
        "read_document",
        "flag_duplicate",
        "flag_shell_company",
        "trace_ownership",
        "flag_overbilling",
        "submit_finding",
        "request_more_docs",
    ] = Field(..., description="Type of action to perform")

    document_id: Optional[str] = Field(None, description="Target document ID")
    entity_ids: Optional[List[str]] = Field(None, description="List of entity/claim IDs")
    finding_type: Optional[Literal[
        "duplicate_billing",
        "shell_company",
        "overbilling",
        "fca_violation",
        "clean",
    ]] = Field(None, description="Type of fraud finding (for submit_finding)")
    evidence: Optional[List[str]] = Field(None, description="Evidence document IDs cited")
    defendant: Optional[str] = Field(None, description="Name of defendant entity")
    amount_at_risk: Optional[float] = Field(None, description="Estimated dollar amount at risk")
    legal_basis: Optional[str] = Field(None, description="Legal statute cited e.g. 31 U.S.C. §3729")
    reasoning: Optional[str] = Field(None, description="Agent's reasoning text")
    request_target: Optional[str] = Field(
        None,
        description="Target entity/topic when requesting more docs (e.g., 'FastBuild LLC bank records')",
    )
    requested_doc_type: Optional[str] = Field(
        None,
        description="Requested document type (e.g., bank_records, audit_memo, compliance_review)",
    )

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Observation space
# ---------------------------------------------------------------------------

class DocumentSummary(BaseModel):
    doc_id: str
    doc_type: str
    title: str
    preview: str
    is_read: bool = False


class FraudSignal(BaseModel):
    signal_type: str
    description: str
    severity: Literal["low", "medium", "high", "critical"]


class Observation(BaseModel):
    """Returned by reset() and step()."""

    task_id: str = Field(..., description="Current task identifier")
    task_description: str = Field(..., description="What the agent must accomplish")
    difficulty: Literal["easy", "medium", "hard"]

    available_documents: List[DocumentSummary] = Field(
        default_factory=list,
        description="All documents available for reading"
    )
    read_documents: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full content of documents the agent has read"
    )
    detected_signals: List[FraudSignal] = Field(
        default_factory=list,
        description="Fraud signals the env has pre-flagged for the agent"
    )

    steps_taken: int = 0
    steps_remaining: int = 10
    cumulative_reward: float = 0.0
    last_action_result: Optional[str] = None
    last_action_error: Optional[str] = None
    done: bool = False
    info: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------

class Reward(BaseModel):
    """Reward returned after each step."""

    value: float = Field(..., ge=0.0, le=1.0, description="Reward this step [0,1]")
    breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Component-wise reward breakdown"
    )
    reason: str = Field("", description="Human-readable explanation")
    is_bonus: bool = False
    is_penalty: bool = False
