"""Strategic opportunity construction for project direction snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from candidate_scoring_utils import grade_priority
    from project_direction_evidence import evidence_objects, paths_matching, rel_path
except ModuleNotFoundError:
    from scripts.candidate_scoring_utils import grade_priority
    from scripts.project_direction_evidence import evidence_objects, paths_matching, rel_path


def score_dimensions(
    *,
    strategic_fit: int,
    user_value: int,
    novelty: int,
    feasibility: int,
    local_verifiability: int,
    reversibility: int,
    evidence_strength: int,
) -> dict[str, int]:
    return {
        "strategic_fit": strategic_fit,
        "user_value": user_value,
        "novelty": novelty,
        "feasibility": feasibility,
        "local_verifiability": local_verifiability,
        "reversibility": reversibility,
        "evidence_strength": evidence_strength,
    }


def opportunity(
    *,
    opportunity_id: str,
    title: str,
    rationale: list[str],
    evidence_paths: list[str],
    evidence: list[dict[str, str]] | None = None,
    suggested_first_step: str,
    suggested_checks: list[str],
    dimensions: dict[str, int],
    risk: str = "guarded",
) -> dict[str, Any]:
    raw_score = sum(dimensions.values())
    priority_score = round(raw_score * 1.35, 2)
    decision = "pick" if priority_score >= 38 and risk in {"low", "guarded", "medium"} else "monitor"
    return {
        "opportunity_id": opportunity_id,
        "title": title,
        "source": "project_direction",
        "work_type": "direction",
        "decision": decision,
        "priority_score": priority_score,
        "priority_grade": grade_priority(int(priority_score)),
        "risk": risk,
        "strategic_dimensions": dimensions,
        "rationale": rationale,
        "evidence_paths": list(dict.fromkeys(evidence_paths))[:5],
        "evidence": evidence
        or evidence_objects(
            list(dict.fromkeys(evidence_paths))[:5],
            signal_text=title,
            confidence="medium",
        ),
        "suggested_first_step": suggested_first_step,
        "suggested_checks": suggested_checks,
    }


def build_opportunities(
    *,
    root: Path,
    files: list[Path],
    purpose: dict[str, Any],
    product_signals: list[dict[str, Any]],
    technical_signals: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
    quote_map: dict[str, str],
    limit: int,
) -> list[dict[str, Any]]:
    signal_labels = {item["label"] for item in product_signals}
    test_available = any(item["label"] == "local_verification_available" for item in constraints)
    check = "python -m unittest discover -s tests" if test_available else "manual local smoke check"
    purpose_paths = list(purpose.get("evidence_paths", []))
    opportunities: list[dict[str, Any]] = []

    if {"interactive_experience", "service_layer"} & signal_labels:
        evidence = paths_matching(files, root, "frontend", "pages", "components", "api", "controller", "route", "backend")
        opportunities.append(
            opportunity(
                opportunity_id="direction:core-user-journey",
                title="Prove and improve the primary user journey",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "A user-facing or service-facing surface exists, so a small vertical-slice improvement can raise product value beyond code hygiene.",
                    "The first step should connect or verify one visible path instead of broadly refactoring.",
                ],
                evidence_paths=evidence or purpose_paths,
                evidence=evidence_objects(
                    evidence or purpose_paths,
                    signal_text="user-facing or service-facing product surface",
                    confidence="medium",
                    quote_map=quote_map,
                ),
                suggested_first_step="Pick one core user journey, document its expected result, and make the smallest code or test change that improves that path.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=5,
                    user_value=5,
                    novelty=4,
                    feasibility=4,
                    local_verifiability=4 if test_available else 3,
                    reversibility=4,
                    evidence_strength=4,
                ),
            )
        )

    if "data_pipeline" in signal_labels:
        evidence = paths_matching(files, root, "collector", "crawler", "ingest", "schema", "migration", ".sql")
        opportunities.append(
            opportunity(
                opportunity_id="direction:data-quality-loop",
                title="Turn data freshness and quality into a product feedback loop",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "Data collection or persistence is visible, so product quality may depend on freshness, coverage, and explainable failures.",
                    "A small observability or validation step can unlock better future features than another local cleanup task.",
                ],
                evidence_paths=evidence or purpose_paths,
                evidence=evidence_objects(
                    evidence or purpose_paths,
                    signal_text="data collection or persistence surface",
                    confidence="medium",
                    quote_map=quote_map,
                ),
                suggested_first_step="Add or tighten one local data-quality check that reports stale, missing, or malformed product data before feature work relies on it.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=5,
                    user_value=5,
                    novelty=4,
                    feasibility=3,
                    local_verifiability=4 if test_available else 3,
                    reversibility=3,
                    evidence_strength=4,
                ),
            )
        )

    if "automation_loop" in signal_labels:
        evidence = paths_matching(files, root, "scripts", "agents.md", "state.md", "runs", "workflow")
        opportunities.append(
            opportunity(
                opportunity_id="direction:autonomous-feedback-loop",
                title="Close one autonomous feedback loop with evidence",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "Automation or agent workflow signals are present, so the next improvement should make the system learn from a completed run.",
                    "This is a project evolution candidate because it improves decision quality, not just local code shape.",
                ],
                evidence_paths=evidence or purpose_paths,
                evidence=evidence_objects(
                    evidence or purpose_paths,
                    signal_text="automation or agent workflow surface",
                    confidence="medium",
                    quote_map=quote_map,
                ),
                suggested_first_step="Record one missing decision or result field that would make the next automated run choose better work.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=5,
                    user_value=4,
                    novelty=5,
                    feasibility=4,
                    local_verifiability=4 if test_available else 3,
                    reversibility=4,
                    evidence_strength=4,
                ),
            )
        )

    if len(purpose_paths) <= 1 or "unknown" in " ".join(purpose.get("summary", "").lower().split()):
        evidence = purpose_paths or [rel_path(root, path) for path in files[:3]]
        opportunities.append(
            opportunity(
                opportunity_id="direction:project-thesis",
                title="Make the project thesis explicit for future work",
                rationale=[
                    "The scanned evidence does not expose a strong project thesis.",
                    "Selfdex needs a clear goal, audience, and current product bet before it can choose ambitious work safely.",
                ],
                evidence_paths=evidence,
                evidence=evidence_objects(
                    evidence,
                    signal_text="project thesis is unclear in scanned docs",
                    confidence="medium",
                    quote_map=quote_map,
                ),
                suggested_first_step="Add or update a short project thesis section that states the target user, current value proposition, and next product bet.",
                suggested_checks=["manual documentation review"],
                dimensions=score_dimensions(
                    strategic_fit=4,
                    user_value=4,
                    novelty=3,
                    feasibility=5,
                    local_verifiability=3,
                    reversibility=5,
                    evidence_strength=3,
                ),
                risk="low",
            )
        )

    if test_available and technical_signals:
        evidence = paths_matching(files, root, "test", "tests", "spec") + purpose_paths
        opportunities.append(
            opportunity(
                opportunity_id="direction:core-flow-check",
                title="Protect the most important project direction with one scenario check",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "There is local verification evidence, so the project can protect a strategic behavior instead of only checking implementation details.",
                ],
                evidence_paths=evidence,
                evidence=evidence_objects(
                    evidence,
                    signal_text="local verification surface can protect project direction",
                    confidence="medium",
                    quote_map=quote_map,
                ),
                suggested_first_step="Add or strengthen one scenario-level check around the behavior that best represents the project value.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=4,
                    user_value=4,
                    novelty=3,
                    feasibility=4,
                    local_verifiability=5,
                    reversibility=4,
                    evidence_strength=4,
                ),
            )
        )

    return sorted(opportunities, key=lambda item: (-item["priority_score"], item["title"]))[: max(limit, 1)]
