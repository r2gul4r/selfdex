#!/usr/bin/env python3
"""Select the next Selfdex improvement candidate from local repository signals."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from argparse_utils import add_format_argument, add_root_argument
    from plan_subagent_fit import build_subagent_fit, recommended_agents_for_fit, subagent_fit_to_dict
    from run_history_penalty import apply_run_history_penalty
    import planner_text_utils as planner_text
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.plan_subagent_fit import build_subagent_fit, recommended_agents_for_fit, subagent_fit_to_dict
    from scripts.run_history_penalty import apply_run_history_penalty
    from scripts import planner_text_utils as planner_text


WORK_TYPE_DESCRIPTIONS = planner_text.WORK_TYPE_DESCRIPTIONS
WORK_TYPE_KEYWORDS = planner_text.WORK_TYPE_KEYWORDS
WORK_TYPE_PRIORITY = planner_text.WORK_TYPE_PRIORITY
STOP_WORDS = planner_text.STOP_WORDS
campaign_goal_matches = planner_text.campaign_goal_matches
classify_work_type = planner_text.classify_work_type
meaningful_tokens = planner_text.meaningful_tokens
normalize_goal_token = planner_text.normalize_goal_token
parse_campaign_goal = planner_text.parse_campaign_goal
parse_campaign_queue = planner_text.parse_campaign_queue


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pick the next Selfdex autopilot task.")
    add_root_argument(parser, help_text="Repository root to scan.")
    add_format_argument(parser, default="markdown", help_text="Output format.")
    return parser.parse_args()


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
            "question": "Should Codex native subagents be used?",
            "answer": "Use official subagents when exploration, docs, implementation, or review can be split into independent agent threads.",
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


def normalized_cluster_key(candidate: Candidate) -> str:
    tokens = [
        token.lower()
        for token in "".join(char if char.isalnum() else " " for char in candidate.title).split()
        if len(token) > 2
    ]
    return f"{candidate.source}:{'-'.join(tokens[:5]) or 'untitled'}"


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

    all_candidates = apply_run_history_penalty(all_candidates, root)
    ranked = sorted(
        all_candidates,
        key=lambda item: (
            -item.priority_score,
            item.source,
            item.title,
        ),
    )
    selected = ranked[0] if ranked else None
    cluster_counts: dict[str, int] = {}
    for candidate in ranked:
        key = normalized_cluster_key(candidate)
        cluster_counts[key] = cluster_counts.get(key, 0) + 1

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_next_task_plan",
        "candidate_count": len(ranked),
        "campaign_goal": campaign_goal,
        "campaign_queue_candidate_count": len(campaign_candidates),
        "errors": errors,
        "selected": candidate_to_dict(selected, campaign_goal, cluster_counts) if selected else None,
        "top_candidates": [candidate_to_dict(item, campaign_goal, cluster_counts) for item in ranked[:5]],
        "recommended_agents": recommend_agents(selected),
    }


def candidate_to_dict(
    candidate: Candidate | None,
    campaign_goal: str = "",
    cluster_counts: dict[str, int] | None = None,
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
    cluster_key = normalized_cluster_key(candidate)
    cluster_size = (cluster_counts or {}).get(cluster_key, 1)
    payload["cluster"] = {
        "key": cluster_key,
        "size": cluster_size,
        "is_duplicate_family": cluster_size > 1,
    }
    return payload


def recommend_agents(candidate: Candidate | None) -> dict[str, Any]:
    fit = build_subagent_fit(candidate)
    fit_payload = subagent_fit_to_dict(fit)
    selected_agents = recommended_agents_for_fit(fit, candidate)
    if candidate is None:
        return {
            "agent_runtime": "codex_native_subagents",
            "subagent_use": "main_only",
            "selected_agents": selected_agents,
            "reason": "No candidate was produced.",
            "write_boundaries": ["main: no candidate to implement"],
            "subagent_fit": fit_payload,
        }

    if candidate.decision != "pick":
        guarded_agents = [agent for agent in selected_agents if agent != "worker"]
        for role in ("explorer", "reviewer"):
            if role not in guarded_agents:
                guarded_agents.append(role)
        return {
            "agent_runtime": "codex_native_subagents",
            "subagent_use": "main_plus_readonly_if_needed",
            "selected_agents": guarded_agents,
            "reason": "Candidate needs clarification or guarded handling before implementation.",
            "write_boundaries": ["main: clarify contract before assigning worker subagents"],
            "subagent_fit": fit_payload,
        }

    if fit.subagent_value == "main_only":
        return {
            "agent_runtime": "codex_native_subagents",
            "subagent_use": "main_only",
            "selected_agents": selected_agents,
            "reason": (
                f"{fit.task_size_class} task with {fit.coordination_cost} coordination cost and "
                f"{fit.parallel_or_specialist_gain} subagent gain; main agent is the simpler owner."
            ),
            "write_boundaries": ["main: implement and verify the selected bounded change"],
            "subagent_fit": fit_payload,
        }

    if fit.subagent_value == "use_subagents":
        return {
            "agent_runtime": "codex_native_subagents",
            "subagent_use": "use_subagents_after_contract_freeze",
            "selected_agents": selected_agents,
            "reason": (
                "Large or separable candidate with independent write boundaries and verification paths "
                "for official Codex explorer, worker, and reviewer agent threads after the contract is frozen."
            ),
            "write_boundaries": [
                "main: own state, campaign state, runs/, integration, and commit gate",
                "explorer: read-only evidence and boundary mapping",
                "worker: own one disjoint write boundary",
                "reviewer: read-only contract and regression review",
            ],
            "subagent_fit": fit_payload,
        }

    return {
        "agent_runtime": "codex_native_subagents",
        "subagent_use": "use_readonly_subagents_first",
        "selected_agents": selected_agents,
        "reason": (
            "Candidate is large or verification-sensitive, but write collision risk means worker subagents "
            "should wait until boundaries are proven disjoint."
        ),
        "write_boundaries": [
            "main: freeze contract, own shared state, and integrate",
            "explorer: read-only slice and write-boundary discovery",
            "reviewer: read-only verification and regression review",
        ],
        "subagent_fit": fit_payload,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    selected = payload.get("selected")
    agents = payload.get("recommended_agents") or {}
    subagent_fit = agents.get("subagent_fit") or {}
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
                f"- agent_runtime: `{agents.get('agent_runtime')}`",
                f"- subagent_use: `{agents.get('subagent_use')}`",
                f"- selected_agents: `{'; '.join(agents.get('selected_agents') or [])}`",
                f"- reason: {agents.get('reason')}",
                "",
                "## Subagent Fit",
                "",
                f"- task_size_class: `{subagent_fit.get('task_size_class')}`",
                f"- estimated_write_boundary_count: `{subagent_fit.get('estimated_write_boundary_count')}`",
                f"- write_collision_risk: `{subagent_fit.get('write_collision_risk')}`",
                f"- coordination_cost: `{subagent_fit.get('coordination_cost')}`",
                f"- parallel_or_specialist_gain: `{subagent_fit.get('parallel_or_specialist_gain')}`",
                f"- verification_independence: `{subagent_fit.get('verification_independence')}`",
                f"- subagent_value: `{subagent_fit.get('subagent_value')}`",
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

        lines.extend(["", "## Write Boundaries", ""])
        for item in agents.get("write_boundaries", []):
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
