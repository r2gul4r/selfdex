"""Orchestration-fit heuristics for Selfdex task planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class OrchestrationFit:
    task_size_class: str
    estimated_write_set_count: int
    shared_file_collision_risk: str
    handoff_cost: str
    parallel_gain: str
    verification_independence: str
    orchestration_value: str


class CandidateLike(Protocol):
    source: str
    work_type: str
    title: str
    source_signals: dict[str, Any]


CAMPAIGN_QUEUE_SOURCE = "campaign_queue"


def coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def normalize_path_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def classify_task_size(candidate: CandidateLike) -> str:
    signals = candidate.source_signals
    title = candidate.title.lower()

    if candidate.source == "test_gap":
        severity = str(signals.get("severity") or "").lower()
        return "medium" if severity == "high" else "small"

    if candidate.source == "refactor":
        signal_source = str(signals.get("candidate_source") or "")
        if signal_source == "complexity_hotspot":
            code_lines = coerce_int(signals.get("code_lines"))
            cyclomatic = coerce_int(signals.get("cyclomatic_estimate"))
            if code_lines >= 600 or cyclomatic >= 100:
                return "large"
            if code_lines >= 300 or cyclomatic >= 50:
                return "medium"
            return "small"
        if signal_source == "duplicate_block":
            paths = normalize_path_list(signals.get("paths"))
            normalized_lines = coerce_int(signals.get("normalized_line_count"))
            occurrence_count = coerce_int(signals.get("occurrence_count"))
            if len(paths) >= 3 and (normalized_lines >= 25 or occurrence_count >= 3):
                return "large"
            if normalized_lines >= 18 or occurrence_count >= 3:
                return "medium"
            return "small"
        if ".py" in title and ("responsibility" in title or "책임" in title):
            return "large"
        if "duplicate" in title or "중복" in title:
            return "small"
        return "medium"

    if candidate.source == CAMPAIGN_QUEUE_SOURCE:
        if any(keyword in title for keyword in ("concurrent", "multi", "orchestration", "registry")):
            return "large"
        if candidate.work_type in {"capability", "automation"}:
            return "medium"
        return "small"

    if candidate.work_type in {"capability", "automation"}:
        return "medium"
    return "small"


def estimate_write_set_count(candidate: CandidateLike, task_size_class: str) -> int:
    signals = candidate.source_signals
    if candidate.source == "test_gap":
        return 2
    if candidate.source == "refactor":
        signal_source = str(signals.get("candidate_source") or "")
        if signal_source == "duplicate_block":
            paths = normalize_path_list(signals.get("paths"))
            return max(1, min(len(set(paths)), 4))
        if signal_source == "complexity_hotspot":
            return 2 if task_size_class == "large" else 1
    if task_size_class == "large":
        return 2
    return 1


def assess_collision_risk(candidate: CandidateLike, task_size_class: str, write_set_count: int) -> str:
    signals = candidate.source_signals
    if candidate.source == "refactor":
        signal_source = str(signals.get("candidate_source") or "")
        if signal_source == "complexity_hotspot":
            return "high"
        if signal_source == "duplicate_block":
            paths = normalize_path_list(signals.get("paths"))
            return "low" if len(set(paths)) >= 2 else "high"
    if candidate.source == "test_gap":
        return "low"
    if task_size_class == "large" and write_set_count <= 1:
        return "high"
    if task_size_class == "large":
        return "medium"
    return "low"


def assess_handoff_cost(task_size_class: str) -> str:
    if task_size_class in {"tiny", "small"}:
        return "high"
    if task_size_class == "medium":
        return "medium"
    return "medium"


def assess_verification_independence(candidate: CandidateLike, task_size_class: str) -> str:
    signals = candidate.source_signals
    if candidate.source == "test_gap":
        return "high"
    if candidate.source == "refactor":
        if str(signals.get("candidate_source") or "") == "duplicate_block":
            paths = normalize_path_list(signals.get("paths"))
            return "high" if len(set(paths)) >= 2 else "medium"
        if str(signals.get("candidate_source") or "") == "complexity_hotspot":
            return "medium"
    if task_size_class == "large":
        return "medium"
    return "low"


def assess_parallel_gain(
    task_size_class: str,
    write_set_count: int,
    collision_risk: str,
    verification_independence: str,
) -> str:
    if task_size_class in {"tiny", "small"}:
        return "low"
    if write_set_count >= 2 and collision_risk in {"low", "medium"} and verification_independence in {"medium", "high"}:
        return "high"
    if task_size_class == "large":
        return "medium"
    if verification_independence == "high":
        return "medium"
    return "low"


def assess_orchestration_value(
    task_size_class: str,
    collision_risk: str,
    handoff_cost: str,
    parallel_gain: str,
) -> str:
    if task_size_class in {"tiny", "small"} and handoff_cost == "high":
        return "low"
    if parallel_gain == "high" and collision_risk != "high":
        return "high"
    if task_size_class == "large" and parallel_gain in {"medium", "high"}:
        return "medium"
    return "low"


def build_orchestration_fit(candidate: CandidateLike | None) -> OrchestrationFit:
    if candidate is None:
        return OrchestrationFit(
            task_size_class="none",
            estimated_write_set_count=0,
            shared_file_collision_risk="none",
            handoff_cost="none",
            parallel_gain="none",
            verification_independence="none",
            orchestration_value="low",
        )

    task_size_class = classify_task_size(candidate)
    write_set_count = estimate_write_set_count(candidate, task_size_class)
    collision_risk = assess_collision_risk(candidate, task_size_class, write_set_count)
    handoff_cost = assess_handoff_cost(task_size_class)
    verification_independence = assess_verification_independence(candidate, task_size_class)
    parallel_gain = assess_parallel_gain(
        task_size_class,
        write_set_count,
        collision_risk,
        verification_independence,
    )
    orchestration_value = assess_orchestration_value(
        task_size_class,
        collision_risk,
        handoff_cost,
        parallel_gain,
    )
    return OrchestrationFit(
        task_size_class=task_size_class,
        estimated_write_set_count=write_set_count,
        shared_file_collision_risk=collision_risk,
        handoff_cost=handoff_cost,
        parallel_gain=parallel_gain,
        verification_independence=verification_independence,
        orchestration_value=orchestration_value,
    )


def orchestration_fit_to_dict(fit: OrchestrationFit) -> dict[str, Any]:
    return {
        "task_size_class": fit.task_size_class,
        "estimated_write_set_count": fit.estimated_write_set_count,
        "shared_file_collision_risk": fit.shared_file_collision_risk,
        "handoff_cost": fit.handoff_cost,
        "parallel_gain": fit.parallel_gain,
        "verification_independence": fit.verification_independence,
        "orchestration_value": fit.orchestration_value,
    }
