"""Small-feature scoring helpers for feature-gap candidate extraction."""

from __future__ import annotations

from typing import Any

try:
    from candidate_scoring_utils import compute_common_score, determine_common_axis_decision, grade_priority
except ModuleNotFoundError:
    from scripts.candidate_scoring_utils import compute_common_score, determine_common_axis_decision, grade_priority

try:
    from repo_area_utils import AREA_LABELS
except ModuleNotFoundError:
    from scripts.repo_area_utils import AREA_LABELS


GOAL_ALIGNMENT_AREA_SCORES = {
    "installer": 3,
    "root_tooling": 3,
    "documentation": 2,
    "agent_profiles": 3,
    "rules_and_skills": 3,
    "examples_and_snapshots": 1,
    "other": 2,
}


def _unique_sorted(items: list[str]) -> list[str]:
    return sorted({item for item in items if item})


def score_to_common_goal_alignment(score: int) -> str:
    if score >= 2:
        return "pass"
    if score == 1:
        return "borderline"
    return "fail"


def summarize_user_value(feature_group: dict[str, Any]) -> tuple[int, str]:
    assessment = feature_group["gap_assessment"]
    tests = feature_group["evidence_bundle"]["tests"]
    signal_counts = feature_group["signal_counts"]
    explicit_signals = sum(
        signal_counts.get(signal_id, 0)
        for signal_id in ("missing_handler", "missing_api_integration", "unwired_ui", "not_implemented")
    )
    if assessment["decision"] == "confirmed_gap" or (explicit_signals > 0 and tests["missing_tests"]):
        return 3, "현재 확인된 기능 공백을 직접 메워 실제 사용 흐름과 회귀 방어를 바로 개선함"
    if assessment["decision"] == "likely_gap":
        return 2, "반복 마찰을 줄이는 보강 후보지만 핵심 공백을 닫는 증거는 한 단계 더 필요함"
    return 1, "보조적 개선 가치는 있으나 현재 목표 달성에는 간접 효과가 더 큼"


def summarize_implementation_cost(feature_group: dict[str, Any]) -> tuple[int, str]:
    related_paths = feature_group["related_paths"]
    code_locations = feature_group["evidence_bundle"]["code_locations"]
    if len(related_paths) <= 1 and len(code_locations) <= 2:
        return 3, "기존 구조 안에서 한두 지점만 수정하면 되는 작은 변경 범위"
    if len(related_paths) <= 3:
        return 2, "현재 구조를 유지한 채 인접 파일 몇 곳을 함께 손보면 되는 범위"
    if len(related_paths) <= 5:
        return 1, "영향 경로가 넓어 작은 기능치고 검증 부담이 큰 편"
    return 0, "구조 변경 승인 없이는 안전하게 넣기 어려운 범위"


def summarize_small_feature_goal_alignment(area_id: str, feature_group: dict[str, Any]) -> tuple[int, str]:
    base_score = GOAL_ALIGNMENT_AREA_SCORES.get(area_id, 1)
    assessment = feature_group["gap_assessment"]
    if assessment["decision"] == "confirmed_gap" and base_score < 3:
        base_score += 1
    score = min(base_score, 3)
    if score == 3:
        return 3, "저장소의 자가 탐지·제안·검증 루프를 직접 강화하는 영역이라 목표 정합성이 높음"
    if score == 2:
        return 2, "프로젝트 목표 흐름을 보조하지만 핵심 루프 강화 효과는 한 단계 약함"
    if score == 1:
        return 1, "프로젝트 목표와 충돌은 없지만 직접 기여도는 낮음"
    return 0, "현재 프로젝트 방향성과 직접 연결되지 않음"


def summarize_ripple_effect(feature_group: dict[str, Any]) -> tuple[int, str]:
    call_flow = feature_group["evidence_bundle"]["call_flow"]
    tests = feature_group["evidence_bundle"]["tests"]
    related_paths = feature_group["related_paths"]
    if tests["missing_tests"] and call_flow["status"] in {"defined_only", "unresolved"}:
        return 3, "기능 보강과 동시에 다음 사이클의 검증 신뢰도와 추적성이 함께 좋아짐"
    if tests["missing_tests"] or call_flow["status"] in {"defined_only", "unresolved"}:
        return 2, "인접한 검증 또는 호출 흐름에 긍정 효과가 있지만 범위는 제한적임"
    if len(related_paths) <= 2:
        return 1, "현재 공백 해결 중심이라 연쇄 이득은 크지 않음"
    return 0, "연쇄 이득보다 회귀 통제 비용이 더 커질 수 있음"


def assess_common_axes(area_id: str, feature_group: dict[str, Any], implementation_cost: int) -> dict[str, str]:
    tests = feature_group["evidence_bundle"]["tests"]
    call_flow = feature_group["evidence_bundle"]["call_flow"]
    gap_assessment = feature_group["gap_assessment"]
    goal_alignment_score, _ = summarize_small_feature_goal_alignment(area_id, feature_group)

    if gap_assessment["decision"] in {"confirmed_gap", "likely_gap"}:
        gap_relevance = "high"
    elif gap_assessment["score"] > 0:
        gap_relevance = "medium"
    else:
        gap_relevance = "low"

    if implementation_cost == 0:
        structural_impact = "high"
    elif len(feature_group["related_paths"]) > 3:
        structural_impact = "medium"
    else:
        structural_impact = "low"

    if implementation_cost == 0:
        safety = "risky"
    elif tests["missing_tests"] or call_flow["status"] in {"defined_only", "unresolved"}:
        safety = "guarded"
    else:
        safety = "safe"

    if implementation_cost >= 2:
        reversibility = "strong"
    elif implementation_cost == 1:
        reversibility = "partial"
    else:
        reversibility = "weak"

    ripple_effect, _ = summarize_ripple_effect(feature_group)
    if ripple_effect >= 3 or area_id in {"root_tooling", "rules_and_skills", "agent_profiles"}:
        leverage = "high"
    elif ripple_effect >= 2:
        leverage = "medium"
    else:
        leverage = "low"

    return {
        "goal_alignment": score_to_common_goal_alignment(goal_alignment_score),
        "gap_relevance": gap_relevance,
        "safety": safety,
        "reversibility": reversibility,
        "structural_impact": structural_impact,
        "leverage": leverage,
    }


