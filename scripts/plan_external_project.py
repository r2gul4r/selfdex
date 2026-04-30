#!/usr/bin/env python3
"""Plan a read-only Codex task for one selected external project."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import unicodedata

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from argparse_utils import add_format_argument, add_root_argument
    from build_external_candidate_snapshot import build_project_snapshot
    from cli_output_utils import write_json_or_markdown
    from list_project_registry import build_payload as build_registry_payload
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.build_external_candidate_snapshot import build_project_snapshot
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.list_project_registry import build_payload as build_registry_payload


SCHEMA_VERSION = 1
QUALITY_DIMENSIONS = (
    "real_problem",
    "user_value",
    "local_verifiability",
    "scope_smallness",
    "risk_reversibility",
)
APPROVAL_GATES = (
    "secrets or credential access",
    "paid API calls",
    "deploys or public runtime changes",
    "database or production writes",
    "destructive filesystem or Git operations",
    "writes outside the frozen target-project contract",
)

PROMPT_SUCCESS_CRITERIA = (
    "candidate is confirmed real from repository evidence",
    "task contract is frozen before any target-project write",
    "only approved files are modified after explicit approval",
    "verification commands are run or skipped with exact reasons",
    "final summary includes changed files, checks, repair attempts, and residual risk",
)

PROMPT_STOP_CONDITIONS = (
    "approval to edit the target project is missing",
    "the candidate is stale, already solved, or unsupported by local evidence",
    "the needed write set differs materially from the proposed boundary",
    "a hard approval gate is triggered",
    "verification cannot run and no equivalent local check exists",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a read-only task contract for one selected external project."
    )
    add_root_argument(parser, help_text="Selfdex repository root.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--project-id", help="Registered project id from PROJECT_REGISTRY.md.")
    target.add_argument("--project-root", help="Ad-hoc external project path to scan read-only.")
    parser.add_argument(
        "--project-name",
        help="Project label for --project-root output. Defaults to the directory name.",
    )
    parser.add_argument(
        "--candidate-index",
        type=int,
        default=1,
        help="1-based candidate index to freeze into the task contract. Defaults to 1.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Top candidate limit to scan before selecting. Defaults to 5.",
    )
    parser.add_argument(
        "--record-run",
        action="store_true",
        help="Write the rendered planning artifact under runs/ in the Selfdex repo.",
    )
    parser.add_argument(
        "--timestamp",
        help="Optional run artifact timestamp in YYYYMMDD-HHMMSS format.",
    )
    add_format_argument(parser, default="markdown", help_text="Output format. Defaults to markdown.")
    return parser.parse_args(argv)


def now_local_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    parts: list[str] = []
    previous_dash = False
    for char in normalized:
        if char.isalnum() or char == "_":
            parts.append(char.lower())
            previous_dash = False
            continue
        if not previous_dash:
            parts.append("-")
            previous_dash = True
    slug = "".join(parts).strip("-").strip(".")
    return slug or "external-project"


def project_key_from_project(project: dict[str, Any]) -> str:
    project_id = str(project.get("project_id") or "").strip()
    if project_id:
        return slugify(project_id)
    resolved = str(project.get("resolved_path") or "").strip()
    if resolved:
        return slugify(Path(resolved).name)
    return "external-project"


def validate_artifact_timestamp(value: str) -> str:
    if not re.match(r"^\d{8}-\d{6}$", value):
        raise ValueError("timestamp must use YYYYMMDD-HHMMSS")
    return value


def resolve_external_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def registry_project(registry: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    for project in registry.get("projects", []):
        if isinstance(project, dict) and project.get("project_id") == project_id:
            return project
    return None


def project_from_path(root: Path, project_root: str, project_name: str | None) -> dict[str, Any]:
    resolved = resolve_external_path(root, project_root)
    return {
        "project_id": project_name or resolved.name or "external_project",
        "path": project_root,
        "resolved_path": str(resolved),
        "path_exists": resolved.exists(),
        "role": "ad_hoc_external_target",
        "write_policy": "read-only",
        "verification": [],
    }


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def candidate_paths(candidate: dict[str, Any]) -> list[str]:
    source_signals = candidate.get("source_signals")
    if isinstance(source_signals, dict):
        paths = normalize_string_list(source_signals.get("paths"))
        if paths:
            return paths
        path = str(source_signals.get("path") or "").strip()
        if path:
            return [path]
    return []


def candidate_quality_estimate(candidate: dict[str, Any]) -> dict[str, Any]:
    paths = candidate_paths(candidate)
    checks = normalize_string_list(candidate.get("suggested_checks"))
    rationale = normalize_string_list(candidate.get("rationale"))
    risk = str(candidate.get("risk") or "").lower()
    work_type = str(candidate.get("work_type") or "").lower()

    scores = {
        "real_problem": 3 if rationale else 2 if candidate.get("source_signals") else 1,
        "user_value": 2 if work_type in {"repair", "hardening", "improvement", "capability", "direction"} else 1,
        "local_verifiability": 3 if checks else 1,
        "scope_smallness": 3 if 0 < len(paths) <= 1 else 2 if len(paths) <= 3 else 1,
        "risk_reversibility": 3 if risk == "low" else 2 if risk in {"", "medium"} else 1,
    }
    total = sum(scores[dimension] for dimension in QUALITY_DIMENSIONS)
    if total >= 12 and min(scores.values()) >= 2:
        verdict = "strong"
    elif total >= 9 and all(scores[item] >= 2 for item in ("real_problem", "local_verifiability", "risk_reversibility")):
        verdict = "usable"
    else:
        verdict = "needs_human_review"
    return {
        "status": "heuristic_estimate",
        "scores": scores,
        "total": total,
        "verdict": verdict,
        "requires_human_scoring": True,
    }


def select_candidate(project_snapshot: dict[str, Any], candidate_index: int) -> dict[str, Any] | None:
    candidates = project_snapshot.get("top_candidates", [])
    if not isinstance(candidates, list):
        return None
    index = max(candidate_index, 1) - 1
    if index >= len(candidates):
        return None
    candidate = candidates[index]
    return candidate if isinstance(candidate, dict) else None


def verification_commands(_project: dict[str, Any], candidate: dict[str, Any] | None) -> list[str]:
    candidate_checks = normalize_string_list(candidate.get("suggested_checks") if candidate else [])
    commands = dedupe(candidate_checks)
    return commands or ["manual review required before write-enabled execution"]


def build_codex_prompt(
    project: dict[str, Any],
    candidate: dict[str, Any],
    inspect_files: list[str],
    modify_files: list[str],
    checks: list[str],
    project_direction: dict[str, Any] | None = None,
) -> str:
    inspect_block = "\n".join(f"- {path}" for path in inspect_files) or "- Discover the smallest relevant files first."
    modify_block = "\n".join(f"- {path}" for path in modify_files) or "- No target files are approved yet; freeze them before editing."
    checks_block = "\n".join(f"- {command}" for command in checks)
    gates_block = "\n".join(f"- {gate}" for gate in APPROVAL_GATES)
    success_block = "\n".join(f"- {criterion}" for criterion in PROMPT_SUCCESS_CRITERIA)
    stops_block = "\n".join(f"- {condition}" for condition in PROMPT_STOP_CONDITIONS)
    direction = project_direction or {}
    direction_block = "\n".join(
        f"- {item}"
        for item in (
            f"purpose: {direction.get('purpose')}" if direction.get("purpose") else "",
            f"opportunity_source: {candidate.get('source')}",
            f"suggested_first_step: {candidate.get('source_signals', {}).get('suggested_first_step')}"
            if isinstance(candidate.get("source_signals"), dict)
            else "",
        )
        if item
    ) or "- No direction snapshot was available; infer purpose read-only before changing files."
    return (
        f"You are working in the user-selected target project:\n"
        f"{project.get('resolved_path')}\n\n"
        "Project direction context:\n"
        f"{direction_block}\n\n"
        "Expected outcome:\n"
        f"Move the project in a better direction with the smallest safe first step for this candidate: {candidate.get('title')}\n\n"
        "Success criteria:\n"
        f"{success_block}\n\n"
        "Context budget:\n"
        "- Read repository instructions and matching skill descriptions before broad search.\n"
        "- Inspect the likely files first, then search only when the first pass leaves uncertainty.\n"
        "- Keep stable policy in mind and put dynamic findings into the frozen contract.\n\n"
        "Tool and skill routing:\n"
        "- Use repo, user, or system skills only when the task explicitly names them or their description directly matches this work.\n"
        "- Load only the matching SKILL.md body; do not install skills, plugins, MCP servers, or edit global Codex config without explicit approval.\n"
        "- Give a short preamble before major tool phases that states what you are checking or changing.\n\n"
        "Start read-only:\n"
        "- Inspect the files below and confirm the task is still real.\n"
        "- Freeze a short task contract before the first target-project write.\n"
        "- Human approval is required before modifying the target project.\n"
        "- If approval is not already explicit in the current thread, stop after the read-only contract and ask for approval.\n\n"
        "Likely files to inspect:\n"
        f"{inspect_block}\n\n"
        "Proposed target write boundary after approval:\n"
        f"{modify_block}\n\n"
        "Verification to run from the target project when execution is approved:\n"
        f"{checks_block}\n\n"
        "Stop conditions:\n"
        f"{stops_block}\n\n"
        "Hard approval gates:\n"
        f"{gates_block}\n\n"
        "Return a PR-ready summary with changed files, verification results, repair attempts, "
        "remaining risk, and evidence suitable for a Selfdex runs/ record."
    )


def build_task_contract(
    project: dict[str, Any],
    candidate: dict[str, Any],
    project_direction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inspect_files = candidate_paths(candidate)
    modify_files = list(inspect_files)
    checks = verification_commands(project, candidate)
    return {
        "selected_candidate": candidate,
        "project_direction": project_direction or {},
        "why_it_matters": normalize_string_list(candidate.get("rationale")),
        "candidate_quality": candidate_quality_estimate(candidate),
        "write_boundaries": {
            "target_project_writes_allowed_now": False,
            "future_write_mode": "requires explicit user approval and an isolated branch or worktree",
            "proposed_target_write_set": modify_files,
            "selfdex_artifact_writes_allowed": ["runs/"],
        },
        "files_likely_to_inspect": inspect_files,
        "files_likely_safe_to_modify_after_approval": modify_files,
        "verification_commands": checks,
        "registry_verification_notes": normalize_string_list(project.get("verification")),
        "risk_level": candidate.get("risk", "unknown"),
        "human_approval_required": True,
        "codex_execution_prompt": build_codex_prompt(
            project,
            candidate,
            inspect_files,
            modify_files,
            checks,
            project_direction,
        ),
    }


def blocked_plan(root: Path, project: dict[str, Any], status: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_external_project_plan",
        "generated_at": utc_timestamp(),
        "status": status,
        "validation_mode": "read_only",
        "external_project_writes_performed": False,
        "root": str(root.resolve()),
        "project": project,
        "blocker": reason,
        "task_contract": None,
        "recorded_run_path": None,
    }


def build_plan(
    root: Path,
    *,
    project_id: str | None = None,
    project_root: str | None = None,
    project_name: str | None = None,
    candidate_index: int = 1,
    limit: int = 5,
) -> dict[str, Any]:
    root = root.resolve()
    if bool(project_id) == bool(project_root):
        raise ValueError("provide exactly one of project_id or project_root")

    if project_id:
        registry = build_registry_payload(root)
        project = registry_project(registry, project_id)
        if project is None:
            return blocked_plan(
                root,
                {"project_id": project_id, "write_policy": "unknown", "path_exists": False},
                "fail",
                "project_id is not registered in PROJECT_REGISTRY.md",
            )
    else:
        project = project_from_path(root, str(project_root), project_name)

    project_snapshot = build_project_snapshot(project, limit=limit)
    if project_snapshot.get("status") == "skipped":
        return blocked_plan(root, project, "blocked", str(project_snapshot.get("skip_reason") or "project skipped"))
    if project_snapshot.get("status") == "error":
        return blocked_plan(root, project, "blocked", "all scanners failed")

    candidate = select_candidate(project_snapshot, candidate_index)
    if candidate is None:
        return blocked_plan(root, project, "no_candidate", "no candidate available for the requested index")

    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_external_project_plan",
        "generated_at": utc_timestamp(),
        "status": "ready",
        "validation_mode": "read_only",
        "external_project_writes_performed": False,
        "root": str(root),
        "project": project,
        "candidate_index": max(candidate_index, 1),
        "candidate_count": project_snapshot.get("candidate_count", 0),
        "scanner_status": project_snapshot.get("status", ""),
        "scanner_errors": project_snapshot.get("scanner_errors", []),
        "task_contract": build_task_contract(project, candidate, project_snapshot.get("project_direction")),
        "recorded_run_path": None,
    }


def plan_artifact_path(root: Path, payload: dict[str, Any], timestamp: str | None = None) -> Path:
    project = payload.get("project", {})
    project_key = project_key_from_project(project)
    stamp = validate_artifact_timestamp(timestamp or now_local_timestamp())
    return root / "runs" / project_key / f"{stamp}-external-project-plan-{project_key}.md"


def write_plan_artifact(root: Path, payload: dict[str, Any], timestamp: str | None = None) -> Path:
    path = plan_artifact_path(root, payload, timestamp)
    if path.exists():
        raise FileExistsError(f"run artifact already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["recorded_run_path"] = str(path)
    path.write_text(render_markdown(payload), encoding="utf-8")
    return path


def render_markdown(payload: dict[str, Any]) -> str:
    project = payload.get("project", {})
    contract = payload.get("task_contract")
    lines = [
        "# External Project Plan",
        "",
        f"- status: `{payload.get('status')}`",
        f"- validation_mode: `{payload.get('validation_mode')}`",
        f"- external_project_writes_performed: `{payload.get('external_project_writes_performed')}`",
        f"- project_id: `{project.get('project_id')}`",
        f"- resolved_path: `{project.get('resolved_path', '')}`",
        f"- write_policy: `{project.get('write_policy')}`",
        f"- human_approval_required: `{bool(contract and contract.get('human_approval_required'))}`",
        f"- recorded_run_path: `{payload.get('recorded_run_path') or 'not_recorded'}`",
        "",
    ]
    if not contract:
        lines.extend(["## Blocker", "", f"- {payload.get('blocker', 'unknown')}"])
        return "\n".join(lines) + "\n"

    candidate = contract["selected_candidate"]
    quality = contract["candidate_quality"]
    project_direction = contract.get("project_direction") or {}
    lines.extend(
        [
            "## Selected Candidate",
            "",
            f"- title: {candidate.get('title')}",
            f"- source: `{candidate.get('source')}`",
            f"- work_type: `{candidate.get('work_type')}`",
            f"- priority_score: `{candidate.get('priority_score')}`",
            f"- risk_level: `{contract.get('risk_level')}`",
            "",
            "## Why It Matters",
            "",
        ]
    )
    if project_direction:
        lines.extend(
            [
                "",
                "## Project Direction Context",
                "",
                f"- purpose: {project_direction.get('purpose', 'unknown')}",
                f"- opportunity_count: `{project_direction.get('opportunity_count', 'unknown')}`",
            ]
        )
    rationale = contract.get("why_it_matters", [])
    lines.extend([f"- {item}" for item in rationale] or ["- no rationale available"])
    lines.extend(
        [
            "",
            "## Candidate Quality Estimate",
            "",
            f"- status: `{quality['status']}`",
            f"- verdict: `{quality['verdict']}`",
            f"- total: `{quality['total']}`",
            f"- requires_human_scoring: `{quality['requires_human_scoring']}`",
        ]
    )
    for dimension in QUALITY_DIMENSIONS:
        lines.append(f"- {dimension}: `{quality['scores'][dimension]}`")

    boundaries = contract["write_boundaries"]
    lines.extend(
        [
            "",
            "## Write Boundaries",
            "",
            f"- target_project_writes_allowed_now: `{boundaries['target_project_writes_allowed_now']}`",
            f"- future_write_mode: {boundaries['future_write_mode']}",
            "- proposed_target_write_set:",
        ]
    )
    lines.extend([f"  - `{path}`" for path in boundaries["proposed_target_write_set"]] or ["  - none"])
    lines.extend(["", "## Files To Inspect", ""])
    lines.extend([f"- `{path}`" for path in contract["files_likely_to_inspect"]] or ["- discover during read-only inspection"])
    lines.extend(["", "## Verification Commands", ""])
    lines.extend([f"- `{command}`" for command in contract["verification_commands"]])
    registry_notes = contract.get("registry_verification_notes", [])
    if registry_notes:
        lines.extend(["", "## Registry Verification Notes", ""])
        lines.extend([f"- {note}" for note in registry_notes])
    lines.extend(
        [
            "",
            "## Codex Execution Prompt",
            "",
            "```text",
            contract["codex_execution_prompt"],
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        payload = build_plan(
            root,
            project_id=args.project_id,
            project_root=args.project_root,
            project_name=args.project_name,
            candidate_index=args.candidate_index,
            limit=args.limit,
        )
        if args.record_run:
            write_plan_artifact(root, payload, args.timestamp)
    except (FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    write_json_or_markdown(payload, args.format, render_markdown)
    if payload["status"] == "ready":
        return 0
    if payload["status"] in {"fail", "blocked"}:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
