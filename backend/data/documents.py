"""
Synthetic government fraud documents for all 3 tasks.
All data is entirely fictional. Generated deterministically so graders are reproducible.
"""

from __future__ import annotations
from typing import Any, Dict


# ---------------------------------------------------------------------------
# TASK 1 — Easy: Duplicate Medicare billing detection
# ---------------------------------------------------------------------------

TASK1_DOCUMENTS: Dict[str, Dict[str, Any]] = {
    "CLAIM-001": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-001",
        "preview": "Patient P4421, Procedure 99213, Date 2024-03-15, $185.00",
        "content": {
            "claim_id": "MC-2024-001",
            "patient_id": "P4421",
            "patient_name": "Robert Haines",
            "procedure_code": "99213",
            "procedure_desc": "Office visit – established patient, moderate complexity",
            "service_date": "2024-03-15",
            "billed_amount": 185.00,
            "provider_id": "PRV-8821",
            "provider_name": "MedCorp Associates LLC",
            "npi": "1234567890",
            "diagnosis_code": "Z00.00",
            "place_of_service": "11 - Office",
            "submitted_date": "2024-03-22",
        },
    },
    "CLAIM-002": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-002",
        "preview": "Patient P4421, Procedure 99213, Date 2024-03-15, $185.00",
        "content": {
            "claim_id": "MC-2024-002",
            "patient_id": "P4421",
            "patient_name": "Robert Haines",
            "procedure_code": "99213",
            "procedure_desc": "Office visit – established patient, moderate complexity",
            "service_date": "2024-03-15",
            "billed_amount": 185.00,
            "provider_id": "PRV-8821",
            "provider_name": "MedCorp Associates LLC",
            "npi": "1234567890",
            "diagnosis_code": "Z00.00",
            "place_of_service": "11 - Office",
            "submitted_date": "2024-03-28",
            "note": "Resubmission - original claim lost",
        },
    },
    "CLAIM-003": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-003",
        "preview": "Patient P8832, Procedure 93000, Date 2024-03-20, $320.00",
        "content": {
            "claim_id": "MC-2024-003",
            "patient_id": "P8832",
            "patient_name": "Linda Forsythe",
            "procedure_code": "93000",
            "procedure_desc": "Electrocardiogram, routine ECG with 12 leads",
            "service_date": "2024-03-20",
            "billed_amount": 320.00,
            "provider_id": "PRV-3342",
            "provider_name": "HeartCare Diagnostics Inc",
            "npi": "9876543210",
            "diagnosis_code": "I10",
            "place_of_service": "22 - Outpatient Hospital",
            "submitted_date": "2024-03-25",
        },
    },
    "CLAIM-004": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-004",
        "preview": "Patient P4421, Procedure 99213, Date 2024-03-16, $185.00",
        "content": {
            "claim_id": "MC-2024-004",
            "patient_id": "P4421",
            "patient_name": "Robert Haines",
            "procedure_code": "99213",
            "procedure_desc": "Office visit – established patient, moderate complexity",
            "service_date": "2024-03-16",
            "billed_amount": 185.00,
            "provider_id": "PRV-8821",
            "provider_name": "MedCorp Associates LLC",
            "npi": "1234567890",
            "diagnosis_code": "Z00.00",
            "place_of_service": "11 - Office",
            "submitted_date": "2024-03-30",
            "note": "Date corrected from original submission",
        },
    },
    "CLAIM-005": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-005",
        "preview": "Patient P2271, Procedure 99214, Date 2024-03-18, $265.00",
        "content": {
            "claim_id": "MC-2024-005",
            "patient_id": "P2271",
            "patient_name": "Marcus Webb",
            "procedure_code": "99214",
            "procedure_desc": "Office visit – established patient, moderate-high complexity",
            "service_date": "2024-03-18",
            "billed_amount": 265.00,
            "provider_id": "PRV-8821",
            "provider_name": "MedCorp Associates LLC",
            "npi": "1234567890",
            "diagnosis_code": "J06.9",
            "place_of_service": "11 - Office",
            "submitted_date": "2024-03-24",
        },
    },
    "CLAIM-006": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-006",
        "preview": "Patient P5519, Procedure 71046, Date 2024-03-22, $410.00",
        "content": {
            "claim_id": "MC-2024-006",
            "patient_id": "P5519",
            "patient_name": "Dorothy Callahan",
            "procedure_code": "71046",
            "procedure_desc": "X-ray, chest, 2 views",
            "service_date": "2024-03-22",
            "billed_amount": 410.00,
            "provider_id": "PRV-7710",
            "provider_name": "Radiology Partners Group",
            "npi": "1122334455",
            "diagnosis_code": "R05.9",
            "place_of_service": "22 - Outpatient Hospital",
            "submitted_date": "2024-03-26",
        },
    },
    "CLAIM-007": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-007",
        "preview": "Patient P9934, Procedure 99213, Date 2024-03-14, $185.00",
        "content": {
            "claim_id": "MC-2024-007",
            "patient_id": "P9934",
            "patient_name": "Albert Nguyen",
            "procedure_code": "99213",
            "procedure_desc": "Office visit – established patient, moderate complexity",
            "service_date": "2024-03-14",
            "billed_amount": 185.00,
            "provider_id": "PRV-8821",
            "provider_name": "MedCorp Associates LLC",
            "npi": "1234567890",
            "diagnosis_code": "M54.5",
            "place_of_service": "11 - Office",
            "submitted_date": "2024-03-20",
        },
    },
    "CLAIM-008": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-008",
        "preview": "Patient P3387, Procedure 80053, Date 2024-03-19, $95.00",
        "content": {
            "claim_id": "MC-2024-008",
            "patient_id": "P3387",
            "patient_name": "Sandra Kim",
            "procedure_code": "80053",
            "procedure_desc": "Comprehensive metabolic panel",
            "service_date": "2024-03-19",
            "billed_amount": 95.00,
            "provider_id": "PRV-4421",
            "provider_name": "LabFirst Diagnostics LLC",
            "npi": "5544332211",
            "diagnosis_code": "E11.9",
            "place_of_service": "81 - Independent Laboratory",
            "submitted_date": "2024-03-23",
        },
    },
    "CLAIM-009": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-009",
        "preview": "Patient P6612, Procedure 99215, Date 2024-03-21, $355.00",
        "content": {
            "claim_id": "MC-2024-009",
            "patient_id": "P6612",
            "patient_name": "Franklin Torres",
            "procedure_code": "99215",
            "procedure_desc": "Office visit – established patient, high complexity",
            "service_date": "2024-03-21",
            "billed_amount": 355.00,
            "provider_id": "PRV-9908",
            "provider_name": "Premier Health Associates",
            "npi": "6677889900",
            "diagnosis_code": "F32.1",
            "place_of_service": "11 - Office",
            "submitted_date": "2024-03-27",
        },
    },
    "CLAIM-010": {
        "doc_type": "medicare_claim",
        "title": "Medicare Claim #MC-2024-010",
        "preview": "Patient P1143, Procedure 90837, Date 2024-03-17, $175.00",
        "content": {
            "claim_id": "MC-2024-010",
            "patient_id": "P1143",
            "patient_name": "Helen Okafor",
            "procedure_code": "90837",
            "procedure_desc": "Psychotherapy, 60 minutes",
            "service_date": "2024-03-17",
            "billed_amount": 175.00,
            "provider_id": "PRV-2255",
            "provider_name": "Behavioral Health Partners",
            "npi": "3344556677",
            "diagnosis_code": "F41.1",
            "place_of_service": "11 - Office",
            "submitted_date": "2024-03-22",
        },
    },
}

