#!/usr/bin/env python3
"""Prepare human-fillable candidate quality scoring templates."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from argparse_utils import parse_planner_report_args
    from planner_payload_utils import load_json, planner_candidates
except ModuleNotFoundError:
    from scripts.argparse_utils import parse_planner_report_args
    from scripts.planner_payload_utils import load_json, planner_candidates


SCHEMA_VERSION = 1
DIMENSIONS = (
    "real_problem",
    "user_value",
    "local_verifiability",
    "scope_smallness",
    "risk_reversibility",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return parse_planner_report_args(
        "Convert planner candidates into a manual candidate quality scoring template.",
        argv,
    )


def first_text(values: list[Any]) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def template_candidate(project_id: str, candidate: dict[str, Any]) -> dict[str, Any]:
    rationale = candidate.get("rationale") if isinstance(candidate.get("rationale"), list) else []
    checks = (
        candidate.get("suggested_checks")
        if isinstance(candidate.get("suggested_checks"), list)
        else []
    )
    title = str(candidate.get("title") or candidate.get("candidate") or "").strip()
    source_project = str(candidate.get("source_project") or project_id).strip()
    return {
        "candidate": title,
        "source_project": source_project,
        "source_signal": str(candidate.get("source") or "").strip(),
        "evidence": first_text(rationale),
        "suggested_verification": first_text(checks),
        "scores": {dimension: None for dimension in DIMENSIONS},
        "score_status": "needs_human_scoring",
        "human_notes": "",
    }


def build_template(planner_payload: dict[str, Any], project_id: str) -> dict[str, Any]:
    candidates = [
        template_candidate(project_id, candidate)
        for candidate in planner_candidates(planner_payload)
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "candidate_quality_template",
        "score_status": "needs_human_scoring",
        "instructions": "Fill each score with an integer from 0 to 3 before running scripts/evaluate_candidate_quality.py.",
        "dimensions": list(DIMENSIONS),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Candidate Quality Scoring Template",
        "",
        f"- score_status: `{payload['score_status']}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        "",
        "## Dimensions",
        "",
    ]
    for dimension in payload["dimensions"]:
        lines.append(f"- `{dimension}`: fill with `0-3`")

    lines.extend(["", "## Candidates", ""])
    if not payload["candidates"]:
        lines.append("- none")
    for candidate in payload["candidates"]:
        lines.extend(
            [
                f"### {candidate['candidate'] or '(untitled candidate)'}",
                "",
                f"- source_project: `{candidate['source_project']}`",
                f"- source_signal: `{candidate['source_signal']}`",
                f"- evidence: {candidate['evidence'] or 'none'}",
                f"- suggested_verification: `{candidate['suggested_verification'] or 'none'}`",
                f"- score_status: `{candidate['score_status']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_template(load_json(args.planner), args.project_id)
    except (OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(payload))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
