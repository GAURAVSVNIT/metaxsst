"""
Task definitions and deterministic graders for all 3 fraud detection tasks.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple
from models import Reward
from data.documents import (
    TASK1_DOCUMENTS, TASK2_DOCUMENTS, TASK3_DOCUMENTS,
    TASK1_GROUND_TRUTH, TASK2_GROUND_TRUTH, TASK3_GROUND_TRUTH,
)

TASKS = {
    "duplicate_billing": {
        "task_id": "duplicate_billing",
        "difficulty": "easy",
        "description": (
            "You are a Medicare fraud investigator. You have received 10 Medicare claims "
            "from a batch submitted by MedCorp Associates LLC. Identify duplicate or near-duplicate "
            "billing — claims where the same service was billed more than once for the same patient. "
            "Read the documents, flag duplicates using flag_duplicate(), and submit your finding. "
            "Legitimate claims must NOT be flagged."
        ),
        "max_steps": 8,
        "document_ids": list(TASK1_DOCUMENTS.keys()),
    },
    "shell_company": {
        "task_id": "shell_company",
        "difficulty": "medium",
        "description": (
            "You are investigating procurement fraud. FastBuild LLC received $3.19M in federal "
            "contracts via sole-source awards by contracting officer James Williams. "
            "Trace the ownership chain of FastBuild LLC, identify the conflict of interest, "
            "and submit your finding with the ownership chain and amount at risk."
        ),
        "max_steps": 12,
        "document_ids": list(TASK2_DOCUMENTS.keys()),
    },
    "fca_complaint": {
        "task_id": "fca_complaint",
        "difficulty": "hard",
        "description": (
            "Build a False Claims Act complaint. MediSupply Corp allegedly overbilled Medicare "
            "for durable medical equipment. Review all documents, identify the fraud scheme, "
            "quantify the dollar amount at risk, identify defendants, and submit a complete "
            "FCA finding citing 31 U.S.C. §3729."
        ),
        "max_steps": 15,
        "document_ids": list(TASK3_DOCUMENTS.keys()),
    },
}


def _norm_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _norm_doc_id(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())


def _alias_match(value: Any, aliases: List[str]) -> bool:
    nv = _norm_text(value)
    if not nv:
        return False
    return any(_norm_text(alias) in nv or nv in _norm_text(alias) for alias in aliases if alias)


def _doc_in_evidence(evidence: List[str], target_doc_id: str) -> bool:
    target = _norm_doc_id(target_doc_id)
    return any(_norm_doc_id(doc_id) == target for doc_id in evidence)


def _doc_overlap_score(evidence: List[str], target_ids: List[str]) -> Tuple[set, int]:
    norm_targets = {_norm_doc_id(doc_id) for doc_id in target_ids}
    norm_evidence = {_norm_doc_id(doc_id) for doc_id in evidence}
    overlap = norm_evidence & norm_targets
    return overlap, len(overlap)


def grade_task1(flagged_pairs, false_positive_ids, submitted_finding, steps_used, max_steps):
    gt = TASK1_GROUND_TRUTH
    score = 0.0
    breakdown = {}
    reasons = []

    def norm(pair): return tuple(sorted(pair))
    flagged_norm = {norm(p) for p in flagged_pairs}
    exact_norm = {norm(p) for p in gt["exact_duplicates"]}
    near_norm = {norm(p) for p in gt["near_duplicates"]}

    exact_found = flagged_norm & exact_norm
    exact_score = len(exact_found) * 0.50
    breakdown["exact_duplicates"] = exact_score
    score += exact_score
    if exact_found:
        reasons.append(f"Exact duplicates found (+{exact_score:.2f})")

    near_found = flagged_norm & near_norm
    near_score = len(near_found) * 0.30
    breakdown["near_duplicates"] = near_score
    score += near_score
    if near_found:
        reasons.append(f"Near duplicates found (+{near_score:.2f})")

    fp_penalty = len(false_positive_ids) * 0.20
    breakdown["false_positive_penalty"] = -fp_penalty
    score -= fp_penalty
    if fp_penalty > 0:
        reasons.append(f"False positives (-{fp_penalty:.2f})")

    if submitted_finding:
        if submitted_finding.get("finding_type") == "duplicate_billing":
            breakdown["correct_finding_type"] = 0.10
            score += 0.10
            reasons.append("Correct finding type (+0.10)")
        elif submitted_finding.get("finding_type") == "clean":
            breakdown["correct_finding_type"] = -0.10
            score -= 0.10
            reasons.append("Incorrect clean finding (-0.10)")
        else:
            breakdown["correct_finding_type"] = -0.05
            score -= 0.05
            reasons.append("Wrong finding type (-0.05)")
        evidence = submitted_finding.get("evidence") or []
        has_claim_001 = _doc_in_evidence(evidence, "CLAIM-001")
        has_claim_002 = _doc_in_evidence(evidence, "CLAIM-002")
        if has_claim_001 and has_claim_002 and len(evidence) >= 2:
            breakdown["evidence_quality"] = 0.10
            score += 0.10
            reasons.append("Correct evidence cited (+0.10)")
        elif evidence:
            breakdown["evidence_quality"] = -0.05
            score -= 0.05
            reasons.append("Incomplete evidence (-0.05)")
        else:
            breakdown["evidence_quality"] = -0.10
            score -= 0.10
            reasons.append("Missing evidence (-0.10)")

    if not exact_found:
        breakdown["exact_missing_penalty"] = -0.10
        score -= 0.10
    if not near_found:
        breakdown["near_missing_penalty"] = -0.05
        score -= 0.05

    if steps_used <= max(1, max_steps // 2):
        breakdown["efficiency_bonus"] = 0.05
        score += 0.05
        reasons.append("Efficiency bonus (+0.05)")

    all_caught = (exact_found == exact_norm) and (near_found == near_norm) and not false_positive_ids
    if all_caught:
        breakdown["perfect_detection"] = 0.10
        score += 0.10
        reasons.append("Perfect detection (+0.10)")

    return Reward(
        value=round(max(0.0, min(1.0, score)), 4),
        breakdown=breakdown,
        reason=" | ".join(reasons) or "No fraud correctly identified",
        is_bonus=score >= 0.90,
        is_penalty=score < 0.20,
    )


def grade_task2(ownership_hops_found, conflict_flagged, conflicted_person, submitted_finding, steps_used, max_steps):
    gt = TASK2_GROUND_TRUTH
    score = 0.0
    breakdown = {}
    reasons = []

    hop_weights = [0.20, 0.25, 0.25]
    gt_hops = gt["ownership_chain"]

    entity_aliases = {
        "FastBuild LLC": ["FastBuild LLC", "FastBuild", "FastBuild Group", "FastBuild Holdings"],
        "ConstructPro Inc": ["ConstructPro Inc", "ConstructPro", "Construct Pro"],
        "R. Holden Family Trust": ["R. Holden Family Trust", "Holden Family Trust", "R Holden Trust"],
        "Derek Williams / Patricia Holden-Williams": [
            "Derek Williams / Patricia Holden-Williams",
            "Patricia Holden-Williams",
            "Patricia Holden Williams",
            "Derek Williams",
            "Holden-Williams",
        ],
    }

    def _entity_match(found_value: str, gt_value: str) -> bool:
        aliases = entity_aliases.get(gt_value, [gt_value])
        return _alias_match(found_value, aliases)

    def hops_match(found, gt_hop):
        f0 = found[0] if len(found) > 0 else ""
        f1 = found[1] if len(found) > 1 else ""
        return _entity_match(f0, gt_hop[0]) and _entity_match(f1, gt_hop[1])

    for i, (gt_hop, weight) in enumerate(zip(gt_hops, hop_weights)):
        for fh in ownership_hops_found:
            if len(fh) >= 2 and hops_match(fh, gt_hop):
                breakdown[f"hop_{i+1}"] = weight
                score += weight
                reasons.append(f"Hop {i+1} traced (+{weight:.2f})")
                break
        else:
            breakdown[f"hop_{i+1}_missing"] = -0.05
            score -= 0.05

    if conflict_flagged:
        breakdown["conflict_flagged"] = 0.10
        score += 0.10
        reasons.append("Conflict of interest flagged (+0.10)")
        cp = conflicted_person or ""
        if _alias_match(cp, ["williams", "patricia", "holden", "holden-williams"]):
            breakdown["correct_person"] = 0.10
            score += 0.10
            reasons.append("Correct conflicted person (+0.10)")
        else:
            breakdown["correct_person"] = -0.05
            score -= 0.05
            reasons.append("Wrong conflicted person (-0.05)")
    else:
        breakdown["conflict_flagged"] = -0.10
        score -= 0.10
        reasons.append("Conflict not flagged (-0.10)")

    if submitted_finding:
        if submitted_finding.get("finding_type") in ("shell_company", "fca_violation"):
            breakdown["finding_type"] = 0.05; score += 0.05
        elif submitted_finding.get("finding_type") == "clean":
            breakdown["finding_type"] = -0.10; score -= 0.10
            reasons.append("Incorrect clean finding (-0.10)")
        else:
            breakdown["finding_type"] = -0.05; score -= 0.05
        amount = submitted_finding.get("amount_at_risk") or 0
        if amount:
            rel_err = abs(amount - gt["total_amount_at_risk"]) / gt["total_amount_at_risk"]
            if rel_err < 0.15:
                breakdown["correct_amount"] = 0.04; score += 0.04
                reasons.append("Amount in tight range (+0.04)")
            elif rel_err < 0.30:
                breakdown["correct_amount"] = 0.02; score += 0.02
                reasons.append("Amount in broad range (+0.02)")
            elif rel_err < 0.50:
                breakdown["correct_amount"] = 0.0
                reasons.append("Amount weak but plausible (+0.00)")
            else:
                breakdown["correct_amount"] = -0.03; score -= 0.03
                reasons.append("Amount far off (-0.03)")
        else:
            breakdown["correct_amount"] = -0.03; score -= 0.03
            reasons.append("Missing amount (-0.03)")
        ev = set(submitted_finding.get("evidence") or [])
        overlap, overlap_count = _doc_overlap_score(list(ev), list(gt["key_evidence"]))
        ev_score = min(0.20, overlap_count * 0.06)
        breakdown["evidence"] = ev_score; score += ev_score
        if overlap:
            reasons.append(f"{len(overlap)} key docs cited (+{ev_score:.2f})")
        if ev and not overlap:
            breakdown["evidence_penalty"] = -0.10
            score -= 0.10
            reasons.append("Wrong evidence cited (-0.10)")
        if len(ev) < 3:
            breakdown["evidence_completeness"] = -0.05
            score -= 0.05
            reasons.append("Too little evidence (-0.05)")
    else:
        breakdown["finding_type"] = -0.10
        breakdown["correct_amount"] = -0.05
        score -= 0.15
        reasons.append("Missing finding (-0.15)")

    return Reward(
        value=round(max(0.0, min(1.0, score)), 4),
        breakdown=breakdown,
        reason=" | ".join(reasons) or "No ownership hops traced",
        is_bonus=score >= 0.85,
        is_penalty=score < 0.20,
    )


def grade_task3(submitted_finding, evidence_cited, steps_used, max_steps):
    gt = TASK3_GROUND_TRUTH
    score = 0.0
    breakdown = {}
    reasons = []

    if not submitted_finding:
        return Reward(value=0.0, breakdown={}, reason="No finding submitted", is_penalty=True)

    defendant = (submitted_finding.get("defendant") or "").lower()
    if _alias_match(defendant, ["MediSupply Corp", "Medi Supply Corp", "MediSupply"]):
        breakdown["defendant"] = 0.25; score += 0.25
        reasons.append("Correct defendant (+0.25)")
    elif _alias_match(defendant, ["poole", "sloane"]):
        breakdown["defendant"] = 0.03; score += 0.03
        reasons.append("Individual defendant (partial) (+0.03)")
    elif defendant:
        breakdown["defendant"] = -0.05
        score -= 0.05
        reasons.append("Wrong defendant (-0.05)")

    ft = (submitted_finding.get("finding_type") or "").lower()
    if ft in ("fca_violation", "overbilling"):
        breakdown["violation_type"] = 0.15; score += 0.15
        reasons.append("Correct violation type (+0.15)")
    elif ft == "clean":
        breakdown["violation_type"] = -0.10
        score -= 0.10
        reasons.append("Incorrect clean finding (-0.10)")

    amount = submitted_finding.get("amount_at_risk") or 0
    if amount and gt["amount_at_risk_min"] <= amount <= gt["amount_at_risk_max"]:
        breakdown["amount"] = 0.10; score += 0.10
        reasons.append(f"Amount ${amount:,.0f} in range (+0.10)")
    elif amount:
        mid = (gt["amount_at_risk_min"] + gt["amount_at_risk_max"]) / 2
        rel_err = abs(amount - mid) / mid
        if rel_err < 0.30:
            breakdown["amount"] = 0.06; score += 0.06
            reasons.append("Amount in broad range (+0.06)")
        elif rel_err < 0.50:
            breakdown["amount"] = 0.02; score += 0.02
            reasons.append("Amount weak but plausible (+0.02)")
        else:
            breakdown["amount"] = -0.03
            score -= 0.03
            reasons.append("Wrong amount range (-0.03)")
    else:
        breakdown["amount"] = -0.03
        score -= 0.03
        reasons.append("Missing amount (-0.03)")

    ev_set = set(evidence_cited)
    overlap, overlap_count = _doc_overlap_score(list(ev_set), list(gt["key_evidence"]))
    if overlap_count >= 3:
        ev_score = 0.30
    elif overlap_count == 2:
        ev_score = 0.16
    elif overlap_count == 1:
        ev_score = 0.04
    else:
        ev_score = 0.0
    breakdown["evidence"] = ev_score; score += ev_score
    if overlap:
        reasons.append(f"{len(overlap)} key docs (+{ev_score:.2f})")
    if evidence_cited and not overlap:
        breakdown["evidence_penalty"] = -0.10
        score -= 0.10
        reasons.append("No key evidence cited (-0.10)")

    if len(evidence_cited or []) < 3:
        breakdown["evidence_completeness"] = -0.05
        score -= 0.05
        reasons.append("Too little evidence (-0.05)")

    legal = (submitted_finding.get("legal_basis") or "").lower()
    if "3729" in legal or "false claims act" in legal:
        breakdown["legal_basis"] = 0.10; score += 0.10
        reasons.append("Correct statute (+0.10)")
    elif "false claims" in legal:
        breakdown["legal_basis"] = 0.05; score += 0.05

    valid_ids = {
        "ANON-TIP-001","CMS-CLAIM-BATCH-001","CMS-CLAIM-BATCH-002",
        "PHYSICIAN-ORDERS-001","INTERNAL-EMAIL-001","PATIENT-COMPLAINT-001",
        "CORPORATE-FILING-001","REIMBURSEMENT-POLICY-001",
        "FINANCIAL-RECORDS-001","EXPERT-ANALYSIS-001",
    }
    false_ev = {_norm_doc_id(doc_id) for doc_id in ev_set} - {_norm_doc_id(doc_id) for doc_id in valid_ids}
    if not false_ev:
        breakdown["no_hallucination"] = 0.15; score += 0.15
        reasons.append("No hallucinated evidence (+0.15)")
    else:
        p = min(0.30, len(false_ev) * 0.10)
        breakdown["hallucination_penalty"] = -p; score -= p
        reasons.append(f"Hallucinated docs (-{p:.2f})")

    reasoning = (submitted_finding.get("reasoning") or "").lower()
    if any(k in reasoning for k in ["upcode", "upcoding", "k0831"]):
        breakdown["scheme_bonus"] = 0.05; score += 0.05
        reasons.append("Scheme identified (+0.05)")

    if any(v == -0.10 for v in breakdown.values()) or any(v == -0.05 for v in breakdown.values()):
        breakdown["weak_submission_penalty"] = -0.05
        score -= 0.05

    if not submitted_finding.get("defendant"):
        breakdown["missing_defendant"] = -0.05
        score -= 0.05
        reasons.append("Missing defendant (-0.05)")

    return Reward(
        value=round(max(0.0, min(1.0, score)), 4),
        breakdown=breakdown,
        reason=" | ".join(reasons) or "Incomplete finding",
        is_bonus=score >= 0.80,
        is_penalty=score < 0.20,
    )