TASK1_GROUND_TRUTH = {
    "exact_duplicates": [("CLAIM-001", "CLAIM-002")],
    "near_duplicates": [("CLAIM-001", "CLAIM-004")],
    "clean_claims": ["CLAIM-003", "CLAIM-005", "CLAIM-006", "CLAIM-007", "CLAIM-008", "CLAIM-009", "CLAIM-010"],
}


# ---------------------------------------------------------------------------
# TASK 2 — Medium: Shell company ownership tracing
# ---------------------------------------------------------------------------

TASK2_DOCUMENTS: Dict[str, Dict[str, Any]] = {
    "CONTRACT-001": {
        "doc_type": "government_contract",
        "title": "Federal Construction Contract #FC-2023-0847",
        "preview": "FastBuild LLC awarded $2.3M for GSA facility renovation",
        "content": {
            "contract_id": "FC-2023-0847",
            "vendor_name": "FastBuild LLC",
            "vendor_ein": "47-3821044",
            "award_amount": 2_300_000.00,
            "award_date": "2023-08-12",
            "project": "GSA Region 4 Facility Renovation – Atlanta",
            "contracting_officer": "J. Williams",
            "contracting_officer_id": "CO-4421",
            "period_of_performance": "2023-09-01 to 2024-03-31",
            "solicitation_type": "Sole Source – 8(a) Program",
            "naics_code": "236220",
        },
    },
    "CONTRACT-002": {
        "doc_type": "government_contract",
        "title": "Federal IT Contract #IT-2023-1102",
        "preview": "FastBuild LLC awarded $890K for network infrastructure",
        "content": {
            "contract_id": "IT-2023-1102",
            "vendor_name": "FastBuild LLC",
            "vendor_ein": "47-3821044",
            "award_amount": 890_000.00,
            "award_date": "2023-11-03",
            "project": "DOT Regional Office Network Upgrade",
            "contracting_officer": "J. Williams",
            "contracting_officer_id": "CO-4421",
            "period_of_performance": "2023-12-01 to 2024-06-30",
            "solicitation_type": "Sole Source – 8(a) Program",
            "naics_code": "541512",
            "note": "Outside vendor's primary NAICS code",
        },
    },
    "VENDOR-REG-001": {
        "doc_type": "vendor_registration",
        "title": "SAM.gov Registration – FastBuild LLC",
        "preview": "FastBuild LLC, Delaware LLC, EIN 47-3821044",
        "content": {
            "legal_name": "FastBuild LLC",
            "dba": None,
            "entity_type": "Limited Liability Company",
            "state_of_incorporation": "Delaware",
            "ein": "47-3821044",
            "cage_code": "8FB21",
            "uei": "FBLLC2023US",
            "registered_agent": "National Registered Agents Inc",
            "principal_address": "1209 Orange Street, Wilmington, DE 19801",
            "primary_naics": "236220",
            "8a_certified": True,
            "8a_certifying_entity": "SBA Region 4",
            "annual_revenue_reported": 180_000,
            "employees_reported": 3,
            "founded": "2022-11-14",
            "note": "Annual revenue inconsistent with contract awards",
        },
    },
    "STATE-FILING-DE-001": {
        "doc_type": "state_corporate_filing",
        "title": "Delaware Division of Corporations – FastBuild LLC",
        "preview": "FastBuild LLC 100% owned by ConstructPro Inc",
        "content": {
            "entity_name": "FastBuild LLC",
            "file_number": "DE-7734821",
            "formation_date": "2022-11-14",
            "registered_agent": "National Registered Agents Inc",
            "members": [
                {
                    "name": "ConstructPro Inc",
                    "ownership_pct": 100,
                    "state": "Nevada",
                    "ein": "88-4421033",
                }
            ],
            "manager": "ConstructPro Inc",
            "status": "Active",
        },
    },
    "STATE-FILING-NV-001": {
        "doc_type": "state_corporate_filing",
        "title": "Nevada Secretary of State – ConstructPro Inc",
        "preview": "ConstructPro Inc owned by R. Holden Family Trust",
        "content": {
            "entity_name": "ConstructPro Inc",
            "file_number": "NV-C20190044231",
            "formation_date": "2019-03-22",
            "registered_agent": "Nevada Corporate Services LLC",
            "officers": [
                {"title": "President", "name": "Redacted per NV statute §78.150"},
                {"title": "Secretary", "name": "Redacted per NV statute §78.150"},
            ],
            "shareholders": [
                {
                    "name": "R. Holden Family Trust",
                    "trust_state": "Delaware",
                    "ownership_pct": 100,
                    "trustee": "See trust documents",
                }
            ],
            "status": "Active",
            "note": "Nevada does not require disclosure of beneficial owners",
        },
    },
    "TRUST-DOC-001": {
        "doc_type": "trust_document",
        "title": "R. Holden Family Trust – Declaration of Trust",
        "preview": "Trustee: Raymond T. Holden. Beneficiaries include family members.",
        "content": {
            "trust_name": "R. Holden Family Trust",
            "trust_state": "Delaware",
            "trust_date": "2018-09-01",
            "trustee": "Raymond T. Holden",
            "trustee_address": "412 Magnolia Drive, Atlanta, GA 30301",
            "beneficiaries": [
                {"name": "Raymond T. Holden", "relationship": "Grantor"},
                {"name": "Patricia Holden-Williams", "relationship": "Spouse"},
                {"name": "Derek Williams", "relationship": "Son-in-law"},
            ],
            "assets": "All shares of ConstructPro Inc and affiliated entities",
        },
    },
    "GOV-EMPLOYEE-001": {
        "doc_type": "government_employee_record",
        "title": "Federal Employee Record – CO-4421",
        "preview": "Contracting Officer James Williams, GSA Region 4",
        "content": {
            "employee_id": "CO-4421",
            "name": "James Williams",
            "agency": "General Services Administration",
            "region": "Region 4 – Southeast",
            "title": "Senior Contracting Officer",
            "gs_grade": "GS-14",
            "office": "Atlanta Federal Center",
            "start_date": "2015-06-01",
            "financial_disclosure_filed": True,
            "financial_disclosure_year": 2023,
            "spouse_name": "Patricia Holden-Williams",
            "note": "Financial disclosure does not list ConstructPro Inc or FastBuild LLC",
        },
    },
    "INVOICE-001": {
        "doc_type": "invoice",
        "title": "Invoice INV-FB-2023-0092 from FastBuild LLC",
        "preview": "FastBuild LLC invoices $2.3M – no itemized breakdown",
        "content": {
            "invoice_id": "INV-FB-2023-0092",
            "vendor": "FastBuild LLC",
            "bill_to": "GSA Region 4",
            "contract_ref": "FC-2023-0847",
            "invoice_date": "2024-03-28",
            "line_items": [
                {
                    "description": "Facility renovation services – per contract",
                    "quantity": 1,
                    "unit_price": 2_300_000.00,
                    "total": 2_300_000.00,
                }
            ],
            "total_amount": 2_300_000.00,
            "payment_terms": "Net 30",
            "bank_account": "Routing 021000021 / Acct 887743921",
            "note": "No itemized labor or material breakdown provided",
        },
    },
}

