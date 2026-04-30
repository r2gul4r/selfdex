from __future__ import annotations

from pathlib import Path
from typing import Any


GOAL_AREAS_TEXT = (
    "- ??μ냼媛 ?먭린 遺議깊븳 肄붾뱶 ?덉쭏怨?湲곕뒫 怨듬갚???ㅼ뒪濡?"
    "李얘퀬, 媛쒖꽑?덉쓣 ?쒖븞쨌援ы쁽쨌寃利앺븳??n"
)


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_external_registry(
    root: Path,
    external: Path,
    *,
    project_id: str = "external_one",
    write_policy: str = "read-only",
    verification: str = "read-only candidate generation",
) -> None:
    write_multi_external_registry(
        root,
        {project_id: external},
        write_policy=write_policy,
        verification=verification,
    )


def write_multi_external_registry(
    root: Path,
    projects: dict[str, Path],
    *,
    write_policy: str = "read-only",
    verification: str = "read-only candidate generation",
) -> None:
    rows = [
        "| selfdex | . | harness | selfdex-local writes only | python -m unittest |",
    ]
    for project_id, path in projects.items():
        rows.append(f"| {project_id} | {path} | fixture | {write_policy} | {verification} |")
    write_file(
        root,
        "PROJECT_REGISTRY.md",
        "# Project Registry\n\n"
        "## Registered Projects\n\n"
        "| project_id | path | role | write_policy | verification |\n"
        "| :-- | :-- | :-- | :-- | :-- |\n"
        + "\n".join(rows)
        + "\n",
    )


def write_goal_cycle_fixture(root: Path) -> None:
    write_file(
        root,
        "CAMPAIGN_STATE.md",
        "# Campaign State\n\n## Campaign\n\n- goal: `Build a harness that can detect, plan, verify, and record work.`\n",
    )
    write_file(root, "docs/GOAL_COMPARISON_AREAS.md", GOAL_AREAS_TEXT)
    write_file(root, "Makefile", "test: test-installers\n\tpython -m unittest discover -s tests\n")


def planner_candidate(
    *,
    source: str = "refactor",
    title: str = "split candidate extraction helpers",
    rationale: list[str] | None = None,
    suggested_checks: list[str] | None = None,
    work_type: str | None = None,
    decision: str | None = None,
    priority_score: float | None = None,
    risk: str | None = None,
) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "source": source,
        "title": title,
        "rationale": list(rationale or ["large file with duplicated logic"]),
        "suggested_checks": list(suggested_checks or ["python -m compileall -q scripts"]),
    }
    optional_values = {
        "work_type": work_type,
        "decision": decision,
        "priority_score": priority_score,
        "risk": risk,
    }
    for key, value in optional_values.items():
        if value is not None:
            candidate[key] = value
    return candidate


def planner_payload(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_next_task_plan",
        "top_candidates": candidates,
    }


def external_snapshot_payload(projects: list[tuple[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_external_candidate_snapshot",
        "projects": [
            {
                "project_id": project_id,
                "top_candidates": candidates,
            }
            for project_id, candidates in projects
        ],
    }
