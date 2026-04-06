# Government Fraud Detection — OpenEnv

An AI agent training environment that simulates real-world government fraud investigation workflows. Agents read messy government documents, trace financial relationships, and submit structured fraud findings — scored deterministically against ground truth.

Inspired by Garry Tan's YC request: *"Infra for Government Fraud Hunters"* and the False Claims Act ecosystem.

---

## Environment Description

The environment places an agent in the role of a government fraud investigator. Across 3 tasks of increasing difficulty, the agent must:

- Read and interpret realistic synthetic government documents
- Identify fraud patterns (duplicate billing, shell company ownership, systematic upcoding)
- Take targeted investigative actions
- Submit a structured finding with evidence and legal basis

The agent never executes queries or accesses external systems — all evaluation is self-contained and deterministic.

---

## Action Space

| Action | Parameters | Description |
|---|---|---|
| `read_document` | `document_id` | Open a specific document for full content |
| `flag_duplicate` | `entity_ids` (2 claim IDs) | Mark two claims as duplicate billing |
| `trace_ownership` | `entity_ids` ([child, parent]) | Assert an ownership relationship |
| `flag_shell_company` | `entity_ids` | Flag entity as potential shell company |
| `flag_overbilling` | `entity_ids` | Flag entity for overbilling |
| `submit_finding` | `finding_type`, `defendant`, `amount_at_risk`, `legal_basis`, `evidence`, `reasoning` | Submit final fraud finding (triggers grader) |
| `request_more_docs` | — | Request additional documents (none available) |

All actions are Pydantic-typed `Action` objects.

---

## Observation Space

Each call to `reset()` and `step()` returns a typed `Observation` with:

| Field | Type | Description |
|---|---|---|
| `task_id` | str | Current task identifier |
| `task_description` | str | What the agent must accomplish |
| `difficulty` | easy\|medium\|hard | Task difficulty level |
| `available_documents` | List[DocumentSummary] | All documents with preview and read status |
| `read_documents` | Dict[str, Any] | Full content of documents already read |
| `detected_signals` | List[FraudSignal] | Pre-flagged anomalies (severity: low/medium/high/critical) |
| `steps_taken` | int | Steps used so far |
| `steps_remaining` | int | Steps remaining before forced termination |
| `cumulative_reward` | float | Running reward total |
| `last_action_result` | str\|null | Human-readable result of last action |
| `last_action_error` | str\|null | Error message if action failed |
| `done` | bool | Whether the episode has ended |

---

## Tasks

### Task 1 — Duplicate Billing (Easy)
**Target score: ≥ 0.70**

The agent receives 10 Medicare claims from a single provider batch. Two are exact duplicates (same patient, date, procedure, provider, amount). One is a near-duplicate with a date shifted by one day. The agent must flag all fraud without false positives.

**Ground truth:**
- Exact duplicate: `(CLAIM-001, CLAIM-002)` → +0.45
- Near-duplicate: `(CLAIM-001, CLAIM-004)` → +0.25
- False positive: any other pair → −0.12 each
- Correct finding type + evidence → +0.20
- Perfect detection bonus → +0.10

**Max steps:** 8

---

### Task 2 — Shell Company Tracing (Medium)
**Target score: ≥ 0.60**

FastBuild LLC received $3.19M in sole-source federal contracts awarded by contracting officer James Williams. The agent must trace a 3-hop ownership chain to reveal that Williams' spouse is a beneficial owner of the vendor — a clear conflict of interest.

**Ownership chain (each hop = partial credit):**
1. FastBuild LLC → ConstructPro Inc (+0.20)
2. ConstructPro Inc → R. Holden Family Trust (+0.25)
3. R. Holden Family Trust → Patricia Holden-Williams (+0.25)

Conflict of interest identification: +0.10 | Correct person: +0.10

**Max steps:** 12

---

### Task 3 — FCA Complaint Construction (Hard)
**Target score: ≥ 0.50 for frontier models**

MediSupply Corp filed 847 Medicare claims for K0831 power wheelchairs (7x industry average). Internal emails confirm intentional upcoding. The agent must construct a complete False Claims Act complaint across 10 heterogeneous documents.

