#!/usr/bin/env python3
"""Generate a read-only external validation proof package."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from argparse_utils import add_format_argument, add_root_argument
    from build_external_candidate_snapshot import build_snapshot, render_markdown as render_snapshot_markdown
    from build_external_validation_report import build_report, render_markdown as render_report_markdown
    from check_external_validation_readiness import build_payload as build_readiness_payload
    from cli_output_utils import write_json_or_markdown
    from evaluate_candidate_quality import DIMENSIONS, evaluate_payload
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.build_external_candidate_snapshot import build_snapshot, render_markdown as render_snapshot_markdown
    from scripts.build_external_validation_report import build_report, render_markdown as render_report_markdown
    from scripts.check_external_validation_readiness import build_payload as build_readiness_payload
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.evaluate_candidate_quality import DIMENSIONS, evaluate_payload


SCHEMA_VERSION = 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write an external validation proof package under runs/.")
    add_root_argument(parser, help_text="Selfdex repository root.")
    parser.add_argument("--limit", type=int, default=3, help="Top candidates per project. Defaults to 3.")
    parser.add_argument("--timestamp", help="Optional package timestamp in YYYYMMDD-HHMMSS format.")
    parser.add_argument(
        "--project-id",
        action="append",
        dest="project_ids",
        help="Optional project id to include. Repeat to select multiple projects.",
    )
    add_format_argument(parser, default="json", help_text="Output format. Defaults to json.")
    return parser.parse_args(argv)


def now_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def score_candidate(candidate: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    rationale = candidate.get("rationale") if isinstance(candidate.get("rationale"), list) else []
    checks = candidate.get("suggested_checks") if isinstance(candidate.get("suggested_checks"), list) else []
    signals = candidate.get("source_signals") if isinstance(candidate.get("source_signals"), dict) else {}
    paths = signals.get("paths") if isinstance(signals.get("paths"), list) else []
    work_type = str(candidate.get("work_type") or "")
    risk = str(candidate.get("risk") or "").lower()

    scores = {
        "real_problem": 3 if rationale or signals.get("evidence") else 2,
        "user_value": 3 if work_type in {"direction", "capability"} else 2,
        "local_verifiability": 3 if checks else 1,
        "scope_smallness": 3 if 0 < len(paths) <= 2 else 2 if len(paths) <= 4 else 1,
        "risk_reversibility": 3 if risk in {"low", "guarded", "medium", ""} else 2,
    }
    evidence = ""
    if rationale:
        evidence = str(rationale[0])
    elif isinstance(signals.get("evidence"), list) and signals["evidence"]:
        first = signals["evidence"][0]
        if isinstance(first, dict):
            evidence = str(first.get("quote") or first.get("signal") or "")
    return {
        "candidate": str(candidate.get("title") or "").strip(),
        "source_project": str(project.get("project_id") or "").strip(),
        "source_signal": str(candidate.get("source") or "").strip(),
        "evidence": evidence,
        "suggested_verification": str(checks[0]) if checks else "manual read-only review",
        "scores": scores,
        "score_status": "operator_scored_from_read_only_evidence",
        "human_notes": "Scored from repository evidence only; no target-project writes were performed.",
    }


def project_snapshot_payload(snapshot: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": snapshot["schema_version"],
        "analysis_kind": snapshot["analysis_kind"],
        "generated_at": snapshot["generated_at"],
        "validation_mode": snapshot["validation_mode"],
        "external_value_proven": snapshot["external_value_proven"],
        "root": snapshot["root"],
        "requested_project_ids": [project["project_id"]],
        "selection": {
            "mode": "package_project",
            "requested_project_ids": [project["project_id"]],
            "selected_project_ids": [project["project_id"]],
            "missing_project_ids": [],
        },
        "project_count": 1,
        "candidate_count": project.get("candidate_count", 0),
        "scanner_error_count": len(project.get("scanner_errors", [])),
        "human_review_status": project.get("human_review_status", "pending"),
        "projects": [project],
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_score_markdown(project: dict[str, Any], quality_payload: dict[str, Any]) -> str:
    lines = [
        "# External Validation Human Score",
        "",
        f"- project_id: `{project.get('project_id')}`",
        "- scoring_mode: `operator_scored_from_read_only_evidence`",
        f"- candidate_count: `{quality_payload['candidate_count']}`",
        "",
        "## Rubric",
        "",
    ]
    for dimension in DIMENSIONS:
        lines.append(f"- `{dimension}`: 0-3")
    lines.extend(["", "## Scores", ""])
    for result in quality_payload["results"]:
        lines.append(f"### {result['candidate']}")
        lines.append("")
        lines.append(f"- verdict: `{result['verdict']}`")
        lines.append(f"- total: `{result['total']}`")
        for dimension in DIMENSIONS:
            lines.append(f"- {dimension}: `{result['scores'].get(dimension)}`")
        lines.append(f"- evidence: {result['evidence'] or 'none'}")
        lines.append(f"- suggested_verification: `{result['suggested_verification'] or 'none'}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_summary_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# External Validation Summary",
        "",
        f"- status: `{payload['status']}`",
        f"- external_value_proven: `{payload['external_value_proven']}`",
        f"- generated_at: `{payload['generated_at']}`",
        f"- project_count: `{payload['project_count']}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        "",
        "## Rubric",
        "",
        "| criterion | description |",
        "| :-- | :-- |",
        "| real_problem | Candidate is grounded in concrete repository evidence. |",
        "| user_value | Fixing it would help a user, developer, or maintainer. |",
        "| scope_smallness | The work can fit into one bounded patch or should be split. |",
        "| local_verifiability | There is a local command or clear manual check for review. |",
        "| risk_reversibility | The change is easy to review, revert, or contain. |",
        "",
        "## Projects",
        "",
        "| project | status | candidates | scored | verdicts | artifacts |",
        "| :-- | :-- | --: | --: | :-- | :-- |",
    ]
    for project in payload["projects"]:
        artifacts = "<br>".join(project["artifacts"].values())
        verdicts = ", ".join(f"{key}:{value}" for key, value in project["verdict_counts"].items() if value) or "none"
        lines.append(
            f"| {project['project_id']} | {project['status']} | {project['candidate_count']} | "
            f"{project['scored_candidate_count']} | {verdicts} | {artifacts} |"
        )
    lines.extend(["", "## Notes", ""])
    lines.append("- Target repositories were scanned read-only; no target-project writes were performed.")
    lines.append("- Scores are operator scoring from local evidence, intended as reviewable proof artifacts.")
    return "\n".join(lines) + "\n"


def build_package(
    root: Path,
    *,
    limit: int = 3,
    timestamp: str | None = None,
    project_ids: list[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    stamp = timestamp or now_timestamp()
    output_dir = root / "runs" / "external-validation"
    readiness = build_readiness_payload(root)
    snapshot = build_snapshot(root, project_ids=project_ids, limit=limit)

    projects: list[dict[str, Any]] = []
    for project in snapshot.get("projects", []):
        if not isinstance(project, dict):
            continue
        project_id = str(project.get("project_id") or "").strip()
        if not project_id:
            continue
        project_payload = project_snapshot_payload(snapshot, project)
        quality_input = {
            "candidates": [
                score_candidate(candidate, project)
                for candidate in project.get("top_candidates", [])
                if isinstance(candidate, dict)
            ]
        }
        quality_payload = evaluate_payload(quality_input)
        report_payload = build_report(root, project_payload, quality_payload, project_id)

        snapshot_path = output_dir / f"{project_id}-snapshot.md"
        score_path = output_dir / f"{project_id}-human-score.md"
        report_path = output_dir / f"{project_id}-report.md"
        score_json_path = output_dir / f"{project_id}-human-score.json"
        write_text(snapshot_path, render_snapshot_markdown(project_payload))
        write_text(score_path, render_score_markdown(project, quality_payload))
        write_text(score_json_path, json.dumps(quality_payload, ensure_ascii=False, indent=2) + "\n")
        write_text(report_path, render_report_markdown(report_payload))

        projects.append(
            {
                "project_id": project_id,
                "status": report_payload["status"],
                "candidate_count": report_payload["candidate_count"],
                "scored_candidate_count": report_payload["scored_candidate_count"],
                "verdict_counts": quality_payload["verdict_counts"],
                "artifacts": {
                    "snapshot": str(snapshot_path.relative_to(root).as_posix()),
                    "human_score": str(score_path.relative_to(root).as_posix()),
                    "human_score_json": str(score_json_path.relative_to(root).as_posix()),
                    "report": str(report_path.relative_to(root).as_posix()),
                },
            }
        )

    candidate_count = sum(project["candidate_count"] for project in projects)
    scored_count = sum(project["scored_candidate_count"] for project in projects)
    useful_verdict_count = sum(
        project["verdict_counts"].get("strong", 0) + project["verdict_counts"].get("usable", 0)
        for project in projects
    )
    report_pass_count = sum(1 for project in projects if project["status"] == "pass")
    external_value_proven = (
        readiness.get("status") == "ready"
        and len(projects) >= readiness.get("minimum_external_projects", 2)
        and candidate_count > 0
        and scored_count == candidate_count
        and useful_verdict_count > 0
        and report_pass_count == len(projects)
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_external_validation_package",
        "generated_at": utc_timestamp(),
        "timestamp": stamp,
        "status": "pass" if external_value_proven else "needs_review",
        "validation_mode": "read_only",
        "external_value_proven": external_value_proven,
        "readiness_status": readiness.get("status"),
        "project_count": len(projects),
        "candidate_count": candidate_count,
        "scored_candidate_count": scored_count,
        "useful_verdict_count": useful_verdict_count,
        "output_dir": str(output_dir.relative_to(root).as_posix()),
        "projects": projects,
    }
    summary_path = output_dir / "summary.md"
    write_text(summary_path, render_summary_markdown(payload))
    payload["summary_path"] = str(summary_path.relative_to(root).as_posix())
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# External Validation Package",
        "",
        f"- status: `{payload['status']}`",
        f"- external_value_proven: `{payload['external_value_proven']}`",
        f"- readiness_status: `{payload['readiness_status']}`",
        f"- project_count: `{payload['project_count']}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- useful_verdict_count: `{payload.get('useful_verdict_count', 0)}`",
        f"- summary_path: `{payload.get('summary_path', '')}`",
        "",
        "## Projects",
        "",
    ]
    for project in payload["projects"]:
        lines.append(
            f"- `{project['project_id']}` status=`{project['status']}` "
            f"candidates=`{project['candidate_count']}` scored=`{project['scored_candidate_count']}`"
        )
    if not payload["projects"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_package(
            Path(args.root),
            limit=args.limit,
            timestamp=args.timestamp,
            project_ids=args.project_ids,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    write_json_or_markdown(payload, args.format, render_markdown)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
