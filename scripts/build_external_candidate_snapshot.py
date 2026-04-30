#!/usr/bin/env python3
"""Build read-only candidate snapshots for registered external projects."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from argparse_utils import add_format_argument, add_root_argument
    from cli_output_utils import write_json_or_markdown
    from build_project_direction import build_payload as build_direction_payload
    from extract_feature_gap_candidates import extract_feature_gap_candidates
    from extract_refactor_candidates import build_payload as build_refactor_payload
    from extract_refactor_candidates import build_refactor_candidates
    from extract_test_gap_candidates import build_payload as build_test_gap_payload
    from list_project_registry import build_payload as build_registry_payload
    from plan_next_task import (
        Candidate,
        candidate_to_dict,
        collect_feature_candidates,
        collect_refactor_candidates,
        collect_test_gap_candidates,
    )
    from refactor_metrics_payload import filter_metrics_payload, load_metrics
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.build_project_direction import build_payload as build_direction_payload
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.extract_feature_gap_candidates import extract_feature_gap_candidates
    from scripts.extract_refactor_candidates import build_payload as build_refactor_payload
    from scripts.extract_refactor_candidates import build_refactor_candidates
    from scripts.extract_test_gap_candidates import build_payload as build_test_gap_payload
    from scripts.list_project_registry import build_payload as build_registry_payload
    from scripts.plan_next_task import (
        Candidate,
        candidate_to_dict,
        collect_feature_candidates,
        collect_refactor_candidates,
        collect_test_gap_candidates,
    )
    from scripts.refactor_metrics_payload import filter_metrics_payload, load_metrics


SCHEMA_VERSION = 1
SELFDEX_PROJECT_IDS = {"selfdex"}
ScanStep = Callable[[Path, int], tuple[list[Candidate], dict[str, Any]]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only top-candidate snapshots for registered external projects."
    )
    add_root_argument(parser, help_text="Selfdex repository root.")
    parser.add_argument(
        "--project-id",
        action="append",
        dest="project_ids",
        help="Optional project id to snapshot. Repeat to select multiple projects.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Top candidate limit per project. Defaults to 5.",
    )
    add_format_argument(parser)
    return parser.parse_args(argv)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_read_only_external(project: dict[str, Any]) -> bool:
    project_id = str(project.get("project_id") or "").strip()
    write_policy = str(project.get("write_policy") or "").lower()
    return bool(project_id and project_id not in SELFDEX_PROJECT_IDS and "read-only" in write_policy)


def unique_project_ids(project_ids: list[str] | None) -> list[str]:
    if not project_ids:
        return []
    return list(dict.fromkeys(project_id.strip() for project_id in project_ids if project_id.strip()))


def registry_project_ids(registry: dict[str, Any]) -> set[str]:
    return {
        str(project.get("project_id") or "").strip()
        for project in registry.get("projects", [])
        if isinstance(project, dict) and str(project.get("project_id") or "").strip()
    }


def missing_requested_project_ids(registry: dict[str, Any], project_ids: list[str] | None) -> list[str]:
    available = registry_project_ids(registry)
    return [project_id for project_id in unique_project_ids(project_ids) if project_id not in available]


def selected_registry_projects(registry: dict[str, Any], project_ids: list[str] | None) -> list[dict[str, Any]]:
    projects = [project for project in registry.get("projects", []) if isinstance(project, dict)]
    if project_ids:
        wanted = set(unique_project_ids(project_ids))
        return [project for project in projects if str(project.get("project_id")) in wanted]
    return [project for project in projects if is_read_only_external(project)]


def build_selection_summary(
    registry: dict[str, Any],
    requested_project_ids: list[str],
    selected_projects: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "mode": "explicit" if requested_project_ids else "all_read_only_external",
        "requested_project_ids": requested_project_ids,
        "selected_project_ids": [
            str(project.get("project_id") or "").strip()
            for project in selected_projects
            if str(project.get("project_id") or "").strip()
        ],
        "missing_project_ids": missing_requested_project_ids(registry, requested_project_ids),
    }


def scan_test_gaps(project_root: Path, limit: int) -> tuple[list[Candidate], dict[str, Any]]:
    payload = build_test_gap_payload(project_root)
    candidates = collect_test_gap_candidates(payload)
    return candidates, {
        "scanner": "test_gap",
        "finding_count": payload.get("finding_count", 0),
        "candidate_count": len(candidates),
    }


def scan_project_direction(project_root: Path, limit: int) -> tuple[list[Candidate], dict[str, Any]]:
    payload = build_direction_payload(project_root, limit=max(limit, 1))
    candidates = [
        Candidate(
            source="project_direction",
            work_type=str(item.get("work_type") or "capability"),
            title=str(item.get("title") or "Project direction opportunity"),
            decision=str(item.get("decision") or "monitor"),
            priority_score=float(item.get("priority_score") or 0),
            risk=str(item.get("risk") or "guarded"),
            rationale=[str(value) for value in item.get("rationale", []) if str(value).strip()][:3],
            suggested_checks=[str(value) for value in item.get("suggested_checks", []) if str(value).strip()],
            source_signals={
                "opportunity_id": item.get("opportunity_id"),
                "paths": item.get("evidence_paths", []),
                "strategic_dimensions": item.get("strategic_dimensions", {}),
                "suggested_first_step": item.get("suggested_first_step", ""),
                "project_purpose": payload.get("purpose", {}).get("summary", ""),
            },
        )
        for item in payload.get("opportunities", [])
        if isinstance(item, dict)
    ]
    return candidates, {
        "scanner": "project_direction",
        "opportunity_count": payload.get("opportunity_count", 0),
        "candidate_count": len(candidates),
        "purpose": payload.get("purpose", {}).get("summary", ""),
    }


def scan_refactor_gaps(project_root: Path, limit: int) -> tuple[list[Candidate], dict[str, Any]]:
    metrics_payload = filter_metrics_payload(load_metrics(project_root, None))
    refactor_candidates = build_refactor_candidates(project_root, metrics_payload, max(limit, 1))
    payload = build_refactor_payload(project_root, metrics_payload, refactor_candidates)
    candidates = collect_refactor_candidates(payload)
    return candidates, {
        "scanner": "refactor",
        "scanned_file_count": payload.get("scanned_file_count", 0),
        "candidate_count": len(candidates),
    }


def scan_feature_gaps(project_root: Path, limit: int) -> tuple[list[Candidate], dict[str, Any]]:
    payload = extract_feature_gap_candidates(project_root)
    candidates = collect_feature_candidates(payload)
    return candidates, {
        "scanner": "feature_gap",
        "scanned_file_count": payload.get("scanned_file_count", 0),
        "candidate_count": len(candidates),
    }


DEFAULT_SCAN_STEPS: tuple[tuple[str, ScanStep], ...] = (
    ("project_direction", scan_project_direction),
    ("test_gap", scan_test_gaps),
    ("refactor", scan_refactor_gaps),
    ("feature_gap", scan_feature_gaps),
)


def rank_candidates(candidates: list[Candidate], limit: int) -> list[Candidate]:
    return sorted(
        candidates,
        key=lambda item: (
            -item.priority_score,
            item.source,
            item.title,
        ),
    )[: max(limit, 1)]


def skipped_project_snapshot(project: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "project_id": project.get("project_id", ""),
        "path": project.get("path", ""),
        "resolved_path": project.get("resolved_path", ""),
        "write_policy": project.get("write_policy", ""),
        "status": "skipped",
        "skip_reason": reason,
        "scanner_errors": [],
        "scanner_summaries": [],
        "candidate_count": 0,
        "top_candidates": [],
        "human_review_status": "not_started",
    }


def build_project_snapshot(
    project: dict[str, Any],
    *,
    limit: int,
    scan_steps: tuple[tuple[str, ScanStep], ...] = DEFAULT_SCAN_STEPS,
) -> dict[str, Any]:
    if not is_read_only_external(project):
        return skipped_project_snapshot(project, "not_external_read_only")
    if not project.get("path_exists"):
        return skipped_project_snapshot(project, "path_missing")

    project_root = Path(str(project["resolved_path"]))
    all_candidates: list[Candidate] = []
    scanner_summaries: list[dict[str, Any]] = []
    scanner_errors: list[dict[str, str]] = []
    for scanner_name, scan_step in scan_steps:
        try:
            candidates, summary = scan_step(project_root, limit)
        except Exception as exc:  # noqa: BLE001 - snapshot must preserve per-scanner failures.
            scanner_errors.append(
                {
                    "scanner": scanner_name,
                    "error": str(exc),
                }
            )
            continue
        all_candidates.extend(candidates)
        scanner_summaries.append(summary)

    top_candidates = [candidate_to_dict(candidate, "") for candidate in rank_candidates(all_candidates, limit)]
    project_direction = next(
        (summary for summary in scanner_summaries if summary.get("scanner") == "project_direction"),
        {},
    )
    if scanner_errors and top_candidates:
        status = "partial"
    elif scanner_errors:
        status = "error"
    else:
        status = "scanned"

    return {
        "project_id": project.get("project_id", ""),
        "path": project.get("path", ""),
        "resolved_path": project.get("resolved_path", ""),
        "write_policy": project.get("write_policy", ""),
        "status": status,
        "scanner_errors": scanner_errors,
        "scanner_summaries": scanner_summaries,
        "project_direction": project_direction,
        "candidate_count": len(top_candidates),
        "top_candidates": top_candidates,
        "human_review_status": "pending" if top_candidates else "not_started",
    }


def build_snapshot(root: Path, *, project_ids: list[str] | None = None, limit: int = 5) -> dict[str, Any]:
    registry = build_registry_payload(root)
    requested_project_ids = unique_project_ids(project_ids)
    projects = selected_registry_projects(registry, requested_project_ids)
    project_snapshots = [
        build_project_snapshot(project, limit=limit)
        for project in projects
    ]
    scanner_error_count = sum(len(project["scanner_errors"]) for project in project_snapshots)
    selection = build_selection_summary(registry, requested_project_ids, projects)
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_external_candidate_snapshot",
        "generated_at": utc_timestamp(),
        "validation_mode": "read_only",
        "external_value_proven": False,
        "root": str(root.resolve()),
        "requested_project_ids": requested_project_ids,
        "selection": selection,
        "project_count": len(project_snapshots),
        "candidate_count": sum(project["candidate_count"] for project in project_snapshots),
        "scanner_error_count": scanner_error_count,
        "human_review_status": "pending",
        "projects": project_snapshots,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# External Candidate Snapshot",
        "",
        f"- validation_mode: `{payload['validation_mode']}`",
        f"- external_value_proven: `{payload['external_value_proven']}`",
        f"- project_count: `{payload['project_count']}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- scanner_error_count: `{payload['scanner_error_count']}`",
        f"- human_review_status: `{payload['human_review_status']}`",
        "",
        "## Projects",
        "",
    ]
    selection = payload.get("selection", {})
    if isinstance(selection, dict):
        lines[8:8] = [
            "",
            "## Selection",
            "",
            f"- mode: `{selection.get('mode', '')}`",
            f"- requested_project_ids: `{', '.join(selection.get('requested_project_ids', [])) or 'none'}`",
            f"- selected_project_ids: `{', '.join(selection.get('selected_project_ids', [])) or 'none'}`",
            f"- missing_project_ids: `{', '.join(selection.get('missing_project_ids', [])) or 'none'}`",
        ]

    if not payload["projects"]:
        lines.append("- none")
        return "\n".join(lines) + "\n"

    for project in payload["projects"]:
        lines.extend(
            [
                f"### {project['project_id']}",
                "",
                f"- status: `{project['status']}`",
                f"- write_policy: `{project['write_policy']}`",
                f"- candidate_count: `{project['candidate_count']}`",
                f"- human_review_status: `{project['human_review_status']}`",
            ]
        )
        project_direction = project.get("project_direction")
        if isinstance(project_direction, dict) and project_direction.get("purpose"):
            lines.append(f"- project_direction: {project_direction['purpose']}")
        if project.get("skip_reason"):
            lines.append(f"- skip_reason: `{project['skip_reason']}`")
        if project["scanner_errors"]:
            lines.append("- scanner_errors:")
            for error in project["scanner_errors"]:
                lines.append(f"  - `{error['scanner']}`: {error['error']}")
        lines.append("- top_candidates:")
        if not project["top_candidates"]:
            lines.append("  - none")
        for candidate in project["top_candidates"]:
            lines.append(
                f"  - `{candidate['source']}` score=`{candidate['priority_score']}` "
                f"decision=`{candidate['decision']}` title={candidate['title']}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    snapshot = build_snapshot(root, project_ids=args.project_ids, limit=args.limit)
    write_json_or_markdown(snapshot, args.format, render_markdown)
    return 2 if snapshot["selection"]["missing_project_ids"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