**Scoring rubric:**
| Dimension | Weight |
|---|---|
| Correct defendant (MediSupply Corp) | 0.20 |
| Correct violation type (fca_violation/overbilling) | 0.15 |
| Amount at risk in [$8M–$11.4M] | 0.15 |
| 3+ key evidence documents cited | up to 0.20 |
| Legal basis: 31 U.S.C. §3729 | 0.10 |
| No hallucinated evidence | 0.20 |
| Upcoding scheme identified (bonus) | 0.05 |

**Max steps:** 15

---

## Reward Function

The reward is **dense** — the agent receives signal at every step, not just at the end.

| Signal | Reward |
|---|---|
| Read a relevant document (first time) | +0.01 to +0.03 |
| Correct duplicate flagged (exact) | +0.40 |
| Correct duplicate flagged (near) | +0.22 |
| False positive duplicate flagged | −0.12 |
| Correct ownership hop traced | +0.18 to +0.22 |
| Correct final finding submitted | up to 1.0 (via grader) |
| Efficiency bonus (solved in ≤ half steps) | +0.05 |
| Perfect detection bonus | +0.10 |
| Infinite loop (same action 3x) | −0.25 + episode end |

All rewards capped at 1.0. Penalties can reduce score to 0.0 minimum.

---

## Setup & Usage

### Local (direct)

```bash
git clone <your-repo>
cd gov-fraud-detection

pip install -r requirements.txt

# Run the API server
python app.py

# Validate spec compliance
curl http://localhost:7860/validate

# Run baseline inference
export HF_TOKEN=your_token
python inference.py
# or a specific task:
python inference.py --task duplicate_billing
```

### Docker

```bash
docker build -t gov-fraud-env .
docker run -p 7860:7860 \
  -e HF_TOKEN=your_token \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  gov-fraud-env
```

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `HF_TOKEN` | Yes | — | Hugging Face / API key |
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | LLM endpoint |
| `MODEL_NAME` | No | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `PORT` | No | `7860` | Server port |

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/tasks` | GET | List all tasks with metadata |
| `/reset` | POST | Start new episode `{"task_id": "...", "session_id": "..."}` |
| `/step` | POST | Execute action `{"action": {...}, "session_id": "..."}` |
| `/state` | GET | Full internal state (for debugging) |
| `/validate` | GET | OpenEnv spec validation |

---

## Baseline Scores

Measured with `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Inference API:

| Task | Difficulty | Expected Score |
|---|---|---|
| duplicate_billing | Easy | 0.70 |
| shell_company | Medium | 0.45 |
| fca_complaint | Hard | 0.35 |
| **Average** | | **0.50** |

A perfect agent scores 1.0 on all tasks.

---

## Project Structure

```
gov-fraud-detection/
├── app.py              # FastAPI REST server (OpenEnv endpoints)
├── environment.py      # GovFraudEnv class (step/reset/state)
├── models.py           # Pydantic models: Action, Observation, Reward
├── inference.py        # Baseline LLM agent with mandatory log format
├── openenv.yaml        # OpenEnv spec metadata
├── requirements.txt
├── Dockerfile
├── data/
│   └── documents.py    # Synthetic fraud documents for all 3 tasks
└── tasks/
    └── graders.py      # Deterministic graders + task metadata
```

---

## Design Decisions

**Why government fraud?** The FCA recovers billions annually but the investigation process is manual and slow. This environment directly mirrors the real workflow: read documents, trace relationships, build a complaint. Agents trained here could accelerate real fraud recovery.

**Why partial rewards?** Binary rewards give no training signal during an episode. Each document read, each ownership hop traced, and each correct flag contributes incrementally — giving agents a gradient to follow even before the final submission.

**Why synthetic data?** All documents are entirely fictional but structurally realistic (real procedure codes, real legal statutes, real HCPCS codes, real FCA citation format). This allows deterministic grading without any dependency on real government data.

**Correctness as a hard constraint:** In Task 3, citing hallucinated evidence documents incurs a −0.05 penalty per document. This penalizes LLMs that make up document IDs — a critical behavior to discourage in real investigative settings.

---

## License

MIT — see LICENSE file.
