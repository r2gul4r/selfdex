#!/usr/bin/env python3
"""Report whether Selfdex is ready for external read-only validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from argparse_utils import add_format_argument, add_root_argument
    from cli_output_utils import write_json_or_markdown
    from list_project_registry import build_payload as build_registry_payload
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.list_project_registry import build_payload as build_registry_payload


SCHEMA_VERSION = 1
SELFDEX_PROJECT_IDS = {"selfdex"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether the project registry is ready for external read-only validation."
    )
    add_root_argument(parser, help_text="Selfdex repository root.")
    parser.add_argument(
        "--minimum-external-projects",
        type=int,
        default=2,
        help="Minimum external read-only projects needed before claiming external validation readiness.",
    )
    add_format_argument(parser)
    return parser.parse_args(argv)


def is_selfdex_project(project: dict[str, Any]) -> bool:
    return str(project.get("project_id") or "").strip() in SELFDEX_PROJECT_IDS


def is_read_only(project: dict[str, Any]) -> bool:
    return "read-only" in str(project.get("write_policy") or "").lower()


def external_projects(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        project
        for project in registry.get("projects", [])
        if isinstance(project, dict) and not is_selfdex_project(project)
    ]


def make_finding(finding_id: str, severity: str, summary: str, *, project_id: str | None = None) -> dict[str, str]:
    finding = {
        "finding_id": finding_id,
        "severity": severity,
        "summary": summary,
    }
    if project_id:
        finding["project_id"] = project_id
    return finding


def build_findings(
    projects: list[dict[str, Any]],
    *,
    minimum_external_projects: int,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if len(projects) < minimum_external_projects:
        findings.append(
            make_finding(
                "external-project-count-low",
                "medium",
                (
                    f"Need at least {minimum_external_projects} external read-only projects; "
                    f"registry has {len(projects)}."
                ),
            )
        )

    for project in projects:
        project_id = str(project.get("project_id") or "").strip()
        if not is_read_only(project):
            findings.append(
                make_finding(
                    "external-project-not-read-only",
                    "high",
                    "External validation projects must be registered with a read-only write_policy.",
                    project_id=project_id,
                )
            )
        if not bool(project.get("path_exists")):
            findings.append(
                make_finding(
                    "external-project-path-missing",
                    "high",
                    "External validation project path does not exist on this machine.",
                    project_id=project_id,
                )
            )
    return findings


def readiness_status(projects: list[dict[str, Any]], findings: list[dict[str, str]], minimum_external_projects: int) -> str:
    if any(finding.get("severity") == "high" for finding in findings):
        return "blocked"
    if len(projects) < minimum_external_projects:
        return "needs_external_projects"
    return "ready"


def build_payload(root: Path, *, minimum_external_projects: int = 2) -> dict[str, Any]:
    registry = build_registry_payload(root)
    projects = external_projects(registry)
    findings = build_findings(projects, minimum_external_projects=minimum_external_projects)
    status = readiness_status(projects, findings, minimum_external_projects)
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_external_validation_readiness",
        "status": status,
        "validation_mode": "read_only",
        "external_value_proven": False,
        "minimum_external_projects": minimum_external_projects,
        "registered_project_count": registry.get("registered_project_count", 0),
        "external_project_count": len(projects),
        "read_only_external_project_count": sum(1 for project in projects if is_read_only(project)),
        "registry_path": registry.get("registry_path", ""),
        "finding_count": len(findings),
        "findings": findings,
        "external_projects": projects,
        "next_action": (
            "Register 2-3 real external repositories as read-only, generate top candidates, "
            "score them with the candidate quality rubric, then run the external validation report."
        ),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# External Validation Readiness",
        "",
        f"- status: `{payload['status']}`",
        f"- validation_mode: `{payload['validation_mode']}`",
        f"- external_value_proven: `{payload['external_value_proven']}`",
        f"- minimum_external_projects: `{payload['minimum_external_projects']}`",
        f"- external_project_count: `{payload['external_project_count']}`",
        f"- read_only_external_project_count: `{payload['read_only_external_project_count']}`",
        "",
        "## Findings",
        "",
    ]
    if payload["findings"]:
        for finding in payload["findings"]:
            project = f" project=`{finding['project_id']}`" if finding.get("project_id") else ""
            lines.append(
                f"- `{finding['severity']}` {finding['finding_id']}:{project} {finding['summary']}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## External Projects", ""])
    if not payload["external_projects"]:
        lines.append("- none")
    for project in payload["external_projects"]:
        lines.append(
            f"- `{project['project_id']}` path_exists=`{project['path_exists']}` "
            f"write_policy=`{project['write_policy']}`"
        )
    lines.extend(["", "## Next Action", "", payload["next_action"]])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_payload(
            Path(args.root).resolve(),
            minimum_external_projects=args.minimum_external_projects,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    write_json_or_markdown(payload, args.format, render_markdown)
    return 1 if payload["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
