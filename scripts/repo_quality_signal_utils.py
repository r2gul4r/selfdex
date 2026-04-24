"""Repo metric quality-signal scoring helpers."""

from __future__ import annotations

from typing import Any


QUALITY_SIGNAL_PROFILE_VERSION = 1
PRIORITY_SCORE_MAX = 48

REPO_METRIC_CAPS = {
    "code_lines": 400,
    "bytes": 20000,
    "max_line_length": 120,
    "max_indent_level": 6,
    "cyclomatic_estimate": 25,
    "decision_points": 40,
    "function_like_blocks": 20,
    "group_count": 3,
    "duplicated_line_instances": 30,
    "max_duplicate_block_lines": 10,
    "commit_count": 8,
    "commits_per_30_days": 4,
    "author_count": 3,
}

REPO_SIGNAL_AXIS_WEIGHTS = {
    "size_pressure": {
        "code_lines": 0.45,
        "bytes": 0.2,
        "max_line_length": 0.2,
        "max_indent_level": 0.15,
    },
    "complexity_pressure": {
        "cyclomatic_estimate": 0.55,
        "decision_points": 0.3,
        "function_like_blocks": 0.15,
    },
    "duplication_pressure": {
        "duplicated_line_instances": 0.5,
        "group_count": 0.3,
        "max_duplicate_block_lines": 0.2,
    },
    "change_pressure": {
        "commit_count": 0.4,
        "commits_per_30_days": 0.4,
        "author_count": 0.2,
    },
}

REPO_SIGNAL_WEIGHTS = {
    "size_pressure": 0.15,
    "complexity_pressure": 0.35,
    "duplication_pressure": 0.3,
    "change_pressure": 0.2,
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_text(item) for item in value if item is not None)
    return str(value)


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def round_score(value: float) -> float:
    return round(value, 4)


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def repo_metric_observed_maxima(files: list[dict[str, Any]]) -> dict[str, float]:
    maxima = {key: 0.0 for key in REPO_METRIC_CAPS}
    for item in files:
        module_size = item.get("module_size", {}) if isinstance(item.get("module_size"), dict) else {}
        complexity = item.get("complexity", {}) if isinstance(item.get("complexity"), dict) else {}
        duplication = item.get("duplication", {}) if isinstance(item.get("duplication"), dict) else {}
        change_frequency = (
            item.get("change_frequency", {}) if isinstance(item.get("change_frequency"), dict) else {}
        )

        maxima["code_lines"] = max(maxima["code_lines"], float(_int_or_none(module_size.get("code_lines")) or 0))
        maxima["bytes"] = max(maxima["bytes"], float(_int_or_none(module_size.get("bytes")) or 0))
        maxima["max_line_length"] = max(
            maxima["max_line_length"],
            float(_int_or_none(module_size.get("max_line_length")) or 0),
        )
        maxima["max_indent_level"] = max(
            maxima["max_indent_level"],
            float(_int_or_none(complexity.get("max_indent_level")) or 0),
        )
        maxima["cyclomatic_estimate"] = max(
            maxima["cyclomatic_estimate"],
            float(_int_or_none(complexity.get("cyclomatic_estimate")) or 0),
        )
        maxima["decision_points"] = max(
            maxima["decision_points"],
            float(_int_or_none(complexity.get("decision_points")) or 0),
        )
        maxima["function_like_blocks"] = max(
            maxima["function_like_blocks"],
            float(_int_or_none(complexity.get("function_like_blocks")) or 0),
        )
        maxima["group_count"] = max(
            maxima["group_count"],
            float(_int_or_none(duplication.get("group_count")) or 0),
        )
        maxima["duplicated_line_instances"] = max(
            maxima["duplicated_line_instances"],
            float(_int_or_none(duplication.get("duplicated_line_instances")) or 0),
        )
        maxima["max_duplicate_block_lines"] = max(
            maxima["max_duplicate_block_lines"],
            float(_int_or_none(duplication.get("max_duplicate_block_lines")) or 0),
        )
        maxima["commit_count"] = max(
            maxima["commit_count"],
            float(_int_or_none(change_frequency.get("commit_count")) or 0),
        )
        maxima["commits_per_30_days"] = max(
            maxima["commits_per_30_days"],
            float(_float_or_none(change_frequency.get("commits_per_30_days")) or 0.0),
        )
        maxima["author_count"] = max(
            maxima["author_count"],
            float(_int_or_none(change_frequency.get("author_count")) or 0),
        )
    return maxima


def normalize_repo_metric(value: float, observed_max: float, cap: float) -> float:
    if value <= 0:
        return 0.0
    relative_component = value / observed_max if observed_max > 0 else 0.0
    cap_component = min(value / cap, 1.0) if cap > 0 else 0.0
    return round_score(clamp_score((relative_component + cap_component) / 2.0))


