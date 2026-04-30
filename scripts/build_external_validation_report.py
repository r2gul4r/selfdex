#!/usr/bin/env python3
"""Build a read-only external validation report from planner and quality payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from argparse_utils import parse_planner_report_args
    from list_project_registry import build_payload as build_registry_payload
    from planner_payload_utils import load_json, planner_candidates
except ModuleNotFoundError:
    from scripts.argparse_utils import parse_planner_report_args
    from scripts.list_project_registry import build_payload as build_registry_payload
    from scripts.planner_payload_utils import load_json, planner_candidates


SCHEMA_VERSION = 1
SELFDEX_PROJECT_IDS = {"selfdex"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return parse_planner_report_args(
        "Build a supervised read-only validation report for planner candidates.",
        argv,
        include_root=True,
        include_quality=True,
    )


def quality_by_candidate(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not payload:
        return {}
    results = payload.get("results")
    if not isinstance(results, list):
        return {}

    matched: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict):
            continue
        candidate = str(result.get("candidate") or "").strip()
        if candidate:
            matched[candidate] = result
    return matched


def registry_project(registry: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    for project in registry.get("projects", []):
        if isinstance(project, dict) and project.get("project_id") == project_id:
            return project
    return None


def external_project_count(registry: dict[str, Any]) -> int:
    count = 0
    for project in registry.get("projects", []):
        if not isinstance(project, dict):
            continue
        project_id = str(project.get("project_id") or "").strip()
        if project_id and project_id not in SELFDEX_PROJECT_IDS:
            count += 1
    return count


def summarize_candidate(
    project_id: str,
    candidate: dict[str, Any],
    quality_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    title = str(candidate.get("title") or candidate.get("candidate") or "").strip()
    quality = quality_index.get(title)
    return {
        "project_id": project_id,
        "title": title,
        "source": candidate.get("source", ""),
        "work_type": candidate.get("work_type", ""),
        "decision": candidate.get("decision", ""),
        "priority_score": candidate.get("priority_score"),
        "risk": candidate.get("risk", ""),
        "rationale": candidate.get("rationale", []) if isinstance(candidate.get("rationale"), list) else [],
        "suggested_checks": (
            candidate.get("suggested_checks", [])
            if isinstance(candidate.get("suggested_checks"), list)
            else []
        ),
        "quality": {
            "status": "scored" if quality else "missing",
            "total": quality.get("total") if quality else None,
            "verdict": quality.get("verdict") if quality else "needs_scoring",
            "scores": quality.get("scores") if quality else {},
            "issues": quality.get("issues") if quality else [],
        },
        "human_review_status": "pending",
    }


def validation_findings(
    registry: dict[str, Any],
    project: dict[str, Any] | None,
    candidates: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    external_count = external_project_count(registry)
    if external_count < 2:
        findings.append(
            {
                "finding_id": "external-project-count-low",
                "severity": "medium",
                "summary": "External validation still needs 2-3 non-selfdex read-only projects.",
            }
        )
    if project is None:
        findings.append(
            {
                "finding_id": "project-not-registered",
                "severity": "high",
                "summary": "Report project_id is not present in PROJECT_REGISTRY.md.",
            }
        )
    elif "read-only" not in str(project.get("write_policy", "")).lower() and project.get("project_id") != "selfdex":
        findings.append(
            {
                "finding_id": "project-not-read-only",
                "severity": "high",
                "summary": "External validation project is not marked read-only.",
            }
        )
    if any(candidate["quality"]["status"] == "missing" for candidate in candidates):
        findings.append(
            {
                "finding_id": "candidate-quality-missing",
                "severity": "medium",
                "summary": "One or more candidates still need rubric scoring.",
            }
        )
    return findings


def report_status(findings: list[dict[str, str]]) -> str:
    if any(item["severity"] == "high" for item in findings):
        return "fail"
    if any(item["finding_id"] == "candidate-quality-missing" for item in findings):
        return "needs_scoring"
    return "pass"


def build_report(
    root: Path,
    planner_payload: dict[str, Any],
    quality_payload: dict[str, Any] | None,
    project_id: str,
) -> dict[str, Any]:
    registry = build_registry_payload(root)
    project = registry_project(registry, project_id)
    quality_index = quality_by_candidate(quality_payload)
    candidates = [
        summarize_candidate(project_id, candidate, quality_index)
        for candidate in planner_candidates(planner_payload)
    ]
    findings = validation_findings(registry, project, candidates)
    status = report_status(findings)
    external_value_proven = (
        status == "pass"
        and bool(candidates)
        and all(candidate["quality"]["status"] == "scored" for candidate in candidates)
        and any(candidate["quality"]["verdict"] in {"strong", "usable"} for candidate in candidates)
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_external_validation_report",
        "status": status,
        "validation_mode": "read_only",
        "external_value_proven": external_value_proven,
        "project": project
        or {
            "project_id": project_id,
            "write_policy": "unknown",
            "path_exists": False,
            "verification": [],
        },
        "registry": {
            "registered_project_count": registry.get("registered_project_count", 0),
            "external_project_count": external_project_count(registry),
            "registry_path": registry.get("registry_path", ""),
        },
        "candidate_count": len(candidates),
        "scored_candidate_count": sum(1 for candidate in candidates if candidate["quality"]["status"] == "scored"),
        "human_review_status": "pending",
        "findings": findings,
        "candidates": candidates,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    project = payload["project"]
    lines = [
        "# External Read-Only Validation Report",
        "",
        f"- status: `{payload['status']}`",
        f"- validation_mode: `{payload['validation_mode']}`",
        f"- external_value_proven: `{payload['external_value_proven']}`",
        f"- project_id: `{project.get('project_id')}`",
        f"- write_policy: `{project.get('write_policy')}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- scored_candidate_count: `{payload['scored_candidate_count']}`",
        f"- human_review_status: `{payload['human_review_status']}`",
        "",
        "## Findings",
        "",
    ]
    if payload["findings"]:
        for finding in payload["findings"]:
            lines.append(f"- `{finding['severity']}` {finding['finding_id']}: {finding['summary']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Candidates", ""])
    if not payload["candidates"]:
        lines.append("- none")
    for candidate in payload["candidates"]:
        quality = candidate["quality"]
        lines.append(
            f"- `{quality['verdict']}` total=`{quality['total']}` "
            f"priority=`{candidate['priority_score']}` title={candidate['title']}"
        )
        lines.append(f"  quality_status: `{quality['status']}`")
        lines.append(f"  human_review_status: `{candidate['human_review_status']}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        planner_payload = load_json(args.planner)
        quality_payload = load_json(args.quality) if args.quality else None
        report = build_report(root, planner_payload, quality_payload, args.project_id)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
