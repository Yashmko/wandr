#!/usr/bin/env python3
"""Summarize WANDR Harbor job outputs for observability and CI regression tracking."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import quantiles
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _event_latency_sec(events_path: Path) -> float | None:
    try:
        rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    except Exception:
        return None
    if not rows:
        return None
    start = rows[0].get("time")
    end = rows[-1].get("time")
    if not isinstance(start, str) or not isinstance(end, str):
        return None
    try:
        from datetime import datetime

        return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    except Exception:
        return None


def _failure_kind(trial_dir: Path) -> str:
    if (trial_dir / "verifier" / "error.json").exists():
        return "verifier_error"
    if (trial_dir / "agent" / "status.json").exists():
        status = _load_json(trial_dir / "agent" / "status.json")
        restart_summary = status.get("restart_summary") or {}
        if restart_summary.get("failure_taxonomy"):
            return str(restart_summary["failure_taxonomy"])
    return "unknown"


def summarize_job(job_dir: Path) -> dict[str, Any]:
    trial_dirs = sorted(path for path in job_dir.iterdir() if path.is_dir())
    costs: list[float] = []
    input_tokens = 0
    output_tokens = 0
    latencies: list[float] = []
    provider_costs: dict[str, float] = {}
    failures = Counter()
    provider_rewards: dict[str, list[float]] = {}

    completed = 0
    for trial in trial_dirs:
        reward_path = trial / "verifier" / "reward.json"
        status_path = trial / "agent" / "status.json"
        result_path = trial / "agent" / "result.json"

        if reward_path.exists():
            completed += 1
            reward = _load_json(reward_path)
            if isinstance(reward.get("reward"), int | float):
                provider = "unknown"
                if status_path.exists():
                    provider = str((_load_json(status_path).get("endpoint") or "unknown"))
                provider_rewards.setdefault(provider, []).append(float(reward["reward"]))

        if status_path.exists() and result_path.exists():
            status = _load_json(status_path)
            result = _load_json(result_path)
            provider = str(status.get("endpoint") or "unknown")
            usage = result.get("usage") or {}
            cost = result.get("cost_usd")
            if isinstance(cost, int | float):
                cost_f = float(cost)
                costs.append(cost_f)
                provider_costs[provider] = provider_costs.get(provider, 0.0) + cost_f
            if isinstance(usage.get("total_input_tokens"), int):
                input_tokens += int(usage["total_input_tokens"])
            elif isinstance(usage.get("input_tokens"), int):
                input_tokens += int(usage["input_tokens"])
            if isinstance(usage.get("output_tokens"), int):
                output_tokens += int(usage["output_tokens"])

        latency = _event_latency_sec(trial / "agent" / "events.jsonl")
        if latency is not None:
            latencies.append(latency)

        if (trial / "verifier" / "error.json").exists() or not reward_path.exists():
            failures[_failure_kind(trial)] += 1

    provider_comparison = {
        provider: {
            "trials": len(rewards),
            "avg_reward": (sum(rewards) / len(rewards)) if rewards else None,
            "total_cost_usd": provider_costs.get(provider, 0.0),
        }
        for provider, rewards in sorted(provider_rewards.items())
    }

    latency_percentiles = None
    if latencies:
        if len(latencies) == 1:
            p50 = p90 = p99 = latencies[0]
        else:
            percentile_values = quantiles(latencies, n=100, method="inclusive")
            p50, p90, p99 = (
                percentile_values[49],
                percentile_values[89],
                percentile_values[98],
            )
        latency_percentiles = {
            "p50_sec": round(p50, 3),
            "p90_sec": round(p90, 3),
            "p99_sec": round(p99, 3),
        }

    return {
        "job_dir": str(job_dir),
        "trials_total": len(trial_dirs),
        "trials_completed": completed,
        "trials_failed": len(trial_dirs) - completed,
        "cost_usd_total": round(sum(costs), 6),
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
        },
        "latency_percentiles": latency_percentiles,
        "failure_taxonomy": dict(sorted(failures.items())),
        "provider_comparison": provider_comparison,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-dir", default="jobs", help="Jobs root directory")
    parser.add_argument(
        "--job-id",
        help="Optional specific job id under jobs directory (defaults to latest)",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON file path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    jobs_dir = (ROOT / args.jobs_dir).resolve()
    if not jobs_dir.is_dir():
        raise SystemExit(f"missing jobs dir: {jobs_dir}")

    job_dir = (
        (jobs_dir / args.job_id).resolve()
        if args.job_id
        else max((p for p in jobs_dir.iterdir() if p.is_dir()), key=lambda p: p.name)
    )
    summary = summarize_job(job_dir)
    output = json.dumps(summary, indent=2) + "\n"
    if args.output:
        output_path = (ROOT / args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
