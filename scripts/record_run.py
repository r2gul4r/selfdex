#!/usr/bin/env python3
"""Write compact Selfdex run records under runs/."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from slug_utils import normalize_slug
except ModuleNotFoundError:
    from scripts.slug_utils import normalize_slug


TIMESTAMP_PATTERN = re.compile(r"^\d{8}-\d{6}$")


@dataclass(frozen=True)
class RunRecord:
    timestamp: str
    project_key: str
    slug: str
    goal: str
    selected_candidate: str
    topology: str
    agent_budget: str
    write_sets: list[str]
    verification: list[str]
    repair_attempts: str
    result: str
    next_candidate: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a Selfdex run record.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--project-key", required=True, help="Project key for runs/<project-key>/ records.")
    parser.add_argument("--slug", required=True, help="Run slug for the filename.")
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Timestamp in YYYYMMDD-HHMMSS format. Defaults to current local time.",
    )
    parser.add_argument("--goal", required=True, help="Run goal.")
    parser.add_argument("--selected-candidate", required=True, help="Selected candidate.")
    parser.add_argument("--topology", required=True, help="Execution topology.")
    parser.add_argument("--agent-budget", required=True, help="Agent budget used.")
    parser.add_argument(
        "--write-set",
        action="append",
        default=[],
        help="Write set entry. May be provided more than once.",
    )
    parser.add_argument(
        "--verification",
        action="append",
        default=[],
        help="Verification entry. May be provided more than once.",
    )
    parser.add_argument("--repair-attempts", default="0", help="Repair attempts used.")
    parser.add_argument("--result", required=True, help="Run result.")
    parser.add_argument("--next-candidate", required=True, help="Next candidate.")
    return parser.parse_args(argv)


def current_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def sanitize_slug(value: str) -> str:
    return normalize_slug(value, fallback="run")


def sanitize_project_key(value: str) -> str:
    return normalize_slug(value, fallback="project")


def validate_timestamp(value: str) -> str:
    if not TIMESTAMP_PATTERN.match(value):
        raise ValueError("timestamp must use YYYYMMDD-HHMMSS")
    return value


def bullet_lines(items: list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def render_record(record: RunRecord) -> str:
    lines = [
        f"# Run {record.timestamp}-{record.slug}",
        "",
        f"- project_key: {record.project_key}",
        f"- goal: {record.goal}",
        f"- selected_candidate: {record.selected_candidate}",
        f"- topology: {record.topology}",
        f"- agent_budget: {record.agent_budget}",
        f"- repair_attempts: {record.repair_attempts}",
        f"- result: {record.result}",
        f"- next_candidate: {record.next_candidate}",
        "",
        "## Write Sets",
        "",
        *bullet_lines(record.write_sets),
        "",
        "## Verification",
        "",
        *bullet_lines(record.verification),
        "",
    ]
    return "\n".join(lines)


def write_run_record(root: Path, record: RunRecord) -> Path:
    timestamp = validate_timestamp(record.timestamp)
    project_key = sanitize_project_key(record.project_key)
    slug = sanitize_slug(record.slug)
    runs_dir = root / "runs" / project_key
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{timestamp}-{slug}.md"
    if path.exists():
        raise FileExistsError(f"run record already exists: {path}")

    normalized = RunRecord(
        timestamp=timestamp,
        project_key=project_key,
        slug=slug,
        goal=record.goal,
        selected_candidate=record.selected_candidate,
        topology=record.topology,
        agent_budget=record.agent_budget,
        write_sets=record.write_sets,
        verification=record.verification,
        repair_attempts=record.repair_attempts,
        result=record.result,
        next_candidate=record.next_candidate,
    )
    path.write_text(render_record(normalized), encoding="utf-8")
    return path


def record_from_args(args: argparse.Namespace) -> RunRecord:
    timestamp = args.timestamp or current_timestamp()
    return RunRecord(
        timestamp=timestamp,
        project_key=args.project_key,
        slug=args.slug,
        goal=args.goal,
        selected_candidate=args.selected_candidate,
        topology=args.topology,
        agent_budget=str(args.agent_budget),
        write_sets=list(args.write_set),
        verification=list(args.verification),
        repair_attempts=str(args.repair_attempts),
        result=args.result,
        next_candidate=args.next_candidate,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        path = write_run_record(root, record_from_args(args))
    except (FileExistsError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
