"""Shared run-history demotion helpers for Selfdex candidate planners."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, TypeVar


RUN_HISTORY_PENALTY = 8.0
FAILED_STATUS_MARKERS = (
    "status: `failed`",
    "status: `blocked`",
    "status: `stopped`",
)

CandidateT = TypeVar("CandidateT")


def failed_run_titles(root: Path, project_id: str = "selfdex") -> set[str]:
    project_runs = root / "runs" / project_id
    if not project_runs.exists():
        return set()

    titles: set[str] = set()
    for path in project_runs.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lowered = text.lower()
        if not any(status in lowered for status in FAILED_STATUS_MARKERS):
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- title:"):
                titles.add(stripped.split(":", 1)[1].strip().strip("`"))
    return titles


def apply_run_history_penalty(
    candidates: list[CandidateT],
    root: Path | None,
    project_id: str = "selfdex",
    *,
    penalty: float = RUN_HISTORY_PENALTY,
) -> list[CandidateT]:
    if root is None:
        return candidates

    failed_titles = failed_run_titles(root, project_id)
    if not failed_titles:
        return candidates

    adjusted: list[CandidateT] = []
    for candidate in candidates:
        title = str(getattr(candidate, "title", ""))
        if title not in failed_titles:
            adjusted.append(candidate)
            continue

        raw_signals = getattr(candidate, "source_signals", {})
        signals: dict[str, Any] = dict(raw_signals) if isinstance(raw_signals, dict) else {}
        signals["run_history"] = {
            "previous_failed_or_blocked": True,
            "score_adjustment": -penalty,
        }
        priority_score = float(getattr(candidate, "priority_score", 0))
        adjusted.append(
            replace(
                candidate,
                priority_score=round(max(priority_score - penalty, 0), 2),
                source_signals=signals,
            )
        )
    return adjusted
