"""
Dynamic dataset generation for Government Fraud Detection tasks.

This module perturbs the base synthetic documents at episode reset time to
reduce memorization while keeping the task schema and key identifiers stable.
"""

from __future__ import annotations

import copy
import random
from datetime import date, timedelta
from typing import Any, Dict, Optional

from data.documents import TASK1_DOCUMENTS, TASK2_DOCUMENTS, TASK3_DOCUMENTS


def _rng(seed: Optional[int] = None) -> random.Random:
    return random.Random(seed) if seed is not None else random.Random()


def _shift_date(r: random.Random, iso_date: str, max_days: int = 21) -> str:
    year, month, day = [int(x) for x in iso_date.split("-")]
    d = date(year, month, day)
    return (d + timedelta(days=r.randint(-max_days, max_days))).isoformat()


def _jitter_amount(r: random.Random, value: float, pct: float) -> float:
    factor = 1.0 + r.uniform(-pct, pct)
    return round(value * factor, 2)


def _add_noise_documents(
    docs: Dict[str, Dict[str, Any]],
    r: random.Random,
    count: int,
    prefix: str,
    doc_type: str,
    title_prefix: str,
    preview_prefix: str,
) -> None:
    """Add distractor documents that look plausible but are irrelevant."""
    for index in range(1, count + 1):
        suffix = r.randint(100, 999)
        doc_id = f"{prefix}-D{index:02d}-{suffix}"
        docs[doc_id] = {
            "doc_type": doc_type,
            "title": f"{title_prefix} {index:02d} / Ref {suffix}",
            "preview": f"{preview_prefix} {suffix}",
            "content": {
                "note": "Irrelevant distractor document generated for robustness testing",
                "reference": suffix,
                "seeded_variant": True,
            },
        }


