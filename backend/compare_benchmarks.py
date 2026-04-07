"""
Compare two benchmark reports and show score deltas.

Usage:
    python compare_benchmarks.py
    python compare_benchmarks.py --old path/to/old.json --new path/to/new.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple


def _load_report(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    # Backward compatibility: if wrapper payload was saved, unwrap results.
    if isinstance(data, dict) and "results" in data and isinstance(data["results"], dict):
        return data["results"]
    return data


def _latest_two_reports(output_dir: Path) -> Tuple[Path, Path]:
    files = sorted(output_dir.glob("benchmark_report_*.json"), key=lambda p: p.stat().st_mtime)
    if len(files) < 2:
        raise RuntimeError("Need at least two benchmark_report_*.json files to compare.")
    return files[-2], files[-1]


def _metric_delta(new_val: float, old_val: float) -> float:
    return round(new_val - old_val, 4)


def compare_reports(old_report: Dict[str, Any], new_report: Dict[str, Any]) -> Dict[str, Any]:
    comparison: Dict[str, Any] = {}
    tasks = sorted(set(old_report.keys()) | set(new_report.keys()))

    for task in tasks:
        old_task = old_report.get(task, {})
        new_task = new_report.get(task, {})
        policies = sorted(set(old_task.keys()) | set(new_task.keys()))
        comparison[task] = {}

        for policy in policies:
            old_metrics = old_task.get(policy, {})
            new_metrics = new_task.get(policy, {})

            old_mean = float(old_metrics.get("mean_score", 0.0))
            new_mean = float(new_metrics.get("mean_score", 0.0))
            old_success = float(old_metrics.get("success_rate", 0.0))
            new_success = float(new_metrics.get("success_rate", 0.0))

            comparison[task][policy] = {
                "old_mean_score": old_mean,
                "new_mean_score": new_mean,
                "delta_mean_score": _metric_delta(new_mean, old_mean),
                "old_success_rate": old_success,
                "new_success_rate": new_success,
                "delta_success_rate": _metric_delta(new_success, old_success),
            }

    return comparison


def _default_output_path(output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"benchmark_comparison_{timestamp}.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two benchmark reports")
    parser.add_argument("--old", type=str, default="", help="Path to older benchmark report JSON")
    parser.add_argument("--new", type=str, default="", help="Path to newer benchmark report JSON")
    parser.add_argument("--output", type=str, default="", help="Optional output path for comparison JSON")
    args = parser.parse_args()

    output_dir = Path(__file__).parent / "training_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.old and args.new:
        old_path = Path(args.old)
        new_path = Path(args.new)
    else:
        old_path, new_path = _latest_two_reports(output_dir)

    old_report = _load_report(old_path)
    new_report = _load_report(new_path)
    comparison = compare_reports(old_report, new_report)

    output_path = Path(args.output) if args.output else _default_output_path(output_dir)
    payload = {
        "old_report": str(old_path),
        "new_report": str(new_path),
        "comparison": comparison,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"comparison_path": str(output_path), **payload}, indent=2))


if __name__ == "__main__":
    main()
