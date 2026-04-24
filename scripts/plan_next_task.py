#!/usr/bin/env python3
"""Select the next Selfdex improvement candidate from local repository signals."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from markdown_utils import clean_markdown_value, extract_markdown_section
    from plan_orchestration_fit import build_orchestration_fit, orchestration_fit_to_dict
except ModuleNotFoundError:
    from scripts.markdown_utils import clean_markdown_value, extract_markdown_section
    from scripts.plan_orchestration_fit import build_orchestration_fit, orchestration_fit_to_dict


@dataclass(frozen=True)
class Candidate:
    source: str
    work_type: str
    title: str
    decision: str
    priority_score: float
    risk: str
    rationale: list[str]
    suggested_checks: list[str]
    source_signals: dict[str, Any] = field(default_factory=dict)


CAMPAIGN_QUEUE_SOURCE = "campaign_queue"
CAMPAIGN_QUEUE_BASE_SCORE = 80.0
CAMPAIGN_QUEUE_ORDER_STEP = 2.0
CAMPAIGN_GOAL_MATCH_BONUS = 6.0
CAMPAIGN_GOAL_MATCH_BONUS_CAP = 18.0

STOP_WORDS = {
    "and",
    "can",
    "for",
    "from",
    "into",
    "that",
    "the",
    "this",
    "with",
}

WORK_TYPE_KEYWORDS = {
    "repair": {
        "bug",
        "broken",
        "failing",
        "failure",
        "fix",
        "regression",
        "repair",
        "restore",
    },
    "hardening": {
        "budget",
        "check",
        "checker",
        "coverage",
        "drift",
        "fixture",
        "guard",
        "reject",
        "test",
        "tests",
        "validation",
        "verify",
    },
    "automation": {
        "automate",
        "automation",
        "generated",
        "record",
        "recorder",
        "refresh",
        "run",
        "runs",
        "write",
        "writes",
    },
    "capability": {
        "analysis",
        "classification",
        "classify",
        "evaluator",
        "multi",
        "orchestration",
        "planner",
        "project",
        "registry",
        "socratic",
        "work_type",
    },
    "improvement": {
        "cleanup",
        "docs",
        "improve",
        "improvement",
        "refactor",
        "reduce",
        "simplify",
    },
}

WORK_TYPE_PRIORITY = (
    "repair",
    "hardening",
    "automation",
    "capability",
    "improvement",
)

WORK_TYPE_DESCRIPTIONS = {
    "repair": "restore broken behavior",
    "hardening": "make existing behavior harder to break",
    "improvement": "improve quality without adding a new capability",
    "capability": "add a new system ability",
    "automation": "automate repeated coordination work",
}
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


def parse_campaign_goal(text: str) -> str:
    for line in extract_markdown_section(text, "Campaign"):
        match = re.match(r"^\s*-\s*goal:\s*(.+?)\s*$", line)
        if match:
            return clean_markdown_value(match.group(1))
    return ""


def parse_campaign_queue(text: str) -> list[str]:
    candidates: list[str] = []
    for line in extract_markdown_section(text, "Candidate Queue"):
        match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if not match:
            continue
        title = clean_markdown_value(match.group(1))
        if title:
            candidates.append(title)
    return candidates


def normalize_goal_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("er"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def meaningful_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in re.split(r"[^a-z0-9]+", value.lower()):
        if len(raw_token) < 3 or raw_token in STOP_WORDS:
            continue
        tokens.add(normalize_goal_token(raw_token))
    return tokens


def campaign_goal_matches(goal: str, title: str) -> list[str]:
    if not goal:
        return []
    return sorted(meaningful_tokens(goal) & meaningful_tokens(title))


def classify_work_type(title: str, default: str = "improvement") -> str:
    tokens = meaningful_tokens(title)
    for work_type in WORK_TYPE_PRIORITY:
        keywords = {normalize_goal_token(keyword) for keyword in WORK_TYPE_KEYWORDS[work_type]}
        if tokens & keywords:
            return work_type
    return default


def build_socratic_evaluation(candidate: Candidate, campaign_goal: str) -> list[dict[str, str]]:
    matches = campaign_goal_matches(campaign_goal, candidate.title)
    if matches:
        goal_fit = f"Direct campaign overlap: {', '.join(matches)}."
    elif candidate.source == CAMPAIGN_QUEUE_SOURCE:
        goal_fit = "Explicit campaign queue item; no direct keyword overlap found."
    else:
        goal_fit = f"Indirect fit through {candidate.source} repository signals."

    evidence = candidate.rationale[0] if candidate.rationale else f"Produced by {candidate.source}."
    primary_check = candidate.suggested_checks[0] if candidate.suggested_checks else "No check suggested."
    work_description = WORK_TYPE_DESCRIPTIONS.get(candidate.work_type, "unclassified work")

    return [
        {
            "question": "Does this serve the current campaign goal?",
            "answer": goal_fit,
        },
        {
            "question": "What kind of work is this?",
            "answer": f"{candidate.work_type}: {work_description}.",
        },
        {
            "question": "What evidence supports doing it?",
            "answer": evidence,
        },
        {
            "question": "What is the smallest useful scope?",
            "answer": candidate.title,
        },
        {
            "question": "How can it be verified locally?",
            "answer": primary_check,
        },
        {
            "question": "Should orchestration be considered?",
            "answer": "Consider subagents only if discovery, implementation, or review can be split into independently verified write sets.",
        },
    ]


def collect_campaign_candidates(root: Path) -> tuple[list[Candidate], str]:
    campaign_path = root / "CAMPAIGN_STATE.md"
    if not campaign_path.exists():
        return [], ""

    text = campaign_path.read_text(encoding="utf-8")
    goal = parse_campaign_goal(text)
    queue_titles = parse_campaign_queue(text)
    queue_count = len(queue_titles)
    candidates: list[Candidate] = []

    for index, title in enumerate(queue_titles):
        matches = campaign_goal_matches(goal, title)
        order_bonus = (queue_count - index) * CAMPAIGN_QUEUE_ORDER_STEP
        goal_bonus = min(
            len(matches) * CAMPAIGN_GOAL_MATCH_BONUS,
            CAMPAIGN_GOAL_MATCH_BONUS_CAP,
        )
        priority_score = CAMPAIGN_QUEUE_BASE_SCORE + order_bonus + goal_bonus
        alignment = ", ".join(matches) if matches else "no direct keyword overlap"
        candidates.append(
            Candidate(
                source=CAMPAIGN_QUEUE_SOURCE,
                work_type=classify_work_type(title, default="capability"),
                title=title,
                decision="pick",
                priority_score=round(priority_score, 2),
                risk="guarded",
                rationale=[
                    f"Candidate Queue item {index + 1} from CAMPAIGN_STATE.md.",
                    f"Campaign goal alignment: {alignment}.",
                    "Campaign queue candidates have a higher base score than imported refactor candidates.",
                ],
                suggested_checks=[
                    "python -m compileall -q scripts",
                    "$env:PYTHONIOENCODING='utf-8'; python .\\scripts\\plan_next_task.py --root . --format json",
                    "$env:PYTHONIOENCODING='utf-8'; python .\\scripts\\plan_next_task.py --root . --format markdown",
                ],
                source_signals={
                    "queue_index": index,
                    "queue_count": queue_count,
                    "goal_match_count": len(matches),
                },
            )
        )
    return candidates, goal


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
                work_type="hardening",
                title=title,
                decision="pick" if severity == "high" else "monitor",
                priority_score=score,
                risk="medium",
                rationale=[item for item in (summary, scenario) if item],
                suggested_checks=[
                    "python -m compileall -q scripts",
                    "python scripts/plan_next_task.py --root . --format json",
                ],
                source_signals={
                    "severity": severity,
                    "category": finding.get("category"),
                },
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
                work_type="improvement",
                title=title,
                decision=decision,
                priority_score=round(score * decision_multiplier(decision), 2),
                risk="medium" if decision == "pick" else "guarded",
                rationale=rationale[:3],
                suggested_checks=[
                    "python -m compileall -q scripts",
                    "python scripts/plan_next_task.py --root . --format json",
                ],
                source_signals=dict(item.get("source_signals") or {}),
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
                work_type="capability",
                title=title,
                decision=decision,
                priority_score=round(score * decision_multiplier(decision), 2),
                risk="guarded",
                rationale=rationale[:3],
                suggested_checks=[
                    "python -m compileall -q scripts",
                    "python scripts/plan_next_task.py --root . --format json",
                ],
                source_signals=dict(item.get("source_signals") or {}),
            )
        )
    return candidates


def choose_candidate(root: Path) -> dict[str, Any]:
    loaders = (
        ("extract_test_gap_candidates.py", collect_test_gap_candidates),
        ("extract_refactor_candidates.py", collect_refactor_candidates),
        ("extract_feature_gap_candidates.py", collect_feature_candidates),
    )
    campaign_candidates, campaign_goal = collect_campaign_candidates(root)
    all_candidates: list[Candidate] = list(campaign_candidates)
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
        "campaign_goal": campaign_goal,
        "campaign_queue_candidate_count": len(campaign_candidates),
        "errors": errors,
        "selected": candidate_to_dict(selected, campaign_goal) if selected else None,
        "top_candidates": [candidate_to_dict(item, campaign_goal) for item in ranked[:5]],
        "recommended_topology": recommend_topology(selected),
    }


def candidate_to_dict(
    candidate: Candidate | None,
    campaign_goal: str = "",
) -> dict[str, Any] | None:
    if candidate is None:
        return None
    payload = {
        "source": candidate.source,
        "work_type": candidate.work_type,
        "title": candidate.title,
        "decision": candidate.decision,
        "priority_score": candidate.priority_score,
        "risk": candidate.risk,
        "rationale": candidate.rationale,
        "suggested_checks": candidate.suggested_checks,
        "socratic_evaluation": build_socratic_evaluation(candidate, campaign_goal),
    }
    if candidate.source_signals:
        payload["source_signals"] = candidate.source_signals
    return payload


def recommend_topology(candidate: Candidate | None) -> dict[str, Any]:
    fit = build_orchestration_fit(candidate)
    fit_payload = orchestration_fit_to_dict(fit)
    if candidate is None:
        return {
            "execution_topology": "autopilot-single",
            "agent_budget": 0,
            "reason": "No candidate was produced.",
            "spawn_decision": "no_spawn",
            "write_sets": ["main: no candidate to implement"],
            "orchestration_fit": fit_payload,
        }

    if candidate.decision != "pick":
        return {
            "execution_topology": "autopilot-serial",
            "agent_budget": 1,
            "reason": "Candidate needs clarification or guarded handling before implementation.",
            "spawn_decision": "no_spawn_until_contract_is_clear",
            "write_sets": ["main: clarify contract before delegation"],
            "orchestration_fit": fit_payload,
        }

    if fit.orchestration_value == "low":
        return {
            "execution_topology": "autopilot-single",
            "agent_budget": 0,
            "reason": (
                f"{fit.task_size_class} task with {fit.handoff_cost} handoff cost and "
                f"{fit.parallel_gain} parallel gain; delegation overhead exceeds expected speedup."
            ),
            "spawn_decision": "no_spawn_handoff_cost_exceeds_gain",
            "write_sets": ["main: implement and verify the selected bounded change"],
            "orchestration_fit": fit_payload,
        }

    if fit.orchestration_value == "high":
        return {
            "execution_topology": "autopilot-parallel",
            "agent_budget": 3,
            "reason": (
                "Large or separable candidate with enough independent write sets and verification paths "
                "to justify concurrent-state workers after the contract is frozen."
            ),
            "spawn_decision": "concurrent_state_recommended_when_contract_frozen",
            "write_sets": [
                "main: own root STATE.md, CAMPAIGN_STATE.md, runs/, integration, and commit",
                "worker: own one disjoint slice state file and write set",
                "reviewer: read-only contract and regression review",
            ],
            "orchestration_fit": fit_payload,
        }

    return {
        "execution_topology": "autopilot-mixed",
        "agent_budget": 2,
        "reason": (
            "Candidate is large or verification-sensitive, but collision risk or handoff cost means "
            "parallel workers should wait until write sets are proven disjoint."
        ),
        "spawn_decision": "sidecar_recommended_freeze_write_sets_first",
        "write_sets": [
            "main: freeze contract, own shared state, and integrate",
            "explorer: read-only slice and write-set discovery",
            "reviewer: read-only verification and regression review",
        ],
        "orchestration_fit": fit_payload,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    selected = payload.get("selected")
    topology = payload.get("recommended_topology") or {}
    orchestration_fit = topology.get("orchestration_fit") or {}
    lines = ["# Next Selfdex Task", ""]
    if selected:
        lines.extend(
            [
                f"- selected: `{selected['title']}`",
                f"- source: `{selected['source']}`",
                f"- work_type: `{selected['work_type']}`",
                f"- decision: `{selected['decision']}`",
                f"- priority_score: `{selected['priority_score']}`",
                f"- risk: `{selected['risk']}`",
                f"- execution_topology: `{topology.get('execution_topology')}`",
                f"- agent_budget: `{topology.get('agent_budget')}`",
                f"- spawn_decision: `{topology.get('spawn_decision')}`",
                f"- reason: {topology.get('reason')}",
                "",
                "## Orchestration Fit",
                "",
                f"- task_size_class: `{orchestration_fit.get('task_size_class')}`",
                f"- estimated_write_set_count: `{orchestration_fit.get('estimated_write_set_count')}`",
                f"- shared_file_collision_risk: `{orchestration_fit.get('shared_file_collision_risk')}`",
                f"- handoff_cost: `{orchestration_fit.get('handoff_cost')}`",
                f"- parallel_gain: `{orchestration_fit.get('parallel_gain')}`",
                f"- verification_independence: `{orchestration_fit.get('verification_independence')}`",
                f"- orchestration_value: `{orchestration_fit.get('orchestration_value')}`",
                "",
                "## Rationale",
                "",
            ]
        )
        for item in selected.get("rationale", []) or ["No rationale captured."]:
            lines.append(f"- {item}")
        lines.extend(["", "## Socratic Evaluation", ""])
        for item in selected.get("socratic_evaluation", []):
            lines.append(f"- {item['question']} {item['answer']}")
        lines.extend(["", "## Suggested Checks", ""])
        for item in selected.get("suggested_checks", []):
            lines.append(f"- `{item}`")

        lines.extend(["", "## Write Sets", ""])
        for item in topology.get("write_sets", []):
            lines.append(f"- {item}")
    else:
        lines.append("- selected: `none`")

    if payload.get("errors"):
        lines.extend(["", "## Scan Errors", ""])
        for error in payload["errors"]:
            lines.append(f"- {error}")

    lines.extend(["", "## Top Candidates", ""])
    for item in payload.get("top_candidates", []):
        lines.append(
            f"- `{item['priority_score']}` {item['source']} "
            f"[{item['work_type']}]: {item['title']}"
        )
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
