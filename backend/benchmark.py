"""
Benchmark runner for Government Fraud Detection.

Compares expert, distilled, and random policies across many seeds.
Use this to measure whether dynamic dataset generation is actually
making the benchmark harder and whether a policy generalizes.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from environment import GovFraudEnv
from models import Action
from train_simple import ExpertPolicy

TASKS = ["duplicate_billing", "shell_company", "fca_complaint"]


def _load_policy() -> Dict[str, Any]:
    policy_path = Path(__file__).parent / "training_outputs" / "trained_policy.json"
    if not policy_path.exists():
        return {"tasks": {}}
    return json.loads(policy_path.read_text(encoding="utf-8"))


def _extract_score(info: Dict[str, Any], current: float) -> float:
    final_score = info.get("final_score")
    if final_score is not None:
        return float(final_score)
    return current


def run_expert(task_id: str, seed: int, dynamic_data: bool) -> Tuple[float, int]:
    env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data, seed=seed)
    env.reset()
    score = 0.0
    steps = 0
    for step in ExpertPolicy.solve(env):
        _, _, done, info = env.step(Action(**step["action"]))
        steps += 1
        score = _extract_score(info, score)
        if done:
            break
    return score, steps


def run_distilled(task_id: str, seed: int, dynamic_data: bool, policy: Dict[str, Any]) -> Tuple[float, int]:
    env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data, seed=seed)
    env.reset()
    score = 0.0
    steps = 0
    task_policy = policy.get("tasks", {}).get(task_id, {})
    for action_dict in task_policy.get("distilled_actions", []):
        _, _, done, info = env.step(Action(**action_dict))
        steps += 1
        score = _extract_score(info, score)
        if done:
            break
    return score, steps


def _random_action(task_id: str, obs, rng: random.Random) -> Action:
    docs = [d.doc_id for d in obs.available_documents]
    if task_id == "duplicate_billing":
        choice = rng.random()
        if choice < 0.35:
            return Action(action_type="read_document", document_id=rng.choice(docs))
        if choice < 0.78:
            # Weak heuristic: occasionally test known likely duplicate pairs.
            candidate_pairs = [
                ("CLAIM-001", "CLAIM-002"),
                ("CLAIM-001", "CLAIM-004"),
            ]
            if rng.random() < 0.35 and all(pair_id in docs for pair_id in candidate_pairs[0]):
                a, b = rng.choice(candidate_pairs)
            else:
                a, b = rng.sample(docs, 2)
            return Action(action_type="flag_duplicate", entity_ids=[a, b], reasoning="random baseline")
        evidence_candidates = [doc_id for doc_id in ["CLAIM-001", "CLAIM-002", "CLAIM-004"] if doc_id in docs]
        if rng.random() < 0.30 and len(evidence_candidates) >= 2:
            evidence = evidence_candidates[:3]
        else:
            evidence = rng.sample(docs, k=min(2, len(docs)))
        return Action(
            action_type="submit_finding",
            finding_type=rng.choice(["duplicate_billing", "clean"]),
            defendant="Unknown",
            amount_at_risk=rng.uniform(0, 1000),
            legal_basis="31 U.S.C. §3729",
            evidence=evidence,
            reasoning="random baseline",
        )

    if task_id == "shell_company":
        choice = rng.random()
        if choice < 0.36:
            return Action(action_type="read_document", document_id=rng.choice(docs))
        if choice < 0.76:
            # Weak heuristic: sometimes choose true ownership hops.
            true_hops = [
                ("FastBuild LLC", "ConstructPro Inc"),
                ("ConstructPro Inc", "R. Holden Family Trust"),
                ("R. Holden Family Trust", "Derek Williams / Patricia Holden-Williams"),
            ]
            if rng.random() < 0.30:
                a, b = rng.choice(true_hops)
            else:
                a = rng.choice(["FastBuild LLC", "ConstructPro Inc", "R. Holden Family Trust", "James Williams", "Patricia Holden-Williams"])
                b = rng.choice(["ConstructPro Inc", "R. Holden Family Trust", "Derek Williams / Patricia Holden-Williams"])
            return Action(action_type="trace_ownership", entity_ids=[a, b], reasoning="random baseline")
        if choice < 0.90:
            return Action(action_type="flag_shell_company", entity_ids=["FastBuild LLC"], reasoning="random baseline")
        evidence_candidates = [
            doc_id
            for doc_id in ["STATE-FILING-DE-001", "STATE-FILING-NV-001", "TRUST-DOC-001", "GOV-EMPLOYEE-001"]
            if doc_id in docs
        ]
        if rng.random() < 0.25 and len(evidence_candidates) >= 3:
            evidence = evidence_candidates[:4]
        else:
            evidence = rng.sample(docs, k=min(3, len(docs)))
        return Action(
            action_type="submit_finding",
            finding_type="shell_company",
            defendant="FastBuild LLC",
            amount_at_risk=rng.uniform(0, 5_000_000),
            legal_basis="31 U.S.C. §3729",
            evidence=evidence,
            reasoning="random baseline",
        )

    choice = rng.random()
    if choice < 0.40:
        return Action(action_type="read_document", document_id=rng.choice(docs))
    if choice < 0.73:
        return Action(action_type="flag_overbilling", entity_ids=["MediSupply Corp"], reasoning="random baseline")
    if choice < 0.92:
        evidence_candidates = [
            doc_id
            for doc_id in ["CMS-CLAIM-BATCH-001", "PHYSICIAN-ORDERS-001", "EXPERT-ANALYSIS-001", "INTERNAL-EMAIL-001"]
            if doc_id in docs
        ]
        if rng.random() < 0.30 and len(evidence_candidates) >= 3:
            evidence = evidence_candidates[:4]
        else:
            evidence = rng.sample(docs, k=min(4, len(docs)))
        return Action(
            action_type="submit_finding",
            finding_type=rng.choice(["fca_violation", "overbilling", "clean"]),
            defendant=rng.choice(["MediSupply Corp", "Poole", "Unknown"]),
            amount_at_risk=rng.uniform(0, 15_000_000),
            legal_basis=rng.choice(["31 U.S.C. §3729", "False Claims Act"]),
            evidence=evidence,
            reasoning="random baseline",
        )
    return Action(action_type="trace_ownership", entity_ids=["MediSupply Corp", "Unknown"], reasoning="random baseline")


def run_random(task_id: str, seed: int, dynamic_data: bool) -> Tuple[float, int]:
    rng = random.Random(seed)
    env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data, seed=seed)
    obs = env.reset()
    score = 0.0
    steps = 0
    done = False
    while not done and steps < 30:
        action = _random_action(task_id, obs, rng)
        try:
            obs, _, done, info = env.step(action)
        except Exception:
            if obs.available_documents:
                obs, _, done, info = env.step(Action(action_type="read_document", document_id=obs.available_documents[0].doc_id))
            else:
                break
        steps += 1
        score = _extract_score(info, score)
        if done:
            break
    return score, steps


def _summarize(runs: List[Tuple[float, int]]) -> Dict[str, Any]:
    scores = [score for score, _ in runs]
    steps = [step for _, step in runs]
    success = sum(1 for score in scores if score >= 0.5)
    return {
        "n": len(runs),
        "mean_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "min_score": round(min(scores), 4) if scores else 0.0,
        "max_score": round(max(scores), 4) if scores else 0.0,
        "mean_steps": round(sum(steps) / len(steps), 2) if steps else 0.0,
        "success_rate": round(success / len(scores), 4) if scores else 0.0,
    }


def benchmark(task: str, num_seeds: int, start_seed: int, dynamic_data: bool) -> Dict[str, Any]:
    policy = _load_policy()
    seeds = list(range(start_seed, start_seed + num_seeds))
    tasks = TASKS if task == "all" else [task]

    results: Dict[str, Any] = {}
    for task_id in tasks:
        expert_runs = [run_expert(task_id, seed, dynamic_data) for seed in seeds]
        distilled_runs = [run_distilled(task_id, seed, dynamic_data, policy) for seed in seeds]
        random_runs = [run_random(task_id, seed, dynamic_data) for seed in seeds]
        results[task_id] = {
            "expert": _summarize(expert_runs),
            "distilled": _summarize(distilled_runs),
            "random": _summarize(random_runs),
        }
    return results


def _default_report_path(task: str, dynamic_data: bool) -> Path:
    output_dir = Path(__file__).parent / "training_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    mode = "dynamic" if dynamic_data else "static"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"benchmark_report_{task}_{mode}_{timestamp}.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Government Fraud Detection policies")
    parser.add_argument("--task", choices=TASKS + ["all"], default="all")
    parser.add_argument("--num-seeds", type=int, default=20, help="Number of seeds to evaluate")
    parser.add_argument("--start-seed", type=int, default=1000, help="Initial seed value")
    parser.add_argument("--dynamic-data", action="store_true", help="Use dynamic per-episode documents")
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional output path for the JSON report",
    )
    args = parser.parse_args()

    results = benchmark(args.task, args.num_seeds, args.start_seed, args.dynamic_data)
    report_path = Path(args.output) if args.output else _default_report_path(args.task, args.dynamic_data)
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), "results": results}, indent=2))


if __name__ == "__main__":
    main()