def generate_dynamic_documents(task_id: str, seed: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
    """
    Return per-episode task documents with randomized surface details.

    Notes:
    - Key document IDs remain unchanged so existing policies and graders still work.
    - Ground-truth relationships remain intact; only surface details are varied.
    """
    r = _rng(seed)

    if task_id == "duplicate_billing":
        docs = copy.deepcopy(TASK1_DOCUMENTS)

        patient_names = ["Robert Haines", "Martha Stone", "Peter Larson", "Nina Ortiz", "Daniel Brooks"]
        provider_names = ["MedCorp Associates LLC", "Summit Care Group", "Northfield Medical Partners"]
        patient_name = r.choice(patient_names)
        provider_name = r.choice(provider_names)
        patient_alias = f"{patient_name} (obfuscated)" if r.random() < 0.5 else patient_name
        provider_alias = r.choice([
            provider_name,
            provider_name.replace("Associates", "Assoc."),
            provider_name.replace("Partners", "Ptnrs"),
        ])
        service_date = _shift_date(r, "2024-03-15", max_days=30)
        near_service_date = _shift_date(r, service_date, max_days=2)
        billed_amount = _jitter_amount(r, 185.0, pct=0.12)

        for claim_id, doc in docs.items():
            content = doc["content"]
            content["submitted_date"] = _shift_date(r, content["submitted_date"], max_days=30)
            content["billed_amount"] = _jitter_amount(r, float(content["billed_amount"]), pct=0.15)

            if claim_id in {"CLAIM-001", "CLAIM-002", "CLAIM-004"}:
                content["patient_name"] = patient_alias
                content["provider_name"] = provider_alias
                content["provider_id"] = "PRV-8821"
                content["procedure_code"] = "99213"
                content["billed_amount"] = billed_amount

            if claim_id in {"CLAIM-001", "CLAIM-002"}:
                content["service_date"] = service_date
            elif claim_id == "CLAIM-004":
                content["service_date"] = near_service_date

            doc["preview"] = (
                f"Patient {content['patient_id']}, Procedure {content['procedure_code']}, "
                f"Date {content['service_date']}, ${content['billed_amount']:.2f}"
            )

        _add_noise_documents(
            docs,
            r,
            count=2,
            prefix="CLAIM",
            doc_type="medicare_claim",
            title_prefix="Medicare Claim Appendix",
            preview_prefix="Extra claim reference",
        )

        return docs

    if task_id == "shell_company":
        docs = copy.deepcopy(TASK2_DOCUMENTS)

        contract_1 = docs["CONTRACT-001"]["content"]
        contract_2 = docs["CONTRACT-002"]["content"]
        contract_1["award_date"] = _shift_date(r, contract_1["award_date"], max_days=60)
        contract_2["award_date"] = _shift_date(r, contract_2["award_date"], max_days=60)
        contract_1["project"] = r.choice([
            "GSA Region 4 Facility Renovation - Atlanta",
            "Federal Archive Retrofit - Atlanta",
            "Regional Operations Building Upgrade - Atlanta",
        ])
        contract_2["project"] = r.choice([
            "DOT Regional Office Network Upgrade",
            "Transport Systems Security Refresh",
            "Regional Data Backbone Modernization",
        ])

        vendor_reg = docs["VENDOR-REG-001"]["content"]
        vendor_reg["legal_name"] = r.choice(["FastBuild LLC", "FastBuild Group LLC", "FastBuild Holdings LLC"])
        vendor_reg["annual_revenue_reported"] = int(_jitter_amount(r, float(vendor_reg["annual_revenue_reported"]), pct=0.35))
        vendor_reg["employees_reported"] = max(2, int(round(_jitter_amount(r, float(vendor_reg["employees_reported"]), pct=0.4))))

        docs["TRUST-DOC-001"]["content"]["trust_date"] = _shift_date(r, docs["TRUST-DOC-001"]["content"]["trust_date"], max_days=180)
        docs["INVOICE-001"]["content"]["invoice_date"] = _shift_date(r, docs["INVOICE-001"]["content"]["invoice_date"], max_days=45)
        docs["GOV-EMPLOYEE-001"]["content"]["title"] = r.choice([
            "Senior Contracting Officer",
            "Contracting Officer IV",
            "Federal Procurement Officer",
        ])

        docs["CONTRACT-001"]["preview"] = (
            f"FastBuild LLC awarded ${contract_1['award_amount'] / 1_000_000:.2f}M for {contract_1['project']}"
        )
        docs["CONTRACT-002"]["preview"] = (
            f"FastBuild LLC awarded ${contract_2['award_amount'] / 1_000_000:.2f}M for {contract_2['project']}"
        )
        docs["VENDOR-REG-001"]["preview"] = (
            "FastBuild LLC, Delaware LLC, "
            f"reported revenue ${vendor_reg['annual_revenue_reported']:,}"
        )
        docs["TRUST-DOC-001"]["preview"] = (
            f"Trustee: {docs['TRUST-DOC-001']['content']['trustee']}. "
            f"Trust date {docs['TRUST-DOC-001']['content']['trust_date']}"
        )

        _add_noise_documents(
            docs,
            r,
            count=2,
            prefix="CORP",
            doc_type="corporate_filing",
            title_prefix="State Filing Appendix",
            preview_prefix="Irrelevant state filing ref",
        )

        return docs

    if task_id == "fca_complaint":
        docs = copy.deepcopy(TASK3_DOCUMENTS)

        tip = docs["ANON-TIP-001"]["content"]
        tip["received_date"] = _shift_date(r, tip["received_date"], max_days=75)
        tip["estimated_fraud_amount"] = r.choice([
            "Could be in the high single-digit millions",
            "Likely over $8M based on claims volume",
            "Potentially between $8M and $12M",
        ])
        tip["tipster_relation"] = r.choice([
            "Former billing department employee",
            "Former coding specialist",
            "Former claims auditor",
        ])

        claim_batch = docs["CMS-CLAIM-BATCH-001"]["content"]
        total_claims = int(round(_jitter_amount(r, float(claim_batch["total_claims"]), pct=0.1)))
        total_claims = max(700, min(950, total_claims))
        claim_batch["total_claims"] = total_claims
        claim_batch["comparison_industry_avg_k0831_claims"] = max(
            90,
            min(180, int(round(_jitter_amount(r, 120.0, pct=0.2)))),
        )

        sampled_orders = docs["PHYSICIAN-ORDERS-001"]["content"]
        sampled_orders["orders_supporting_k0831"] = r.randint(10, 16)
        sampled_orders["orders_not_supporting_k0831"] = 50 - sampled_orders["orders_supporting_k0831"]
        sampled_orders["orders_missing_entirely"] = r.randint(5, 11)

        complaints = docs["PATIENT-COMPLAINT-001"]["content"]
        complaints["complaints_reviewed"] = r.randint(20, 35)

        expert = docs["EXPERT-ANALYSIS-001"]["content"]["findings"]
        expert["non_compliant_claims_estimated_pct"] = r.randint(70, 82)
        expert["estimated_non_compliant_claims"] = int(
            total_claims * (expert["non_compliant_claims_estimated_pct"] / 100.0)
        )

        docs["CMS-CLAIM-BATCH-001"]["preview"] = (
            f"{total_claims} claims for K0831 power wheelchair, ${claim_batch['total_billed'] / 1_000_000:.1f}M total"
        )
        docs["PHYSICIAN-ORDERS-001"]["preview"] = (
            f"{sampled_orders['orders_not_supporting_k0831']} of 50 sampled physician orders do not support K0831 level"
        )
        docs["PATIENT-COMPLAINT-001"]["preview"] = (
            f"{complaints['complaints_reviewed']} complaints: received wrong equipment or no equipment"
        )
        docs["EXPERT-ANALYSIS-001"]["preview"] = (
            "Expert estimates improper Medicare payments in multi-million range "
            f"with {expert['non_compliant_claims_estimated_pct']}% non-compliance"
        )

        _add_noise_documents(
            docs,
            r,
            count=3,
            prefix="MISC",
            doc_type="misc_ledger",
            title_prefix="Miscellaneous Appendix",
            preview_prefix="Irrelevant operational note",
        )

        return docs

    raise ValueError(f"Unsupported task_id for dynamic generation: {task_id}")
