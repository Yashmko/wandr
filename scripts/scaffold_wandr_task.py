#!/usr/bin/env python3
"""Scaffold a new WANDR task source directory with quality metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_ROOT = ROOT / "reference" / "wandr_tasks"
TASK_NAME_RE = re.compile(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*")
VALID_DIFFICULTY = {"easy", "medium", "hard", "expert"}
VALID_RUNTIME_CLASS = {"short", "standard", "long"}
VALID_COST_CLASS = {"low", "medium", "high"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_name", help="New root task name, e.g. customer_support_quality")
    parser.add_argument(
        "--title",
        help="Optional display title used in generated prompt scaffolding",
    )
    parser.add_argument(
        "--difficulty",
        default="medium",
        choices=sorted(VALID_DIFFICULTY),
        help="Task difficulty tag",
    )
    parser.add_argument(
        "--runtime-class",
        default="standard",
        choices=sorted(VALID_RUNTIME_CLASS),
        help="Expected verifier runtime class",
    )
    parser.add_argument(
        "--cost-class",
        default="medium",
        choices=sorted(VALID_COST_CLASS),
        help="Expected evaluation cost class",
    )
    parser.add_argument(
        "--domain-tag",
        action="append",
        dest="domain_tags",
        default=[],
        help="Domain tag (repeatable)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing task directory",
    )
    return parser.parse_args()


def _task_title(task_name: str, override: str | None) -> str:
    if override and override.strip():
        return override.strip()
    return task_name.replace("_", " ").replace(".", " / ").title()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _config_stub(task_name: str) -> str:
    return f'''"""{task_name} task source config."""

from pathlib import Path

from src.config import KeySpec, TaskConfig

HERE = Path(__file__).parent

CONFIG = TaskConfig(
    name="{task_name}",
    task_template=(HERE / "prompts" / "task_template.md.jinja").read_text().strip(),
    key_hierarchy=[
        KeySpec("topic", required=3),
        KeySpec("url", required=2),
    ],
)
'''


def _prompt_stub(task_name: str, title: str) -> str:
    return f'''# {title}

Research and extract evidence-backed results for task `{task_name}`.

## Required JSONL schema

Each row must include:
- `item`: key fields that identify the evaluated entity
- `answer`: extracted answer fields
- `excerpts`: supporting source excerpts with URLs

Use high-quality sources and preserve citation provenance.
'''


def _metadata_stub(
    *,
    task_name: str,
    difficulty: str,
    runtime_class: str,
    cost_class: str,
    domain_tags: list[str],
) -> str:
    normalized_tags = sorted({tag.strip().lower() for tag in domain_tags if tag.strip()})
    tags_toml = "\n".join(f'  "{tag}",' for tag in normalized_tags) or '  "general",'
    return f'''# Task quality metadata used by adapter validation gates.
name = "{task_name}"
difficulty = "{difficulty}"
expected_runtime_class = "{runtime_class}"
expected_cost_class = "{cost_class}"

[quality]
domain_tags = [
{tags_toml}
]
'''


def scaffold(args: argparse.Namespace) -> Path:
    task_name = args.task_name.strip()
    if not TASK_NAME_RE.fullmatch(task_name):
        raise ValueError(
            "task_name must be a dotted filename-safe task name "
            "(letters, numbers, underscore, dash, optional dot segments)"
        )

    task_dir = TASKS_ROOT / task_name
    if task_dir.exists() and not args.overwrite:
        raise FileExistsError(f"{task_dir} already exists; pass --overwrite to replace it")

    if task_dir.exists() and args.overwrite:
        for child in sorted(task_dir.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        task_dir.rmdir()

    title = _task_title(task_name, args.title)
    _write_text(task_dir / "config.py", _config_stub(task_name))
    _write_text(task_dir / "prompts" / "task_template.md.jinja", _prompt_stub(task_name, title))
    _write_text(
        task_dir / "task_meta.toml",
        _metadata_stub(
            task_name=task_name,
            difficulty=args.difficulty,
            runtime_class=args.runtime_class,
            cost_class=args.cost_class,
            domain_tags=args.domain_tags,
        ),
    )
    return task_dir


def main() -> int:
    args = parse_args()
    task_dir = scaffold(args)
    print(f"Scaffolded {task_dir.relative_to(ROOT)}")
    print("Next steps:")
    print("1) Fill prompt + config semantics in reference/wandr_tasks/<task>/")
    print("2) Regenerate Harbor task with adapters/wandr CLI")
    print("3) Run ./scripts/wandr check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