TASK2_GROUND_TRUTH = {
    "ownership_chain": [
        ("FastBuild LLC", "ConstructPro Inc"),
        ("ConstructPro Inc", "R. Holden Family Trust"),
        ("R. Holden Family Trust", "Derek Williams / Patricia Holden-Williams"),
    ],
    "conflict_of_interest": True,
    "conflicted_officer": "James Williams",
    "conflicted_family_member": "Patricia Holden-Williams",
    "total_amount_at_risk": 3_190_000.00,
    "violation_type": "shell_company",
    "key_evidence": [
        "STATE-FILING-DE-001",
        "STATE-FILING-NV-001",
        "TRUST-DOC-001",
        "GOV-EMPLOYEE-001",
    ],
}


# ---------------------------------------------------------------------------
# TASK 3 — Hard: Full FCA complaint from mixed docs
# ---------------------------------------------------------------------------

TASK3_DOCUMENTS: Dict[str, Dict[str, Any]] = {
    "ANON-TIP-001": {
        "doc_type": "anonymous_tip",
        "title": "Anonymous Whistleblower Tip #WT-2024-0033",
        "preview": "Tip alleges MediSupply Corp overbilling CMS for durable medical equipment",
        "content": {
            "tip_id": "WT-2024-0033",
            "received_date": "2024-01-15",
            "allegation": (
                "MediSupply Corp has been systematically billing Medicare for "
                "power wheelchairs (HCPCS K0831) at the highest reimbursement tier "
                "regardless of patient need or physician documentation. "
                "Many patients received standard manual wheelchairs or nothing at all. "
                "The scheme has been ongoing since at least Q3 2022. "
                "The billing manager, Karen Sloane, instructed staff to always select K0831."
            ),
            "tipster_relation": "Former billing department employee",
            "estimated_fraud_amount": "Could be tens of millions",
        },
    },
    "CMS-CLAIM-BATCH-001": {
        "doc_type": "cms_claim_batch",
        "title": "CMS Claims Extract – MediSupply Corp 2022-2024",
        "preview": "847 claims for K0831 power wheelchair, $14.2M total",
        "content": {
            "provider": "MediSupply Corp",
            "provider_npi": "3344556600",
            "claim_period": "2022-07-01 to 2024-01-31",
            "hcpcs_billed": "K0831",
            "hcpcs_description": "Power wheelchair, group 3 heavy duty",
            "total_claims": 847,
            "total_billed": 14_200_000.00,
            "medicare_paid": 11_360_000.00,
            "avg_per_claim": 16_000.00 + (800_000 / 847),
            "comparison_industry_avg_k0831_claims": 120,
            "comparison_industry_avg_billed": 2_016_000.00,
            "anomaly_flag": "Claims volume 7x industry average for provider size",
        },
    },
    "CMS-CLAIM-BATCH-002": {
        "doc_type": "cms_claim_batch",
        "title": "CMS Claims Extract – MediSupply Corp K0001 comparison",
        "preview": "Only 12 claims for K0001 standard manual wheelchair in same period",
        "content": {
            "provider": "MediSupply Corp",
            "provider_npi": "3344556600",
            "claim_period": "2022-07-01 to 2024-01-31",
            "hcpcs_billed": "K0001",
            "hcpcs_description": "Standard manual wheelchair",
            "total_claims": 12,
            "total_billed": 36_000.00,
            "medicare_paid": 28_800.00,
            "note": "K0831 to K0001 ratio is 70:1; industry norm is approximately 3:1",
        },
    },
    "PHYSICIAN-ORDERS-001": {
        "doc_type": "physician_orders",
        "title": "Physician Order Sample – 50 random K0831 claims",
        "preview": "38 of 50 sampled physician orders do not support K0831 level",
        "content": {
            "sample_size": 50,
            "orders_reviewed": 50,
            "orders_supporting_k0831": 12,
            "orders_not_supporting_k0831": 38,
            "orders_missing_entirely": 8,
            "common_documented_needs": [
                "Ambulation assistance for moderate distances",
                "Post-surgical mobility aid",
                "Arthritis-related limited mobility",
            ],
            "k0831_clinical_requirement": (
                "Patient must have severe neurological or musculoskeletal condition "
                "preventing any self-propulsion; requires detailed functional assessment"
            ),
            "finding": "76% of sampled orders do not meet K0831 medical necessity criteria",
        },
    },
    "INTERNAL-EMAIL-001": {
        "doc_type": "internal_email",
        "title": "Internal Email Chain – Billing Department",
        "preview": "Karen Sloane instructs staff to always bill K0831",
        "content": {
            "email_chain": [
                {
                    "date": "2022-09-14",
                    "from": "Karen Sloane <k.sloane@medisupply.example>",
                    "to": "Billing Staff <billing@medisupply.example>",
                    "subject": "Wheelchair billing – updated protocol",
                    "body": (
                        "Team, going forward please select K0831 for all wheelchair "
                        "orders unless the physician specifically writes K0001. "
                        "K0831 reimbursement is significantly higher and we need to "
                        "hit our Q4 targets. If you have questions see me directly. "
                        "Do not put this in writing elsewhere."
                    ),
                },
                {
                    "date": "2022-09-15",
                    "from": "T. Reyes <t.reyes@medisupply.example>",
                    "to": "Karen Sloane <k.sloane@medisupply.example>",
                    "subject": "Re: Wheelchair billing – updated protocol",
                    "body": "Understood. What if the doctor's order says standard?",
                },
                {
                    "date": "2022-09-15",
                    "from": "Karen Sloane <k.sloane@medisupply.example>",
                    "to": "T. Reyes <t.reyes@medisupply.example>",
                    "subject": "Re: Re: Wheelchair billing – updated protocol",
                    "body": "Bill K0831 anyway. We'll say it was a clerical upgrade.",
                },
            ],
        },
    },
    "PATIENT-COMPLAINT-001": {
        "doc_type": "patient_complaints",
        "title": "CMS Patient Complaint Log – MediSupply Corp",
        "preview": "23 complaints: received wrong equipment or no equipment",
        "content": {
            "complaints_reviewed": 23,
            "complaint_period": "2022-07-01 to 2024-01-31",
            "complaint_types": {
                "received_manual_wheelchair_billed_for_power": 9,
                "received_no_equipment_but_medicare_billed": 7,
                "received_different_model_than_billed": 5,
                "billing_dispute_other": 2,
            },
            "sample_complaint": (
                "Patient ID P7741: Was told she qualified for a power wheelchair. "
                "Received a manual chair. Medicare was billed $16,500 for K0831. "
                "Her doctor never ordered a power wheelchair."
            ),
        },
    },
    "CORPORATE-FILING-001": {
        "doc_type": "corporate_filing",
        "title": "MediSupply Corp – Delaware Certificate of Incorporation",
        "preview": "MediSupply Corp incorporated 2020, CEO Richard Poole",
        "content": {
            "entity_name": "MediSupply Corp",
            "ein": "61-4421887",
            "state": "Delaware",
            "incorporated": "2020-02-18",
            "registered_agent": "The Corporation Trust Company",
            "officers": [
                {"title": "CEO", "name": "Richard Poole"},
                {"title": "CFO", "name": "Sandra Poole"},
                {"title": "Billing Manager", "name": "Karen Sloane"},
            ],
            "cms_provider_enrollment": "Active – Enrolled 2020-06-01",
            "medicare_provider_number": "33-4455660",
        },
    },
    "REIMBURSEMENT-POLICY-001": {
        "doc_type": "cms_policy",
        "title": "CMS LCD L33702 – Power Mobility Devices",
        "preview": "K0831 requires documented severe functional limitation",
        "content": {
            "lcd_number": "L33702",
            "title": "Power Mobility Devices – Coverage Criteria",
            "effective_date": "2020-01-01",
            "k0831_criteria": [
                "Severe neurological condition (e.g., ALS, MS, SCI) OR",
                "Severe musculoskeletal condition preventing any self-propulsion",
                "Face-to-face evaluation by treating physician documenting functional limitation",
                "Seven-element order from physician within 45 days of evaluation",
                "Home assessment confirming power wheelchair can be used in the home",
            ],
            "k0831_rate_2023": 16_488.00,
            "k0001_rate_2023": 3_000.00,
            "difference": 13_488.00,
            "false_claims_implication": (
                "Billing K0831 without meeting coverage criteria constitutes "
                "a false claim under 31 U.S.C. §3729(a)(1)(A)"
            ),
        },
    },
    "FINANCIAL-RECORDS-001": {
        "doc_type": "financial_records",
        "title": "MediSupply Corp – Bank Records Summary 2022-2024",
        "preview": "Medicare payments of $11.36M deposited; large transfers to Poole family LLCs",
        "content": {
            "institution": "First National Bank",
            "account_holder": "MediSupply Corp",
            "period": "2022-07-01 to 2024-01-31",
            "medicare_deposits": 11_360_000.00,
            "transfers_out": [
                {
                    "recipient": "Poole Ventures LLC",
                    "amount": 4_200_000.00,
                    "description": "Management consulting fees",
                },
                {
                    "recipient": "Coastal Properties LLC",
                    "amount": 2_100_000.00,
                    "description": "Lease payments",
                },
                {
                    "recipient": "Personal account – R. Poole",
                    "amount": 1_800_000.00,
                    "description": "Salary distributions",
                },
            ],
            "note": "Poole Ventures LLC and Coastal Properties LLC are owned by Poole family members",
        },
    },
    "EXPERT-ANALYSIS-001": {
        "doc_type": "expert_analysis",
        "title": "Independent DME Billing Expert Report",
        "preview": "Expert estimates $8.2M in improper Medicare payments to MediSupply Corp",
        "content": {
            "expert": "Dr. Judith Kwan, CPC, CPMA",
            "methodology": (
                "Reviewed 847 K0831 claims, sampled 50 physician orders, "
                "applied CMS LCD L33702 criteria to determine medical necessity compliance"
            ),
            "findings": {
                "non_compliant_claims_estimated_pct": 76,
                "estimated_non_compliant_claims": 644,
                "avg_overpayment_per_claim": 12_744.00,
                "total_estimated_overpayment": 8_207_136.00,
                "treble_damages_fca": 24_621_408.00,
                "civil_penalties_per_claim": "Between $13,946 and $27,894",
            },
            "conclusion": (
                "The billing pattern is inconsistent with any legitimate clinical practice. "
                "The internal email chain confirms intentional upcoding. "
                "This constitutes a violation of 31 U.S.C. §3729(a)(1)(A) and (B)."
            ),
        },
    },
}

TASK3_GROUND_TRUTH = {
    "defendant": "MediSupply Corp",
    "defendant_individuals": ["Richard Poole", "Karen Sloane"],
    "violation_type": "fca_violation",
    "violation_statutes": ["31 U.S.C. §3729(a)(1)(A)", "31 U.S.C. §3729(a)(1)(B)"],
    "amount_at_risk_min": 8_000_000.00,
    "amount_at_risk_max": 11_400_000.00,
    "key_evidence": [
        "INTERNAL-EMAIL-001",
        "CMS-CLAIM-BATCH-001",
        "PHYSICIAN-ORDERS-001",
        "ANON-TIP-001",
    ],
    "scheme": "upcoding_dme",
    "treble_damages": 24_621_408.00,
}
