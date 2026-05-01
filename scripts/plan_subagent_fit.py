"""Codex-native subagent fit heuristics for Selfdex task planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class SubagentFit:
    task_size_class: str
    estimated_write_boundary_count: int
    write_collision_risk: str
    coordination_cost: str
    parallel_or_specialist_gain: str
    verification_independence: str
    subagent_value: str


class CandidateLike(Protocol):
    source: str
    work_type: str
    title: str
    source_signals: dict[str, Any]


CAMPAIGN_QUEUE_SOURCE = "campaign_queue"
DOCS_RESEARCH_KEYWORDS = (
    "official docs",
    "api",
    "sdk",
    "mcp",
    "chatgpt apps",
    "openai",
    "gpt",
    "model",
    "subagent",
    "multiagentv2",
)
DOCS_RESEARCH_SIGNAL_KEYS = {
    "requires_official_docs",
    "official_docs_required",
    "docs_research_required",
    "external_docs_dependency",
    "api_behavior_uncertain",
}


def coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def normalize_path_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def contains_truthy_docs_signal(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "required", "needed"}


def iter_signal_text(value: Any) -> list[str]:
    if isinstance(value, dict):
        texts: list[str] = []
        for key, child in value.items():
            texts.append(str(key))
            texts.extend(iter_signal_text(child))
        return texts
    if isinstance(value, (list, tuple, set)):
        texts = []
        for child in value:
            texts.extend(iter_signal_text(child))
        return texts
    if value is None:
        return []
    return [str(value)]


def needs_docs_researcher(candidate: CandidateLike) -> bool:
    signals = candidate.source_signals
    for key in DOCS_RESEARCH_SIGNAL_KEYS:
        if key in signals and contains_truthy_docs_signal(signals.get(key)):
            return True

    haystack = " ".join([candidate.title, candidate.work_type, *iter_signal_text(signals)]).lower()
    return any(keyword in haystack for keyword in DOCS_RESEARCH_KEYWORDS)


def append_unique(values: list[str], value: str) -> list[str]:
    if value not in values:
        values.append(value)
    return values


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
        if any(keyword in title for keyword in ("concurrent", "multi", "subagent", "agent", "registry")):
            return "large"
        if candidate.work_type in {"capability", "automation"}:
            return "medium"
        return "small"

    if candidate.work_type in {"capability", "automation"}:
        return "medium"
    return "small"


def estimate_write_boundary_count(candidate: CandidateLike, task_size_class: str) -> int:
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


def assess_collision_risk(candidate: CandidateLike, task_size_class: str, boundary_count: int) -> str:
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
    if task_size_class == "large" and boundary_count <= 1:
        return "high"
    if task_size_class == "large":
        return "medium"
    return "low"


def assess_coordination_cost(task_size_class: str) -> str:
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


def assess_parallel_or_specialist_gain(
    task_size_class: str,
    boundary_count: int,
    collision_risk: str,
    verification_independence: str,
) -> str:
    if task_size_class in {"tiny", "small"}:
        return "low"
    if boundary_count >= 2 and collision_risk in {"low", "medium"} and verification_independence in {"medium", "high"}:
        return "high"
    if task_size_class == "large":
        return "medium"
    if verification_independence == "high":
        return "medium"
    return "low"


def assess_subagent_value(
    task_size_class: str,
    collision_risk: str,
    coordination_cost: str,
    gain: str,
) -> str:
    if task_size_class in {"tiny", "small"} and coordination_cost == "high":
        return "main_only"
    if gain == "high" and collision_risk != "high":
        return "use_subagents"
    if task_size_class == "large" and gain in {"medium", "high"}:
        return "use_readonly_subagents_first"
    return "main_only"


def recommended_agents_for_fit(fit: SubagentFit, candidate: CandidateLike | None) -> list[str]:
    if candidate is None:
        return ["main"]
    wants_docs_research = needs_docs_researcher(candidate)
    if fit.subagent_value == "use_subagents":
        agents = ["main", "explorer", "worker", "reviewer"]
        return append_unique(agents, "docs_researcher") if wants_docs_research else agents
    if fit.subagent_value == "use_readonly_subagents_first":
        agents = ["main", "explorer", "reviewer"]
        return append_unique(agents, "docs_researcher") if wants_docs_research else agents
    if wants_docs_research:
        return ["main", "docs_researcher"]
    return ["main"]


def build_subagent_fit(candidate: CandidateLike | None) -> SubagentFit:
    if candidate is None:
        return SubagentFit(
            task_size_class="none",
            estimated_write_boundary_count=0,
            write_collision_risk="none",
            coordination_cost="none",
            parallel_or_specialist_gain="none",
            verification_independence="none",
            subagent_value="main_only",
        )

    task_size_class = classify_task_size(candidate)
    boundary_count = estimate_write_boundary_count(candidate, task_size_class)
    collision_risk = assess_collision_risk(candidate, task_size_class, boundary_count)
    coordination_cost = assess_coordination_cost(task_size_class)
    verification_independence = assess_verification_independence(candidate, task_size_class)
    gain = assess_parallel_or_specialist_gain(
        task_size_class,
        boundary_count,
        collision_risk,
        verification_independence,
    )
    subagent_value = assess_subagent_value(
        task_size_class,
        collision_risk,
        coordination_cost,
        gain,
    )
    return SubagentFit(
        task_size_class=task_size_class,
        estimated_write_boundary_count=boundary_count,
        write_collision_risk=collision_risk,
        coordination_cost=coordination_cost,
        parallel_or_specialist_gain=gain,
        verification_independence=verification_independence,
        subagent_value=subagent_value,
    )


def subagent_fit_to_dict(fit: SubagentFit) -> dict[str, Any]:
    return {
        "task_size_class": fit.task_size_class,
        "estimated_write_boundary_count": fit.estimated_write_boundary_count,
        "write_collision_risk": fit.write_collision_risk,
        "coordination_cost": fit.coordination_cost,
        "parallel_or_specialist_gain": fit.parallel_or_specialist_gain,
        "verification_independence": fit.verification_independence,
        "subagent_value": fit.subagent_value,
    }
