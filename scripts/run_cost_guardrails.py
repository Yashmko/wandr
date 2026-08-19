#!/usr/bin/env python3
"""Estimate run scope and enforce optional budget guardrails."""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPENSIVE_CONFIGS = frozenset({"configs/validation.yaml", "configs/wandr.yaml"})


@dataclass(frozen=True)
class ScopeEstimate:
    config_path: Path
    task_count: int
    agent_count: int
    n_attempts: int
    n_concurrent_trials: int

    @property
    def trial_units(self) -> int:
        return self.task_count * self.agent_count * self.n_attempts



def _load_yaml(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path}: expected mapping root")
    return document


def _dataset_task_count(path: Path, exclude_task_names: set[str]) -> int:
    dataset_toml = path / "dataset.toml"
    if not dataset_toml.is_file():
        raise ValueError(f"missing dataset manifest: {dataset_toml}")
    document = tomllib.loads(dataset_toml.read_text(encoding="utf-8"))
    tasks = document.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError(f"{dataset_toml}: expected [[tasks]] entries")
    names = {
        entry.get("name")
        for entry in tasks
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    return len(names - exclude_task_names)


def _task_count(config_path: Path, config: dict[str, Any]) -> int:
    explicit_tasks = config.get("tasks") or []
    if explicit_tasks:
        return len(explicit_tasks)

    datasets = config.get("datasets") or []
    if not datasets:
        raise ValueError(f"{config_path}: must declare tasks or datasets")

    total = 0
    for entry in datasets:
        if not isinstance(entry, dict):
            raise ValueError(f"{config_path}: dataset entry must be a mapping")
        raw_path = entry.get("path")
        if not isinstance(raw_path, str):
            raise ValueError(f"{config_path}: dataset entry missing path")
        dataset_path = (ROOT / raw_path).resolve()
        excludes = set(entry.get("exclude_task_names") or [])
        total += _dataset_task_count(dataset_path, excludes)
    return total


def estimate_scope(config_path: Path) -> ScopeEstimate:
    config = _load_yaml(config_path)
    agent_count = len(config.get("agents") or [])
    if agent_count < 1:
        raise ValueError(f"{config_path}: expected at least one agent")
    return ScopeEstimate(
        config_path=config_path,
        task_count=_task_count(config_path, config),
        agent_count=agent_count,
        n_attempts=int(config.get("n_attempts", 1)),
        n_concurrent_trials=int(config.get("n_concurrent_trials", 1)),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Config path relative to repo root")
    parser.add_argument(
        "--max-trial-units",
        type=int,
        help="Hard stop when estimated task x agent x attempt count exceeds this value",
    )
    parser.add_argument(
        "--max-concurrent-trials",
        type=int,
        help="Hard stop when n_concurrent_trials exceeds this value",
    )
    parser.add_argument(
        "--allow-expensive",
        action="store_true",
        help="Allow known expensive configs without acknowledgement env",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = (ROOT / args.config).resolve()
    estimate = estimate_scope(config_path)

    rel = config_path.relative_to(ROOT).as_posix()
    print(
        "estimated scope:",
        f"config={rel}",
        f"tasks={estimate.task_count}",
        f"agents={estimate.agent_count}",
        f"attempts={estimate.n_attempts}",
        f"concurrency={estimate.n_concurrent_trials}",
        f"trial_units={estimate.trial_units}",
    )

    if rel in EXPENSIVE_CONFIGS and not args.allow_expensive:
        if os.environ.get("WANDR_ACK_EXPENSIVE_CONFIG") not in {"1", "true", "yes"}:
            print(
                "error: expensive config requires WANDR_ACK_EXPENSIVE_CONFIG=1",
                file=sys.stderr,
            )
            return 2

    if (
        args.max_trial_units is not None
        and args.max_trial_units > 0
        and estimate.trial_units > args.max_trial_units
    ):
        print(
            f"error: estimated trial_units {estimate.trial_units} exceed limit {args.max_trial_units}",
            file=sys.stderr,
        )
        return 2

    if (
        args.max_concurrent_trials is not None
        and args.max_concurrent_trials > 0
        and estimate.n_concurrent_trials > args.max_concurrent_trials
    ):
        print(
            "error: n_concurrent_trials "
            f"{estimate.n_concurrent_trials} exceed limit {args.max_concurrent_trials}",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
