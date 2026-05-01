#!/usr/bin/env python3
"""Build a read-only Selfdex control-surface snapshot."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from cli_output_utils import write_json_or_markdown
    import list_project_registry
    import plan_next_task
except ModuleNotFoundError:
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts import list_project_registry
    from scripts import plan_next_task


RUN_FIELD_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_-]+):\s*`?(.+?)`?\s*$")
RUN_ARTIFACT_PATTERN = re.compile(r"^(?P<timestamp>\d{8}-\d{6})-.+\.md$")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a read-only Selfdex control surface snapshot.")
    parser.add_argument("--root", default=".", help="Selfdex repository root.")
    parser.add_argument("--run-limit", type=int, default=5, help="Recent run summary limit.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args(argv)


def compact_project(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": project.get("project_id"),
        "path": project.get("path"),
        "resolved_path": project.get("resolved_path"),
        "path_exists": project.get("path_exists"),
        "role": project.get("role"),
        "write_policy": project.get("write_policy"),
        "verification": project.get("verification") or [],
    }


def compact_candidate(candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if not candidate:
        return None
    return {
        "source": candidate.get("source"),
        "work_type": candidate.get("work_type"),
        "title": candidate.get("title"),
        "decision": candidate.get("decision"),
        "priority_score": candidate.get("priority_score"),
        "risk": candidate.get("risk"),
        "rationale": list(candidate.get("rationale") or [])[:3],
        "suggested_checks": list(candidate.get("suggested_checks") or [])[:3],
    }


def run_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def parse_run_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = RUN_FIELD_PATTERN.match(line)
        if match:
            fields[match.group(1)] = match.group(2).strip("` ")
    return fields


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def build_approval_status(root: Path) -> dict[str, Any]:
    campaign = read_json_object(root / "CAMPAIGN_STATE.json")
    state = read_json_object(root / "STATE.json")
    campaign_values = campaign.get("campaign") if isinstance(campaign.get("campaign"), dict) else {}
    model_policy = (
        campaign.get("model_usage_policy")
        if isinstance(campaign.get("model_usage_policy"), dict)
        else {}
    )
    current_task = state.get("current_task") if isinstance(state.get("current_task"), dict) else {}
    latest_run = campaign.get("latest_run") if isinstance(campaign.get("latest_run"), dict) else {}
    first_surface = (
        campaign.get("first_app_surface")
        if isinstance(campaign.get("first_app_surface"), dict)
        else {}
    )

    return {
        "target_project_writes_allowed": False,
        "target_project_write_approval_required": True,
        "target_execution_approval_required": True,
        "write_capable_apps_mcp_tools_exposed": bool(
            first_surface.get("write_capable_target_execution_exposed", False)
        ),
        "gpt_direction_review_auto_call": bool(
            model_policy.get("gpt_direction_review_auto_call", False)
        ),
        "gpt_direction_review_approval": model_policy.get(
            "gpt_direction_review_approval",
            "user-approved-or-user-called-only",
        ),
        "direction_review_default": campaign_values.get(
            "direction_review_default",
            "recommend_and_wait_for_user_approval",
        ),
        "current_task": current_task.get("task", ""),
        "current_phase": current_task.get("phase", ""),
        "latest_run_status": latest_run.get("status", ""),
        "latest_run_artifact": latest_run.get("artifact_path", ""),
    }


def summarize_run(root: Path, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    fields = parse_run_fields(text)
    return {
        "path": path.relative_to(root).as_posix(),
        "title": run_title(text, path),
        "status": fields.get("status", "unknown"),
        "project_key": fields.get("project_key", path.parent.name),
        "summary": fields.get("summary", ""),
    }


def latest_runs(root: Path, limit: int) -> list[dict[str, Any]]:
    runs_dir = root / "runs"
    if not runs_dir.exists():
        return []
    run_paths = [
        path
        for path in runs_dir.glob("**/*.md")
        if path.is_file() and RUN_ARTIFACT_PATTERN.match(path.name)
    ]
    run_paths = sorted(
        run_paths,
        key=lambda path: (
            RUN_ARTIFACT_PATTERN.match(path.name).group("timestamp"),  # type: ignore[union-attr]
            path.relative_to(root).as_posix(),
        ),
        reverse=True,
    )
    return [summarize_run(root, path) for path in run_paths[: max(limit, 0)]]


def build_payload(root: Path, *, run_limit: int = 5) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []

    try:
        registry_payload = list_project_registry.build_payload(root)
        projects = [compact_project(project) for project in registry_payload.get("projects", [])]
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        projects = []
        errors.append(f"project registry unavailable: {exc}")

    try:
        planner_payload = plan_next_task.choose_candidate(root)
        next_task = compact_candidate(planner_payload.get("selected"))
        planner_errors = list(planner_payload.get("errors") or [])
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        next_task = None
        planner_errors = [f"next task unavailable: {exc}"]

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_control_surface_snapshot",
        "surface_kind": "read_only",
        "mutating_tools_exposed": False,
        "execution_policy": "No target-project execution, branch creation, or writes are exposed by this snapshot.",
        "root": str(root),
        "project_count": len(projects),
        "projects": projects,
        "next_task": next_task,
        "recent_runs": latest_runs(root, run_limit),
        "approval_status": build_approval_status(root),
        "errors": errors + planner_errors,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Selfdex Control Surface Snapshot",
        "",
        f"- surface_kind: `{payload['surface_kind']}`",
        f"- mutating_tools_exposed: `{payload['mutating_tools_exposed']}`",
        f"- project_count: `{payload['project_count']}`",
        f"- recent_run_count: `{len(payload['recent_runs'])}`",
        f"- execution_policy: {payload['execution_policy']}",
        "",
        "## Approval Status",
        "",
    ]
    approval_status = payload.get("approval_status") or {}
    for key in (
        "target_project_writes_allowed",
        "target_project_write_approval_required",
        "target_execution_approval_required",
        "write_capable_apps_mcp_tools_exposed",
        "gpt_direction_review_auto_call",
        "gpt_direction_review_approval",
        "current_task",
        "current_phase",
        "latest_run_status",
    ):
        lines.append(f"- {key}: `{approval_status.get(key, '')}`")

    lines.extend(
        [
            "",
            "## Projects",
            "",
        ]
    )
    for project in payload["projects"]:
        lines.append(
            f"- `{project['project_id']}` {project['role']} "
            f"write_policy=`{project['write_policy']}` path_exists=`{project['path_exists']}`"
        )
    if not payload["projects"]:
        lines.append("- none")

    lines.extend(["", "## Next Task", ""])
    task = payload.get("next_task")
    if task:
        lines.extend(
            [
                f"- title: `{task['title']}`",
                f"- source: `{task['source']}`",
                f"- work_type: `{task['work_type']}`",
                f"- decision: `{task['decision']}`",
                f"- risk: `{task['risk']}`",
            ]
        )
    else:
        lines.append("- none")

    lines.extend(["", "## Recent Runs", ""])
    for run in payload["recent_runs"]:
        lines.append(f"- `{run['path']}` status=`{run['status']}` title=`{run['title']}`")
    if not payload["recent_runs"]:
        lines.append("- none")

    if payload.get("errors"):
        lines.extend(["", "## Read-Only Collection Errors", ""])
        for error in payload["errors"]:
            lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    payload = build_payload(root, run_limit=args.run_limit)
    write_json_or_markdown(payload, args.format, render_markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
