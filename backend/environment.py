"""
Government Fraud Detection Environment
Implements the full OpenEnv spec: step() / reset() / state()
"""

from __future__ import annotations

import copy
import json
import random
from typing import Any, Dict, List, Optional, Tuple

from models import Action, Observation, Reward, DocumentSummary, FraudSignal
from data.documents import (
    TASK1_DOCUMENTS,
    TASK2_DOCUMENTS,
    TASK3_DOCUMENTS,
)
from data.dynamic_dataset import generate_dynamic_documents
from tasks.graders import (
    TASKS,
    grade_task1,
    grade_task2,
    grade_task3,
)


class GovFraudEnv:
    """
    Government Fraud Detection OpenEnv Environment.

    Simulates a fraud investigator's workflow:
    - Read messy government documents
    - Flag suspicious patterns
    - Trace ownership chains
    - Submit structured findings

    Supports 3 tasks with increasing difficulty.
    """

    TASK_DOCUMENTS = {
        "duplicate_billing": TASK1_DOCUMENTS,
        "shell_company": TASK2_DOCUMENTS,
        "fca_complaint": TASK3_DOCUMENTS,
    }

    # Pre-flagged signals shown to agent at the start of each task
    TASK_SIGNALS = {
        "duplicate_billing": [
            FraudSignal(
                signal_type="POTENTIAL_DUPLICATE",
                description="Multiple claims from PRV-8821 for patient P4421 detected",
                severity="high",
            ),
            FraudSignal(
                signal_type="SAME_DATE_SAME_PROVIDER",
                description="Two claims share patient, date, and provider — possible duplicate billing",
                severity="critical",
            ),
        ],
        "shell_company": [
            FraudSignal(
                signal_type="SOLE_SOURCE_ANOMALY",
                description="FastBuild LLC received 2 sole-source contracts ($3.19M) in 4 months",
                severity="high",
            ),
            FraudSignal(
                signal_type="REVENUE_MISMATCH",
                description="Vendor reported $180K annual revenue but received $3.19M in contracts",
                severity="critical",
            ),
            FraudSignal(
                signal_type="DELAWARE_LLC",
                description="FastBuild LLC registered at common registered agent address (1209 Orange St, Wilmington DE)",
                severity="medium",
            ),
        ],
        "fca_complaint": [
            FraudSignal(
                signal_type="ANOMALOUS_CLAIM_VOLUME",
                description="MediSupply Corp filed 847 K0831 claims — 7x industry average",
                severity="critical",
            ),
            FraudSignal(
                signal_type="WHISTLEBLOWER_TIP",
                description="Anonymous tip alleges intentional upcoding of wheelchair claims",
                severity="high",
            ),
            FraudSignal(
                signal_type="INTERNAL_COMMUNICATION",
                description="Internal emails may contain evidence of intentional billing fraud",
                severity="critical",
            ),
        ],
    }

    def __init__(
        self,
        task_id: str = "duplicate_billing",
        dynamic_data: bool = False,
        seed: Optional[int] = None,
    ):
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {list(TASKS.keys())}")
        self.task_id = task_id
        self.dynamic_data = dynamic_data
        self.seed = seed
        self._episode_counter = 0
        self._task_meta = TASKS[task_id]
        self._documents = copy.deepcopy(self.TASK_DOCUMENTS[task_id])
        self._hidden_documents: Dict[str, Dict[str, Any]] = {}
        self._obs: Optional[Observation] = None
        self._state: Dict[str, Any] = {}
        self._reset_state()

    # ------------------------------------------------------------------
    # OpenEnv API
    # ------------------------------------------------------------------

    def reset(self) -> Observation:
        """Start a fresh episode. Returns the initial observation."""
        self._episode_counter += 1
        self._documents = self._build_documents_for_episode()
        self._hidden_documents = self._build_hidden_documents_for_episode()
        self._reset_state()
        self._obs = self._build_observation()
        return self._obs

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """
        Execute one action.
        Returns: (observation, reward_value, done, info)
        """
        if self._obs is None:
            raise RuntimeError("Call reset() before step()")
        if self._state["done"]:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        # Infinite loop detection
        last_actions = self._state.get("last_actions", [])
        action_key = f"{action.action_type}:{action.document_id}:{action.entity_ids}"
        last_actions.append(action_key)
        self._state["last_actions"] = last_actions[-6:]
        if len(last_actions) >= 3 and len(set(last_actions[-3:])) == 1:
            self._state["done"] = True
            reward = Reward(
                value=0.0,
                breakdown={"loop_penalty": -0.25},
                reason="Infinite loop detected — same action repeated 3 times",
                is_penalty=True,
            )
            self._state["cumulative_reward"] = max(
                0.0, self._state["cumulative_reward"] - 0.25
            )
            self._obs = self._build_observation(
                last_result="Loop detected",
                last_error="Repeated same action 3 times — episode terminated",
            )
            info = self._build_info(reward)
            return self._obs, 0.0, True, info

        # Dispatch action
        reward, result_msg, error_msg = self._dispatch(action)

        # Accumulate reward
        self._state["steps_taken"] += 1
        self._state["cumulative_reward"] = min(
            1.0, self._state["cumulative_reward"] + reward.value
        )

        # Check episode end
        if action.action_type == "submit_finding":
            self._state["done"] = True
        elif self._state["steps_taken"] >= self._task_meta["max_steps"]:
            self._state["done"] = True

        self._obs = self._build_observation(last_result=result_msg, last_error=error_msg)
        info = self._build_info(reward)
        return self._obs, reward.value, self._state["done"], info

    def state(self) -> Dict[str, Any]:
        """Return full internal state (for debugging / evaluation)."""
        return copy.deepcopy(self._state)

    def close(self) -> None:
        """Clean up resources."""
        pass

    # ------------------------------------------------------------------
    # Action dispatcher
    # ------------------------------------------------------------------

    def _dispatch(
        self, action: Action
    ) -> Tuple[Reward, str, Optional[str]]:
        """Route action to the correct handler. Returns (reward, result, error)."""

        if action.action_type == "read_document":
            return self._action_read_document(action)

        elif action.action_type == "flag_duplicate":
            return self._action_flag_duplicate(action)

        elif action.action_type == "flag_shell_company":
            return self._action_flag_shell_company(action)

        elif action.action_type == "trace_ownership":
            return self._action_trace_ownership(action)

        elif action.action_type == "flag_overbilling":
            return self._action_flag_overbilling(action)

        elif action.action_type == "submit_finding":
            return self._action_submit_finding(action)

        elif action.action_type == "request_more_docs":
            return self._action_request_more_docs(action)

        else:
            return Reward(value=0.0, reason="Unknown action type"), \
                   "", f"Unknown action_type: {action.action_type}"

    # ------------------------------------------------------------------
    # Individual action handlers
    # ------------------------------------------------------------------

    def _action_read_document(self, action: Action) -> Tuple[Reward, str, Optional[str]]:
        doc_id = action.document_id
        if not doc_id:
            return Reward(value=0.0, reason="No document_id provided"), "", "Missing document_id"
        if doc_id not in self._documents:
            return Reward(value=0.0, reason="Document not found", is_penalty=True), \
                   "", f"Document '{doc_id}' does not exist"

        already_read = doc_id in self._state["read_documents"]
        self._state["read_documents"][doc_id] = self._documents[doc_id]["content"]

        # Small reward for reading a relevant document (first time only)
        relevance = self._document_relevance(doc_id)
        if already_read:
            self._state["cumulative_reward"] = max(
                0.0, self._state["cumulative_reward"] - 0.005
            )
            r = Reward(
                value=0.0,
                breakdown={"repeat_read_penalty": -0.005},
                reason=f"Already read {doc_id}",
                is_penalty=True,
            )
        else:
            # Investigation budget: reading always has a small cost.
            read_cost = 0.01
            net_read_reward = max(0.0, round(relevance * 0.03 - read_cost, 4))
            r = Reward(
                value=net_read_reward,
                breakdown={
                    "document_read": round(relevance * 0.03, 4),
                    "read_cost": -read_cost,
                },
                reason=f"Read document {doc_id} (relevance={relevance:.1f}, budget cost applied)",
            )
        return r, f"Document '{doc_id}' loaded successfully", None

    def _action_flag_duplicate(self, action: Action) -> Tuple[Reward, str, Optional[str]]:
        if self.task_id != "duplicate_billing":
            return Reward(value=0.0, reason="Not applicable in this task"), \
                   "", "flag_duplicate is only valid for duplicate_billing task"
        ids = action.entity_ids or []
        if len(ids) < 2:
            return Reward(value=0.0, reason="Need at least 2 IDs"), \
                   "", "Provide at least 2 claim IDs to flag as duplicates"

        pair = tuple(sorted(ids[:2]))
        if pair in self._state["flagged_pairs"]:
            return Reward(value=0.0, reason="Pair already flagged"), \
                   f"Pair {pair} already flagged", None

        self._state["flagged_pairs"].add(pair)

        # Check against ground truth immediately for partial reward
        from data.documents import TASK1_GROUND_TRUTH as gt
        exact_norm = {tuple(sorted(p)) for p in gt["exact_duplicates"]}
        near_norm = {tuple(sorted(p)) for p in gt["near_duplicates"]}

        if pair in exact_norm:
            r = Reward(value=0.40, breakdown={"exact_duplicate": 0.40},
                       reason=f"Exact duplicate found: {pair}")
        elif pair in near_norm:
            r = Reward(value=0.22, breakdown={"near_duplicate": 0.22},
                       reason=f"Near-duplicate found: {pair}")
        else:
            # False positive
            self._state["false_positive_ids"].append(ids[0])
            r = Reward(value=0.0, breakdown={"false_positive": -0.12},
                       reason=f"False positive flagged: {pair}", is_penalty=True)
            self._state["cumulative_reward"] = max(
                0.0, self._state["cumulative_reward"] - 0.12
            )
        return r, f"Flagged pair {pair} as duplicate", None

    def _action_flag_shell_company(self, action: Action) -> Tuple[Reward, str, Optional[str]]:
        if self.task_id != "shell_company":
            return Reward(value=0.0, reason="Not applicable"), \
                   "", "flag_shell_company is only valid for shell_company task"
        entity = action.entity_ids[0] if action.entity_ids else ""
        self._state["flagged_entities"].add(entity)
        r = Reward(value=0.05, breakdown={"entity_flagged": 0.05},
                   reason=f"Entity flagged as suspicious: {entity}")
        return r, f"Flagged '{entity}' as potential shell company", None

    def _action_trace_ownership(self, action: Action) -> Tuple[Reward, str, Optional[str]]:
        if self.task_id not in ("shell_company", "fca_complaint"):
            return Reward(value=0.0, reason="Not applicable"), \
                   "", "trace_ownership not applicable for this task"
        ids = action.entity_ids or []
        if len(ids) < 2:
            return Reward(value=0.0, reason="Provide parent and child entity names"), \
                   "", "Provide at least 2 entity names: [child, parent]"

        hop = tuple(ids[:2])
        if hop in self._state["traced_hops"]:
            return Reward(value=0.0, reason="Hop already traced"), \
                   f"Hop {hop} already traced", None
        self._state["traced_hops"].add(hop)

        # Check against ground truth
        from data.documents import TASK2_GROUND_TRUTH as gt
        hop_weights = [0.18, 0.22, 0.22]
        for i, (gt_hop, weight) in enumerate(zip(gt["ownership_chain"], hop_weights)):
            g0, g1 = gt_hop[0].lower(), gt_hop[1].lower()
            h0, h1 = hop[0].lower(), hop[1].lower()
            if (g0 in h0 or h0 in g0) and (g1 in h1 or h1 in g1):
                r = Reward(value=weight,
                           breakdown={f"ownership_hop_{i+1}": weight},
                           reason=f"Ownership hop {i+1} correctly traced (+{weight})")
                return r, f"Traced: {hop[0]} → {hop[1]}", None

        return Reward(value=0.0, reason=f"No match for hop {hop}"), \
               f"No ownership relationship found for {hop}", None

    def _action_flag_overbilling(self, action: Action) -> Tuple[Reward, str, Optional[str]]:
        entity = action.entity_ids[0] if action.entity_ids else ""
        self._state["flagged_entities"].add(entity)
        r = Reward(value=0.04, breakdown={"overbilling_flag": 0.04},
                   reason=f"Overbilling flagged for: {entity}")
        return r, f"Flagged '{entity}' for potential overbilling", None

    def _action_submit_finding(self, action: Action) -> Tuple[Reward, str, Optional[str]]:
        """Run the full grader and return final score."""
        finding = action.model_dump()
        self._state["submitted_finding"] = finding

        if self.task_id == "duplicate_billing":
            reward = grade_task1(
                flagged_pairs=list(self._state["flagged_pairs"]),
                false_positive_ids=self._state["false_positive_ids"],
                submitted_finding=finding,
                steps_used=self._state["steps_taken"],
                max_steps=self._task_meta["max_steps"],
            )
        elif self.task_id == "shell_company":
            hops = [list(h) for h in self._state["traced_hops"]]
            reward = grade_task2(
                ownership_hops_found=hops,
                conflict_flagged=action.finding_type in ("shell_company", "fca_violation"),
                conflicted_person=action.reasoning or "",
                submitted_finding=finding,
                steps_used=self._state["steps_taken"],
                max_steps=self._task_meta["max_steps"],
            )
        else:  # fca_complaint
            reward = grade_task3(
                submitted_finding=finding,
                evidence_cited=action.evidence or [],
                steps_used=self._state["steps_taken"],
                max_steps=self._task_meta["max_steps"],
            )

        self._state["final_score"] = reward.value
        return reward, f"Finding submitted. Final score: {reward.value:.4f}", None

    def _action_request_more_docs(self, action: Action) -> Tuple[Reward, str, Optional[str]]:
        """
        Reveal one hidden supporting document when the request is specific and timely.

        This action is optional and designed to support evidence quality, not replace
        core fraud detection performance.
        """
        if not self._hidden_documents:
            return Reward(value=0.0, reason="No additional documents available for this task"), \
                   "No additional documents available", None

        docs_read = len(self._state["read_documents"])
        if docs_read < 2:
            self._state["cumulative_reward"] = max(0.0, self._state["cumulative_reward"] - 0.03)
            return Reward(
                value=0.0,
                breakdown={"premature_request_penalty": -0.03},
                reason="Requested more docs too early",
                is_penalty=True,
            ), "Request denied: read at least 2 documents first", None

        query_parts = [
            action.request_target or "",
            action.requested_doc_type or "",
            action.reasoning or "",
            " ".join(action.entity_ids or []),
        ]
        query = " ".join(part.strip().lower() for part in query_parts if part)
        if not query:
            return Reward(value=0.0, reason="Missing request target"), \
                   "Request needs a target or requested_doc_type", "Provide request_target or requested_doc_type"

        best_doc_id: Optional[str] = None
        best_score = -1
        for doc_id, doc in self._hidden_documents.items():
            hints = [h.lower() for h in doc.get("request_hints", [])]
            score = sum(1 for hint in hints if hint in query)
            if score > best_score:
                best_score = score
                best_doc_id = doc_id

        if best_doc_id is None or best_score <= 0:
            self._state["cumulative_reward"] = max(0.0, self._state["cumulative_reward"] - 0.02)
            return Reward(
                value=0.0,
                breakdown={"bad_request_penalty": -0.02},
                reason="Request was too vague or irrelevant",
                is_penalty=True,
            ), "Request denied: target not specific enough", None

        revealed_doc = self._hidden_documents.pop(best_doc_id)
        # Keep request hints internal; they are not part of the observable corpus.
        revealed_doc.pop("request_hints", None)
        self._documents[best_doc_id] = revealed_doc
        self._state["requested_docs"].append(best_doc_id)

        return Reward(
            value=0.03,
            breakdown={"targeted_request_bonus": 0.03},
            reason=f"Additional supporting document released: {best_doc_id}",
            is_bonus=True,
        ), f"Additional document released: {best_doc_id}", None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self._state = {
            "task_id": self.task_id,
            "steps_taken": 0,
            "cumulative_reward": 0.0,
            "done": False,
            "read_documents": {},
            "flagged_pairs": set(),
            "false_positive_ids": [],
            "flagged_entities": set(),
            "traced_hops": set(),
            "submitted_finding": None,
            "final_score": None,
            "requested_docs": [],
            "last_actions": [],
        }

    def _build_observation(
        self,
        last_result: Optional[str] = None,
        last_error: Optional[str] = None,
    ) -> Observation:
        task_meta = self._task_meta
        available = [
            DocumentSummary(
                doc_id=doc_id,
                doc_type=doc["doc_type"],
                title=doc["title"],
                preview=doc["preview"],
                is_read=doc_id in self._state["read_documents"],
            )
            for doc_id, doc in self._documents.items()
        ]
        steps_taken = self._state["steps_taken"]
        max_steps = task_meta["max_steps"]

        return Observation(
            task_id=self.task_id,
            task_description=task_meta["description"],
            difficulty=task_meta["difficulty"],
            available_documents=available,
            read_documents=dict(self._state["read_documents"]),
            detected_signals=self.TASK_SIGNALS.get(self.task_id, []),
            steps_taken=steps_taken,
            steps_remaining=max(0, max_steps - steps_taken),
            cumulative_reward=round(self._state["cumulative_reward"], 4),
            last_action_result=last_result,
            last_action_error=last_error,
            done=self._state["done"],
            info={
                "flagged_pairs": [list(p) for p in self._state["flagged_pairs"]],
                "traced_hops": [list(h) for h in self._state["traced_hops"]],
                "flagged_entities": list(self._state["flagged_entities"]),
                "requested_docs": list(self._state.get("requested_docs", [])),
                "hidden_docs_remaining": len(self._hidden_documents),
                "final_score": self._state.get("final_score"),
            },
        )

    def _build_info(self, reward: Reward) -> Dict[str, Any]:
        return {
            "reward_breakdown": reward.breakdown,
            "reward_reason": reward.reason,
            "is_bonus": reward.is_bonus,
            "is_penalty": reward.is_penalty,
            "final_score": self._state.get("final_score"),
            "steps_taken": self._state["steps_taken"],
            "cumulative_reward": self._state["cumulative_reward"],
            "docs_requested": list(self._state.get("requested_docs", [])),
        }

    def _document_relevance(self, doc_id: str) -> float:
        """Relevance score [0,1] for a document to the current task's ground truth."""
        if self.task_id == "duplicate_billing":
            key_ids = {"CLAIM-001", "CLAIM-002", "CLAIM-004"}
            return 1.0 if doc_id in key_ids else 0.3
        elif self.task_id == "shell_company":
            from data.documents import TASK2_GROUND_TRUTH as gt
            key_ids = set(gt["key_evidence"])
            return 1.0 if doc_id in key_ids else 0.4
        else:
            from data.documents import TASK3_GROUND_TRUTH as gt
            key_ids = set(gt["key_evidence"])
            return 1.0 if doc_id in key_ids else 0.4

    def _build_documents_for_episode(self) -> Dict[str, Dict[str, Any]]:
        """Build the document bundle for this episode (static or dynamic)."""
        if not self.dynamic_data:
            return copy.deepcopy(self.TASK_DOCUMENTS[self.task_id])

        if self.seed is None:
            episode_seed = random.randint(1, 10**9)
        else:
            episode_seed = self.seed + self._episode_counter

        return generate_dynamic_documents(task_id=self.task_id, seed=episode_seed)

    def _build_hidden_documents_for_episode(self) -> Dict[str, Dict[str, Any]]:
        """
        Build optional supporting documents that can be unlocked via request_more_docs.

        These documents are corroborative, not mandatory for success.
        """
        if self.task_id == "duplicate_billing":
            return {
                "AUDIT-MEMO-001": {
                    "doc_type": "audit_memo",
                    "title": "Internal Audit Memo — Duplicate Claim Pattern",
                    "preview": "Auditor notes repeated claim attributes for PRV-8821 and patient P4421",
                    "content": {
                        "summary": "Claims appear duplicated with matching patient/provider/procedure signatures.",
                        "focus_claims": ["CLAIM-001", "CLAIM-002", "CLAIM-004"],
                    },
                    "request_hints": ["audit", "duplicate", "provider", "claim", "prv-8821"],
                }
            }

        if self.task_id == "shell_company":
            return {
                "BANK-LEDGER-001": {
                    "doc_type": "bank_records",
                    "title": "Bank Ledger Extract — FastBuild Settlement Account",
                    "preview": "Wire transfers from contract payouts routed to trust-managed account",
                    "content": {
                        "summary": "Federal contract funds were moved through ConstructPro-linked accounts.",
                        "entities": ["FastBuild LLC", "ConstructPro Inc", "R. Holden Family Trust"],
                    },
                    "request_hints": ["bank", "wire", "ledger", "fastbuild", "constructpro", "trust"],
                }
            }

        return {
            "COMPLIANCE-REVIEW-001": {
                "doc_type": "compliance_review",
                "title": "Clinical Compliance Review — K0831 Medical Necessity",
                "preview": "Reviewer found broad mismatch between billed coding level and supporting orders",
                "content": {
                    "summary": "A significant portion of sampled claims lacked support for K0831 billing level.",
                    "focus_docs": ["CMS-CLAIM-BATCH-001", "PHYSICIAN-ORDERS-001"],
                },
                "request_hints": ["compliance", "medical necessity", "k0831", "orders", "review"],
            }
        }
