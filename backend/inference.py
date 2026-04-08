"""
Inference Script — Government Fraud Detection OpenEnv
=====================================================
Runs an LLM agent against all 3 tasks using the OpenAI client.
Emits mandatory [START] / [STEP] / [END] log format.

Required env vars:
  API_BASE_URL   LLM endpoint   (default: https://router.huggingface.co/v1)
  MODEL_NAME     Model name     (default: Qwen/Qwen2.5-72B-Instruct)
  HF_TOKEN       API key

Usage:
  python inference.py
  python inference.py --task duplicate_billing
  python inference.py --task shell_company
  python inference.py --task fca_complaint
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY", "hf_placeholder")
BENCHMARK = "gov-fraud-detection"
MAX_STEPS = 10
TEMPERATURE = 0.2
MAX_TOKENS = 1024
SUCCESS_THRESHOLD = 0.50

TASKS = ["duplicate_billing", "shell_company", "fca_complaint"]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert government fraud investigator AI agent operating inside an OpenEnv environment.

You will receive observations containing government documents (Medicare claims, corporate filings, contracts, emails, etc.) and pre-flagged fraud signals.

Your goal: detect fraud, trace ownership chains, and submit a structured finding.

AVAILABLE ACTIONS (respond with exactly one JSON action per turn):

1. Read a document:
{"action_type": "read_document", "document_id": "<doc_id>"}

2. Flag duplicate claims (Task 1):
{"action_type": "flag_duplicate", "entity_ids": ["CLAIM-001", "CLAIM-002"], "reasoning": "Same patient, date, provider, amount"}

3. Trace ownership (Task 2):
{"action_type": "trace_ownership", "entity_ids": ["FastBuild LLC", "ConstructPro Inc"], "reasoning": "Delaware filing shows 100% ownership"}

4. Flag shell company (Task 2):
{"action_type": "flag_shell_company", "entity_ids": ["FastBuild LLC"], "reasoning": "Revenue mismatch, sole-source awards"}

5. Flag overbilling (Task 3):
{"action_type": "flag_overbilling", "entity_ids": ["MediSupply Corp"], "reasoning": "7x industry average K0831 claims"}

6. Request additional supporting docs (optional):
{"action_type": "request_more_docs", "request_target": "FastBuild LLC bank records", "requested_doc_type": "bank_records", "reasoning": "Need corroboration for ownership-linked fund flow"}

7. Submit final finding:
{"action_type": "submit_finding",
 "finding_type": "duplicate_billing|shell_company|overbilling|fca_violation|clean",
 "defendant": "<name>",
 "amount_at_risk": <float>,
 "legal_basis": "31 U.S.C. §3729",
 "evidence": ["DOC-ID-1", "DOC-ID-2"],
 "reasoning": "<your reasoning>"}

STRATEGY:
- You are working under a strict investigation budget
- You have limited steps; avoid brute-force reading
- Some documents are irrelevant noise and should be ignored unless needed
- Each unnecessary read_document action hurts final efficiency
- First read the pre-flagged signals carefully
- Read the most suspicious documents first
- Use request_more_docs only if evidence is still insufficient after initial review
- Build evidence before submitting
- Be precise — false positives are penalized
- Always submit a finding before running out of steps

SHELL COMPANY CHECKLIST (Task 2):
- Before submit_finding, complete at least 2 trace_ownership hops
- Include conflict-of-interest context in reasoning (Williams/Holden relation)
- Cite at least 3 evidence documents
- If evidence is thin, use request_more_docs for bank_records before submitting

Respond ONLY with valid JSON. No prose, no markdown, no explanation outside the JSON.
"""

# ---------------------------------------------------------------------------
# Logging helpers (mandatory format)
# ---------------------------------------------------------------------------

def log_start(task: str, model: str) -> None:
    print(f"[START] task={task} env={BENCHMARK} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_str = error if error else "null"
    done_str = "true" if done else "false"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_str}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_str = "true" if success else "false"
    print(f"[END] success={success_str} steps={steps} rewards={rewards_str}", flush=True)


# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------

def make_client() -> OpenAI:
    return OpenAI(api_key=API_KEY, base_url=API_BASE_URL)


def call_llm(client: OpenAI, messages: List[Dict[str, str]]) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Action parsing
# ---------------------------------------------------------------------------

def parse_action(raw: str) -> Optional[Dict[str, Any]]:
    """Extract JSON action from LLM response."""
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end])
            except Exception:
                pass
    return None


# ---------------------------------------------------------------------------
# Environment interaction (via HTTP to local server, or direct import)
# ---------------------------------------------------------------------------

def run_episode_direct(task_id: str, client: OpenAI, dynamic_data: bool = False) -> Dict[str, Any]:
    """
    Run one episode directly importing the environment (no HTTP server needed).
    This is the primary mode for the baseline script.
    """
    from environment import GovFraudEnv
    from models import Action

    env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data)
    obs = env.reset()

    rewards: List[float] = []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    step_num = 0
    done = False
    final_score = 0.0

    log_start(task_id, MODEL_NAME)

    while not done and step_num < MAX_STEPS:
        # Build observation summary for LLM
        obs_summary = _build_obs_summary(obs)
        messages.append({"role": "user", "content": obs_summary})

        # Call LLM
        try:
            raw_response = call_llm(client, messages)
        except Exception as e:
            log_step(step_num + 1, "llm_error", 0.0, True, str(e))
            log_end(False, step_num, rewards)
            return {"task": task_id, "success": False, "score": 0.0, "steps": step_num}

        messages.append({"role": "assistant", "content": raw_response})

        # Parse action
        action_dict = parse_action(raw_response)
        if action_dict is None:
            action_str = "invalid_json"
            log_step(step_num + 1, action_str, 0.0, False, "Could not parse JSON action")
            rewards.append(0.0)
            step_num += 1
            # Inject error back to LLM
            messages.append({
                "role": "user",
                "content": "ERROR: Your response was not valid JSON. Respond with ONLY a JSON action object."
            })
            continue

        # Build Action object
        try:
            action = Action(**action_dict)
        except Exception as e:
            action_str = action_dict.get("action_type", "unknown")
            log_step(step_num + 1, action_str, 0.0, False, f"Invalid action: {e}")
            rewards.append(0.0)
            step_num += 1
            continue

        action_str = _action_to_str(action)

        # Shell-company guardrail: discourage premature submission before
        # tracing ownership and gathering sufficient evidence.
        if task_id == "shell_company" and _is_shell_submit_too_early(action, obs):
            guard_msg = (
                "Submit blocked: incomplete shell-company investigation. "
                "Trace ownership hops (>=2), include conflict reasoning, and cite >=3 evidence docs "
                "before submit_finding."
            )
            log_step(step_num + 1, action_str, 0.0, False, guard_msg)
            rewards.append(0.0)
            step_num += 1
            messages.append({"role": "user", "content": f"ERROR: {guard_msg}"})
            continue

        # Execute step
        try:
            obs, reward, done, info = env.step(action)
        except Exception as e:
            log_step(step_num + 1, action_str, 0.0, True, str(e))
            log_end(False, step_num, rewards)
            return {"task": task_id, "success": False, "score": 0.0, "steps": step_num}

        error_msg = obs.last_action_error
        rewards.append(reward)
        step_num += 1

        log_step(step_num, action_str, reward, done, error_msg)

        if info.get("final_score") is not None:
            final_score = info["final_score"]

    success = final_score >= SUCCESS_THRESHOLD
    log_end(success, step_num, rewards)

    return {
        "task": task_id,
        "success": success,
        "score": final_score,
        "steps": step_num,
        "rewards": rewards,
        "cumulative_reward": sum(rewards),
    }


