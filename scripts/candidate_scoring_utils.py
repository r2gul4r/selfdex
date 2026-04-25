"""Shared candidate scoring primitives for Selfdex extractor scripts."""

from __future__ import annotations


COMMON_AXIS_POINTS = {
    "goal_alignment": {"pass": 3, "borderline": 1, "fail": 0},
    "gap_relevance": {"high": 3, "medium": 2, "low": 0},
    "safety": {"safe": 3, "guarded": 2, "risky": 0},
    "reversibility": {"strong": 3, "partial": 2, "weak": 0},
    "structural_impact": {"low": 3, "medium": 2, "high": 0},
    "leverage": {"high": 3, "medium": 2, "low": 1},
}


def compute_common_score(common_axes: dict[str, str]) -> int:
    return sum(COMMON_AXIS_POINTS[axis_name][axis_value] for axis_name, axis_value in common_axes.items())


def determine_common_axis_decision(common_axes: dict[str, str]) -> tuple[str, str] | None:
    if common_axes["goal_alignment"] == "fail":
        return "reject", "hold"
    if common_axes["gap_relevance"] == "low":
        return "defer", "hold"
    if common_axes["safety"] == "risky":
        return "defer", "hold"
    if common_axes["reversibility"] == "weak":
        return "defer", "hold"
    if common_axes["structural_impact"] == "high":
        return "needs_approval", "hold"
    return None


def grade_priority(priority_score: int) -> str:
    if priority_score >= 40:
        return "A"
    if priority_score >= 32:
        return "B"
    if priority_score >= 24:
        return "C"
    return "D"
