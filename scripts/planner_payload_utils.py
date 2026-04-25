"""Shared planner payload helpers for report-oriented scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def planner_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    top_candidates = payload.get("top_candidates")
    if isinstance(top_candidates, list):
        return [candidate for candidate in top_candidates if isinstance(candidate, dict)]

    projects = payload.get("projects")
    if payload.get("analysis_kind") == "selfdex_external_candidate_snapshot" and isinstance(projects, list):
        candidates: list[dict[str, Any]] = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            source_project = str(project.get("project_id") or "").strip()
            for candidate in project.get("top_candidates", []):
                if not isinstance(candidate, dict):
                    continue
                item = dict(candidate)
                item.setdefault("source_project", source_project)
                candidates.append(item)
        return candidates

    selected = payload.get("selected")
    if isinstance(selected, dict):
        return [selected]
    return []