def _build_obs_summary(obs) -> str:
    """Convert observation to a concise LLM-readable string."""
    lines = [
        f"=== TASK: {obs.task_id} ({obs.difficulty}) ===",
        f"Description: {obs.task_description}",
        f"Steps remaining: {obs.steps_remaining} | Cumulative reward: {obs.cumulative_reward:.3f}",
        "",
    ]

    if obs.last_action_result:
        lines.append(f"Last action result: {obs.last_action_result}")
    if obs.last_action_error:
        lines.append(f"⚠ Error: {obs.last_action_error}")

    lines.append("\n=== FRAUD SIGNALS ===")
    for sig in obs.detected_signals:
        lines.append(f"[{sig.severity.upper()}] {sig.signal_type}: {sig.description}")

    lines.append("\n=== AVAILABLE DOCUMENTS ===")
    for doc in obs.available_documents:
        status = "[READ]" if doc.is_read else "[UNREAD]"
        lines.append(f"{status} {doc.doc_id} | {doc.doc_type} | {doc.preview}")

    if obs.read_documents:
        lines.append("\n=== DOCUMENT CONTENTS ===")
        for doc_id, content in obs.read_documents.items():
            lines.append(f"\n--- {doc_id} ---")
            lines.append(json.dumps(content, indent=2, default=str)[:1500])

    if obs.info.get("flagged_pairs"):
        lines.append(f"\nAlready flagged pairs: {obs.info['flagged_pairs']}")
    if obs.info.get("traced_hops"):
        lines.append(f"Already traced hops: {obs.info['traced_hops']}")

    if obs.done:
        lines.append(f"\n=== EPISODE DONE | Final score: {obs.info.get('final_score', 'N/A')} ===")

    return "\n".join(lines)


def _action_to_str(action) -> str:
    parts = [action.action_type]
    if action.document_id:
        parts.append(action.document_id)
    if action.entity_ids:
        parts.append(",".join(action.entity_ids[:2]))
    if action.finding_type:
        parts.append(action.finding_type)
    return "(" + "|".join(parts) + ")"


def _is_shell_submit_too_early(action, obs) -> bool:
    if action.action_type != "submit_finding":
        return False

    traced_hops = obs.info.get("traced_hops") or []
    evidence = action.evidence or []
    reasoning = (action.reasoning or "").lower()

    if len(traced_hops) < 2:
        return True
    if action.finding_type not in {"shell_company", "fca_violation"}:
        return True
    if len(evidence) < 3:
        return True
    if not any(token in reasoning for token in ["williams", "holden", "spouse", "conflict"]):
        return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Government Fraud Detection — Inference Script")
    parser.add_argument(
        "--task",
        choices=TASKS + ["all"],
        default="all",
        help="Which task(s) to run",
    )
    parser.add_argument(
        "--dynamic-data",
        action="store_true",
        help="Run against dynamic per-episode datasets",
    )
    args = parser.parse_args()

    client = make_client()
    tasks_to_run = TASKS if args.task == "all" else [args.task]

    all_results = []
    for task_id in tasks_to_run:
        print(f"\n{'='*60}", flush=True)
        print(f"Running task: {task_id}", flush=True)
        print(f"{'='*60}", flush=True)
        result = run_episode_direct(task_id, client, dynamic_data=args.dynamic_data)
        all_results.append(result)
        time.sleep(1)  # Brief pause between tasks

    # Summary
    print("\n" + "="*60, flush=True)
    print("BASELINE RESULTS SUMMARY", flush=True)
    print("="*60, flush=True)
    for r in all_results:
        status = "SUCCESS" if r["success"] else "FAIL"
        print(
            f"  [{status}] {r['task']:25s} score={r['score']:.4f} steps={r['steps']}",
            flush=True,
        )
    avg = sum(r["score"] for r in all_results) / len(all_results) if all_results else 0
    print(f"\n  Average score: {avg:.4f}", flush=True)
    print(f"  Model: {MODEL_NAME}", flush=True)
    print(f"  API base: {API_BASE_URL}", flush=True)


if __name__ == "__main__":
    main()
