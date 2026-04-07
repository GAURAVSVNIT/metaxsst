"""
Local agent training / distillation script.

This script does not fine-tune a language model. Instead, it distills the
demonstration JSONL files produced by train_simple.py into a reusable policy
artifact and can evaluate that policy against the environment.

Usage:
    python train_agent.py
    python train_agent.py --episodes 100 --task all
    python train_agent.py --evaluate
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from environment import GovFraudEnv
from models import Action


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "training_outputs")
POLICY_FILE = os.path.join(OUTPUT_DIR, "trained_policy.json")
TASKS = ["duplicate_billing", "shell_company", "fca_complaint"]


@dataclass
class DistilledEpisode:
    task_id: str
    actions: List[Dict[str, Any]]


def _load_training_files() -> List[str]:
    pattern_full = os.path.join(OUTPUT_DIR, "training_data_*.jsonl")
    pattern_simple = os.path.join(OUTPUT_DIR, "training_data_simple_*.jsonl")
    files = sorted(glob.glob(pattern_full))
    files.extend(sorted(glob.glob(pattern_simple)))
    # Prefer full trajectories when both are present.
    return sorted(set(files), key=lambda path: ("simple" in os.path.basename(path), path))


def _parse_examples() -> List[DistilledEpisode]:
    examples: List[DistilledEpisode] = []
    for path in _load_training_files():
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if "trajectory" in record and "task_id" in record:
                    actions = [step.get("action") for step in record.get("trajectory", []) if step.get("action")]
                    if actions:
                        examples.append(DistilledEpisode(task_id=record["task_id"], actions=actions))
                    continue

                messages = record.get("messages", [])
                if len(messages) < 3:
                    continue

                user_content = messages[1].get("content", "")
                assistant_content = messages[2].get("content", "")

                task_id = None
                if user_content.startswith("Task: "):
                    task_id = user_content.splitlines()[0].replace("Task: ", "").strip()

                action_blob = None
                if "Action:" in assistant_content:
                    action_text = assistant_content.split("Action:", 1)[1].strip()
                    try:
                        action_blob = json.loads(action_text)
                    except json.JSONDecodeError:
                        pass

                if task_id and action_blob:
                    examples.append(DistilledEpisode(task_id=task_id, actions=[action_blob]))

    return examples


def train_policy(episodes: int, task: str) -> Dict[str, Any]:
    examples = _parse_examples()
    if not examples:
        raise RuntimeError(
            "No training examples found. Run train_simple.py first to generate training_outputs/*.jsonl"
        )

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for example in examples:
        if task != "all" and example.task_id != task:
            continue
        grouped[example.task_id].extend(example.actions)

    policy: Dict[str, Any] = {
        "metadata": {
            "source": "distilled_from_demonstrations",
            "episodes_requested": episodes,
            "task": task,
            "training_files": _load_training_files(),
        },
        "tasks": {},
    }

    for task_id in TASKS:
        if task != "all" and task_id != task:
            continue

        actions = grouped.get(task_id, [])
        if not actions:
            continue

        # Preserve action order while preferring the most common demonstration
        # for each step index. This is enough for these deterministic tasks.
        sequences = [example.actions for example in examples if example.task_id == task_id]
        max_len = max(len(sequence) for sequence in sequences)
        distilled_sequence: List[Dict[str, Any]] = []

        for index in range(max_len):
            bucket = []
            for sequence in sequences:
                if index < len(sequence):
                    bucket.append(json.dumps(sequence[index], sort_keys=True))
            if bucket:
                chosen = Counter(bucket).most_common(1)[0][0]
                distilled_sequence.append(json.loads(chosen))

        policy["tasks"][task_id] = {
            "num_sequences": len(sequences),
            "distilled_actions": distilled_sequence,
        }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(POLICY_FILE, "w", encoding="utf-8") as handle:
        json.dump(policy, handle, indent=2)

    return policy


def evaluate_policy(
    policy: Dict[str, Any],
    task: Optional[str] = None,
    dynamic_data: bool = False,
) -> Dict[str, float]:
    tasks = [task] if task and task != "all" else TASKS
    scores: Dict[str, float] = {}

    for task_id in tasks:
        task_policy = policy.get("tasks", {}).get(task_id)
        if not task_policy:
            scores[task_id] = 0.0
            continue

        env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data)
        obs = env.reset()
        final_score = 0.0
        for action_dict in task_policy["distilled_actions"]:
            action = Action(**action_dict)
            obs, reward, done, info = env.step(action)
            if info.get("final_score") is not None:
                final_score = info["final_score"]
            if done:
                break
        scores[task_id] = final_score

    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Distill demonstration data into a local policy")
    parser.add_argument("--episodes", type=int, default=100, help="Number of episodes requested")
    parser.add_argument("--task", choices=TASKS + ["all"], default="all", help="Task to train on")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate the distilled policy after training")
    parser.add_argument("--dynamic-data", action="store_true", help="Evaluate on dynamic per-episode datasets")
    args = parser.parse_args()

    policy = train_policy(args.episodes, args.task)
    print(f"Saved distilled policy to {POLICY_FILE}")

    if args.evaluate:
        scores = evaluate_policy(policy, args.task, dynamic_data=args.dynamic_data)
        for task_id, score in scores.items():
            print(f"{task_id}: {score:.4f}")
        if scores:
            print(f"average: {sum(scores.values()) / len(scores):.4f}")


if __name__ == "__main__":
    main()