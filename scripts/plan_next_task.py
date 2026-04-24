#!/usr/bin/env python3
"""Select the next Selfdex improvement candidate from local repository signals."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Candidate:
    source: str
    title: str
    decision: str
    priority_score: float
    risk: str
    rationale: list[str]
    suggested_checks: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pick the next Selfdex autopilot task.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args()


def run_json(root: Path, script_name: str) -> tuple[dict[str, Any] | None, str | None]:
    script_path = root / "scripts" / script_name
    if not script_path.exists():
        return None, f"missing script: {script_path}"

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.run(
        [sys.executable, str(script_path), "--root", str(root), "--pretty"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if process.returncode != 0:
        return None, process.stderr.strip() or f"{script_name} failed with {process.returncode}"
    try:
        return json.loads(process.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"{script_name} returned invalid JSON: {exc}"


def severity_score(severity: str) -> int:
    return {"high": 36, "medium": 26, "low": 14}.get(severity, 10)


def decision_multiplier(decision: str) -> float:
    return {
        "pick": 1.15,
        "needs_approval": 0.55,
        "defer": 0.65,
        "reject": 0.0,
        "hold": 0.4,
    }.get(decision, 1.0)


def collect_test_gap_candidates(payload: dict[str, Any]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for finding in payload.get("findings", []):
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity") or "low")
        title = str(finding.get("title") or finding.get("summary") or "Test gap")
        summary = str(finding.get("summary") or "")
        scenario = str(finding.get("scenario") or "")
        score = severity_score(severity)
        if finding.get("category") == "verification_gap":
            score += 6
        candidates.append(
            Candidate(
                source="test_gap",
                title=title,
                decision="pick" if severity == "high" else "monitor",
                priority_score=score,
                risk="medium",
                rationale=[item for item in (summary, scenario) if item],
                suggested_checks=[
                    "python -m compileall -q scripts",
                    "python scripts/plan_next_task.py --root . --format json",
                ],
            )
        )
    return candidates


def collect_refactor_candidates(payload: dict[str, Any]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for item in payload.get("refactor_candidates", []):
        if not isinstance(item, dict):
            continue
        decision = str(item.get("decision") or "defer")
        title = str(item.get("title") or "Refactor candidate")
        score = float(item.get("priority_score") or item.get("score") or 0)
        rationale = [str(value) for value in item.get("selection_rationale", []) if value]
        candidates.append(
            Candidate(
                source="refactor",
                title=title,
                decision=decision,
                priority_score=round(score * decision_multiplier(decision), 2),
                risk="medium" if decision == "pick" else "guarded",
                rationale=rationale[:3],
                suggested_checks=[
                    "python -m compileall -q scripts",
                    "python scripts/plan_next_task.py --root . --format json",
                ],
            )
        )
    return candidates


def collect_feature_candidates(payload: dict[str, Any]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for item in payload.get("small_feature_candidates", []):
        if not isinstance(item, dict):
            continue
        decision = str(item.get("decision") or "defer")
        title = str(item.get("title") or "Feature candidate")
        score = float(item.get("priority_score") or item.get("score") or 0)
        rationale = [str(value) for value in item.get("selection_rationale", []) if value]
        candidates.append(
            Candidate(
                source="feature_gap",
                title=title,
                decision=decision,
                priority_score=round(score * decision_multiplier(decision), 2),
                risk="guarded",
                rationale=rationale[:3],
                suggested_checks=[
                    "python -m compileall -q scripts",
                    "python scripts/plan_next_task.py --root . --format json",
                ],
            )
        )
    return candidates


def choose_candidate(root: Path) -> dict[str, Any]:
    loaders = (
        ("extract_test_gap_candidates.py", collect_test_gap_candidates),
        ("extract_refactor_candidates.py", collect_refactor_candidates),
        ("extract_feature_gap_candidates.py", collect_feature_candidates),
    )
    all_candidates: list[Candidate] = []
    errors: list[str] = []

    for script_name, collector in loaders:
        payload, error = run_json(root, script_name)
        if error:
            errors.append(error)
            continue
        if payload:
            all_candidates.extend(collector(payload))

    ranked = sorted(
        all_candidates,
        key=lambda item: (
            -item.priority_score,
            item.source,
            item.title,
        ),
    )
    selected = ranked[0] if ranked else None

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_next_task_plan",
        "candidate_count": len(ranked),
        "errors": errors,
        "selected": candidate_to_dict(selected) if selected else None,
        "top_candidates": [candidate_to_dict(item) for item in ranked[:5]],
        "recommended_topology": recommend_topology(selected),
    }


def candidate_to_dict(candidate: Candidate | None) -> dict[str, Any] | None:
    if candidate is None:
        return None
    return {
        "source": candidate.source,
        "title": candidate.title,
        "decision": candidate.decision,
        "priority_score": candidate.priority_score,
        "risk": candidate.risk,
        "rationale": candidate.rationale,
        "suggested_checks": candidate.suggested_checks,
    }


def recommend_topology(candidate: Candidate | None) -> dict[str, Any]:
    if candidate is None:
        return {
            "execution_topology": "autopilot-single",
            "agent_budget": 0,
            "reason": "No candidate was produced.",
        }
    if candidate.source == "test_gap":
        return {
            "execution_topology": "autopilot-parallel",
            "agent_budget": 2,
            "reason": "A test or verification gap can use explorer/reviewer lanes while the main thread scopes the fix.",
        }
    if candidate.decision == "pick":
        return {
            "execution_topology": "autopilot-mixed",
            "agent_budget": 3,
            "reason": "A picked implementation candidate should freeze the contract, then fan out implementation and review.",
        }
    return {
        "execution_topology": "autopilot-serial",
        "agent_budget": 1,
        "reason": "Candidate needs clarification or guarded handling before implementation.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    selected = payload.get("selected")
    topology = payload.get("recommended_topology") or {}
    lines = ["# Next Selfdex Task", ""]
    if selected:
        lines.extend(
            [
                f"- selected: `{selected['title']}`",
                f"- source: `{selected['source']}`",
                f"- decision: `{selected['decision']}`",
                f"- priority_score: `{selected['priority_score']}`",
                f"- risk: `{selected['risk']}`",
                f"- execution_topology: `{topology.get('execution_topology')}`",
                f"- agent_budget: `{topology.get('agent_budget')}`",
                f"- reason: {topology.get('reason')}",
                "",
                "## Rationale",
                "",
            ]
        )
        for item in selected.get("rationale", []) or ["No rationale captured."]:
            lines.append(f"- {item}")
        lines.extend(["", "## Suggested Checks", ""])
        for item in selected.get("suggested_checks", []):
            lines.append(f"- `{item}`")
    else:
        lines.append("- selected: `none`")

    if payload.get("errors"):
        lines.extend(["", "## Scan Errors", ""])
        for error in payload["errors"]:
            lines.append(f"- {error}")

    lines.extend(["", "## Top Candidates", ""])
    for item in payload.get("top_candidates", []):
        lines.append(f"- `{item['priority_score']}` {item['source']}: {item['title']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = choose_candidate(root)
    if args.format == "json":
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
