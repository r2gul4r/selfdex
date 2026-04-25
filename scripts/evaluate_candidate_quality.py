#!/usr/bin/env python3
"""Evaluate Selfdex candidate quality rubric scores."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
DIMENSIONS = (
    "real_problem",
    "user_value",
    "local_verifiability",
    "scope_smallness",
    "risk_reversibility",
)


@dataclass(frozen=True)
class CandidateQuality:
    candidate: str
    source_project: str
    source_signal: str
    evidence: str
    suggested_verification: str
    scores: dict[str, int]
    total: int
    verdict: str
    issues: list[str]
    human_notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate,
            "source_project": self.source_project,
            "source_signal": self.source_signal,
            "evidence": self.evidence,
            "suggested_verification": self.suggested_verification,
            "scores": self.scores,
            "total": self.total,
            "verdict": self.verdict,
            "issues": self.issues,
            "human_notes": self.human_notes,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate candidate quality rubric scores from JSON input."
    )
    parser.add_argument(
        "--input",
        help="JSON file containing one candidate, a candidate list, or {'candidates': [...]}. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args(argv)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def load_payload(input_path: str | None) -> Any:
    if input_path:
        with Path(input_path).open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    return json.loads(sys.stdin.read().lstrip("\ufeff"))


def candidate_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("candidates"), list):
        items = payload["candidates"]
    elif isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = [payload]
    else:
        raise ValueError("Input must be a JSON object, list, or object with a 'candidates' array.")

    candidates = [item for item in items if isinstance(item, dict)]
    if len(candidates) != len(items):
        raise ValueError("Every candidate entry must be a JSON object.")
    return candidates


def score_source(item: dict[str, Any]) -> dict[str, Any]:
    nested = item.get("scores")
    if isinstance(nested, dict):
        return nested
    return item


def parse_scores(item: dict[str, Any]) -> tuple[dict[str, int], list[str]]:
    source = score_source(item)
    scores: dict[str, int] = {}
    issues: list[str] = []
    for dimension in DIMENSIONS:
        raw_value = source.get(dimension)
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            issues.append(f"{dimension} must be an integer from 0 to 3")
            continue
        if raw_value < 0 or raw_value > 3:
            issues.append(f"{dimension} must be between 0 and 3")
            continue
        scores[dimension] = raw_value
    return scores, issues


def verdict_for(scores: dict[str, int]) -> str:
    total = sum(scores.values())
    minimum = min(scores.values())
    if 12 <= total <= 15 and minimum >= 2:
        return "strong"
    if (
        9 <= total <= 11
        and minimum >= 1
        and scores["real_problem"] >= 2
        and scores["local_verifiability"] >= 2
        and scores["risk_reversibility"] >= 2
    ):
        return "usable"
    if scores["scope_smallness"] <= 1:
        return "split"
    return "defer"


def evaluate_candidate(item: dict[str, Any]) -> CandidateQuality:
    scores, issues = parse_scores(item)
    if issues:
        total = sum(scores.values())
        verdict = "invalid"
    else:
        total = sum(scores.values())
        verdict = verdict_for(scores)

    return CandidateQuality(
        candidate=as_text(item.get("candidate") or item.get("title") or item.get("name")),
        source_project=as_text(item.get("source_project")),
        source_signal=as_text(item.get("source_signal")),
        evidence=as_text(item.get("evidence")),
        suggested_verification=as_text(item.get("suggested_verification")),
        scores=scores,
        total=total,
        verdict=verdict,
        issues=issues,
        human_notes=as_text(item.get("human_notes")),
    )


def evaluate_payload(payload: Any) -> dict[str, Any]:
    results = [evaluate_candidate(item).to_dict() for item in candidate_items(payload)]
    verdict_counts = {verdict: 0 for verdict in ("strong", "usable", "defer", "split", "invalid")}
    for result in results:
        verdict = result["verdict"]
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "candidate_quality_evaluation",
        "status": "fail" if verdict_counts["invalid"] else "pass",
        "candidate_count": len(results),
        "verdict_counts": verdict_counts,
        "results": results,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Candidate Quality Evaluation",
        "",
        f"- status: `{payload['status']}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        "",
        "## Verdict Counts",
        "",
    ]
    for verdict, count in payload["verdict_counts"].items():
        lines.append(f"- {verdict}: `{count}`")

    lines.extend(["", "## Candidates", ""])
    if not payload["results"]:
        lines.append("- none")
    for result in payload["results"]:
        candidate = result["candidate"] or "(untitled candidate)"
        lines.append(
            f"- `{result['verdict']}` total=`{result['total']}` candidate={candidate}"
        )
        if result["issues"]:
            lines.append(f"  issues: {'; '.join(result['issues'])}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = evaluate_payload(load_payload(args.input))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(payload))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
