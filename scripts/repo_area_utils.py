"""Shared repository area labels and classifiers for Selfdex scripts."""

from __future__ import annotations

from pathlib import Path


AREA_LABELS = {
    "installer": "설치기와 작업공간 스캐폴딩",
    "root_tooling": "루트 도구/자동화",
    "documentation": "문서와 평가 기준",
    "agent_profiles": "에이전트 프로필/설정",
    "rules_and_skills": "규칙과 스킬 자산",
    "examples_and_snapshots": "예시와 스냅샷",
    "other": "기타 영역",
}


def classify_area(path: Path) -> str:
    parts = path.parts
    if not parts:
        return "other"
    head = parts[0]
    if head == "installer":
        return "installer"
    if head == "docs":
        return "documentation"
    if head in {"codex_agents", "profiles"}:
        return "agent_profiles"
    if head in {"codex_rules", "codex_skills"}:
        return "rules_and_skills"
    if head == "examples":
        return "examples_and_snapshots"
    if head == "scripts":
        return "root_tooling"
    if len(parts) == 1:
        return "root_tooling"
    return "other"