def build_repo_metric_inputs(item: dict[str, Any]) -> dict[str, float]:
    module_size = item.get("module_size", {}) if isinstance(item.get("module_size"), dict) else {}
    complexity = item.get("complexity", {}) if isinstance(item.get("complexity"), dict) else {}
    duplication = item.get("duplication", {}) if isinstance(item.get("duplication"), dict) else {}
    change_frequency = (
        item.get("change_frequency", {}) if isinstance(item.get("change_frequency"), dict) else {}
    )
    commit_count = float(_int_or_none(change_frequency.get("commit_count")) or 0)
    commits_per_30_days = float(_float_or_none(change_frequency.get("commits_per_30_days")) or 0.0)
    if commit_count < 2:
        commits_per_30_days = 0.0

    return {
        "code_lines": float(_int_or_none(module_size.get("code_lines")) or 0),
        "bytes": float(_int_or_none(module_size.get("bytes")) or 0),
        "max_line_length": float(_int_or_none(module_size.get("max_line_length")) or 0),
        "max_indent_level": float(_int_or_none(complexity.get("max_indent_level")) or 0),
        "cyclomatic_estimate": float(_int_or_none(complexity.get("cyclomatic_estimate")) or 0),
        "decision_points": float(_int_or_none(complexity.get("decision_points")) or 0),
        "function_like_blocks": float(_int_or_none(complexity.get("function_like_blocks")) or 0),
        "group_count": float(_int_or_none(duplication.get("group_count")) or 0),
        "duplicated_line_instances": float(_int_or_none(duplication.get("duplicated_line_instances")) or 0),
        "max_duplicate_block_lines": float(_int_or_none(duplication.get("max_duplicate_block_lines")) or 0),
        "commit_count": commit_count,
        "commits_per_30_days": commits_per_30_days,
        "author_count": float(_int_or_none(change_frequency.get("author_count")) or 0),
    }


def grade_repo_priority(priority_score: float) -> str:
    if priority_score >= 40:
        return "A"
    if priority_score >= 32:
        return "B"
    if priority_score >= 24:
        return "C"
    return "D"


def repo_priority_decision(priority_grade: str) -> str:
    if priority_grade in {"A", "B"}:
        return "prioritize"
    if priority_grade == "C":
        return "monitor"
    return "low"


def summarize_repo_hotspot(entry: dict[str, Any]) -> str:
    top_signal = entry["quality_signal"]["top_signals"][0]
    return (
        f"{entry['path']} | score={entry['quality_signal']['priority_score']:.2f} "
        f"| grade={entry['quality_signal']['priority_grade']} "
        f"| top_signal={top_signal['metric']}"
    )


def build_repo_metric_contribution(
    axis_name: str,
    metric_name: str,
    metric_weight: float,
    metric_inputs: dict[str, float],
    observed_maxima: dict[str, float],
) -> tuple[float, dict[str, Any], dict[str, Any]]:
    raw_value = metric_inputs[metric_name]
    normalized_value = normalize_repo_metric(
        raw_value,
        observed_maxima.get(metric_name, 0.0),
        float(REPO_METRIC_CAPS[metric_name]),
    )
    contribution = normalized_value * metric_weight
    metric_entry = {
        "metric": metric_name,
        "raw": raw_value,
        "normalized": normalized_value,
        "weight": metric_weight,
        "axis_contribution": round_score(contribution),
    }
    signal_entry = {"axis": axis_name, **metric_entry}
    return contribution, metric_entry, signal_entry


def build_repo_axis_breakdown(
    metric_inputs: dict[str, float], observed_maxima: dict[str, float]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    axis_breakdown: dict[str, dict[str, Any]] = {}
    signal_contributions: list[dict[str, Any]] = []

    for axis_name, axis_weights in REPO_SIGNAL_AXIS_WEIGHTS.items():
        axis_score = 0.0
        metrics: list[dict[str, Any]] = []
        for metric_name, metric_weight in axis_weights.items():
            contribution, metric_entry, signal_entry = build_repo_metric_contribution(
                axis_name,
                metric_name,
                metric_weight,
                metric_inputs,
                observed_maxima,
            )
            axis_score += contribution
            metrics.append(metric_entry)
            signal_contributions.append(signal_entry)

        axis_breakdown[axis_name] = {
            "weight": REPO_SIGNAL_WEIGHTS[axis_name],
            "score": round_score(axis_score),
            "weighted_contribution": round_score(axis_score * REPO_SIGNAL_WEIGHTS[axis_name]),
            "metrics": metrics,
        }

    return axis_breakdown, signal_contributions


def build_repo_quality_signal(
    path: str,
    axis_breakdown: dict[str, dict[str, Any]],
    signal_contributions: list[dict[str, Any]],
) -> dict[str, Any]:
    weighted_score = sum(
        axis_info["weighted_contribution"] for axis_info in axis_breakdown.values()
    )
    priority_score = round(weighted_score * PRIORITY_SCORE_MAX, 2)
    priority_grade = grade_repo_priority(priority_score)
    top_signals = sorted(
        signal_contributions,
        key=lambda signal: (
            -signal["axis_contribution"],
            -signal["normalized"],
            signal["metric"],
        ),
    )[:3]

    return {
        "profile_version": QUALITY_SIGNAL_PROFILE_VERSION,
        "weighted_score": round_score(weighted_score),
        "priority_score": priority_score,
        "priority_grade": priority_grade,
        "priority_decision": repo_priority_decision(priority_grade),
        "axis_breakdown": axis_breakdown,
        "top_signals": top_signals,
        "summary": summarize_repo_hotspot(
            {
                "path": path,
                "quality_signal": {
                    "priority_score": priority_score,
                    "priority_grade": priority_grade,
                    "top_signals": top_signals or [{"metric": "none"}],
                },
            }
        ),
    }


def normalize_repo_metric_file(
    item: dict[str, Any], observed_maxima: dict[str, float]
) -> dict[str, Any]:
    metric_inputs = build_repo_metric_inputs(item)
    path = _text(item.get("path"))
    axis_breakdown, signal_contributions = build_repo_axis_breakdown(
        metric_inputs,
        observed_maxima,
    )

    return {
        "path": path,
        "language": _text(item.get("language")),
        "module_size": item.get("module_size"),
        "complexity": item.get("complexity"),
        "duplication": item.get("duplication"),
        "change_frequency": item.get("change_frequency"),
        "quality_signal": build_repo_quality_signal(path, axis_breakdown, signal_contributions),
    }