def determine_small_feature_decision(
    common_axes: dict[str, str],
    value: int,
    implementation_cost: int,
    goal_alignment_score: int,
    ripple_effect: int,
    priority_score: int,
) -> tuple[str, str]:
    common_decision = determine_common_axis_decision(common_axes)
    if common_decision is not None:
        return common_decision
    if goal_alignment_score < 2:
        return "reject", "hold"
    if value < 2:
        return "defer", "hold"
    if implementation_cost == 0:
        return "needs_approval", "hold"
    if ripple_effect == 0:
        return "defer", "hold"
    return "pick", grade_priority(priority_score)


def build_implementation_scope(feature_group: dict[str, Any], implementation_cost_summary: str) -> list[str]:
    scope = [implementation_cost_summary]
    code_locations = feature_group["evidence_bundle"]["code_locations"]
    call_flow = feature_group["evidence_bundle"]["call_flow"]
    tests = feature_group["evidence_bundle"]["tests"]
    if code_locations:
        anchors = _unique_sorted(
            [
                f"{item['path']}:{item['line']}"
                for item in code_locations
                if item.get("path") and item.get("line")
            ]
        )
        scope.append(f"우선 수정 후보 코드 위치: {', '.join(anchors[:4])}")
    if call_flow["definition"]:
        definition = call_flow["definition"]
        scope.append(f"주요 정의 지점: {definition['path']}:{definition['line']}")
    if tests["matched_test_files"]:
        scope.append(
            "연관 테스트 확인 범위: "
            + ", ".join(item["path"] for item in tests["matched_test_files"][:4])
        )
    elif tests["missing_tests"]:
        scope.append("관련 테스트가 없어 기능 보강과 함께 회귀 방어 경로 확인이 필요함")
    return scope


def build_selection_rationale(
    feature_group: dict[str, Any],
    common_axes: dict[str, str],
    user_value_summary: str,
    goal_alignment_summary: str,
    ripple_effect_summary: str,
) -> list[str]:
    rationale = [user_value_summary, goal_alignment_summary, ripple_effect_summary]
    rationale.extend(feature_group["gap_assessment"]["reasons"])
    rationale.append(
        "공통 축 판정: " + ", ".join(f"{key}={value}" for key, value in common_axes.items())
    )
    return rationale


def build_small_feature_candidate(area_id: str, feature_group: dict[str, Any]) -> dict[str, Any]:
    value, user_value_summary = summarize_user_value(feature_group)
    implementation_cost, implementation_cost_summary = summarize_implementation_cost(feature_group)
    goal_alignment_score, goal_alignment_summary = summarize_small_feature_goal_alignment(
        area_id, feature_group
    )
    ripple_effect, ripple_effect_summary = summarize_ripple_effect(feature_group)
    specific_score = value + implementation_cost + goal_alignment_score + ripple_effect
    common_axes = assess_common_axes(area_id, feature_group, implementation_cost)
    common_score = compute_common_score(common_axes)
    priority_score = (common_score * 2) + specific_score
    decision, priority_grade = determine_small_feature_decision(
        common_axes,
        value,
        implementation_cost,
        goal_alignment_score,
        ripple_effect,
        priority_score,
    )

    return {
        "proposal_id": f"small_feature:{area_id}:{feature_group['feature_key']}",
        "candidate_kind": "small_feature",
        "title": feature_group["title"],
        "linked_gap": "feature_gap",
        "linked_feature_key": feature_group["feature_key"],
        "functional_area": area_id,
        "functional_area_label": AREA_LABELS.get(area_id, area_id),
        "user_value": user_value_summary,
        "implementation_scope": build_implementation_scope(feature_group, implementation_cost_summary),
        "selection_rationale": build_selection_rationale(
            feature_group,
            common_axes,
            user_value_summary,
            goal_alignment_summary,
            ripple_effect_summary,
        ),
        "common_axes": common_axes,
        "small_feature_rubric": {
            "value": value,
            "implementation_cost": implementation_cost,
            "goal_alignment": goal_alignment_score,
            "ripple_effect": ripple_effect,
            "specific_score": specific_score,
        },
        "common_score": common_score,
        "specific_score": specific_score,
        "priority_score": priority_score,
        "priority_grade": priority_grade,
        "decision": decision,
        "source_feature_group": {
            "feature_key": feature_group["feature_key"],
            "candidate_count": feature_group["candidate_count"],
            "signal_counts": feature_group["signal_counts"],
            "related_paths": feature_group["related_paths"],
            "gap_assessment": feature_group["gap_assessment"],
        },
    }


def build_small_feature_candidates(areas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for area in areas:
        area_id = area["area_id"]
        for feature_group in area["feature_groups"]:
            candidate = build_small_feature_candidate(area_id, feature_group)
            if candidate["common_axes"]["goal_alignment"] != "pass":
                continue
            candidates.append(candidate)

    return sorted(
        candidates,
        key=lambda item: (
            {"pick": 0, "defer": 1, "needs_approval": 2, "reject": 3}.get(item["decision"], 4),
            -item["priority_score"],
            -item["small_feature_rubric"]["goal_alignment"],
            -item["small_feature_rubric"]["value"],
            item["title"],
        ),
    )
