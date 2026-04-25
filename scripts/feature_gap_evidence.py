"""Evidence helpers for feature-gap candidate extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from feature_file_records import FileRecord, normalize_excerpt
except ModuleNotFoundError:
    from scripts.feature_file_records import FileRecord, normalize_excerpt

try:
    from repo_area_utils import classify_area
except ModuleNotFoundError:
    from scripts.repo_area_utils import classify_area


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
STOPWORDS = {
    "todo",
    "fixme",
    "stub",
    "stubbed",
    "placeholder",
    "implemented",
    "implementation",
    "missing",
    "handler",
    "callback",
    "screen",
    "button",
    "dialog",
    "view",
    "page",
    "start",
    "resume",
    "submit",
    "click",
    "api",
    "client",
    "endpoint",
    "fetch",
    "request",
    "integration",
    "with",
    "from",
    "this",
    "that",
    "none",
    "soon",
}
DETECTOR_SIGNAL_LITERAL_WORDS = (
    "to" + "do",
    "fix" + "me",
    "st" + "ub",
    "st" + "ubbed",
    "place" + "holder",
)


def extract_tokens(*values: str) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for value in values:
        for raw in TOKEN_PATTERN.findall(value):
            token = raw.lower()
            if token in STOPWORDS:
                continue
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def summarize_signals(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        signal_id = str(candidate.get("signal_id"))
        counts[signal_id] = counts.get(signal_id, 0) + 1
    return dict(sorted(counts.items()))


def unique_sorted(items: list[str]) -> list[str]:
    return sorted({item for item in items if item})


def summarize_related_paths(paths: list[str], limit: int = 8) -> list[str]:
    return unique_sorted(paths)[:limit]


def is_detector_self_reference(line: str) -> bool:
    stripped = line.strip()
    literal = stripped.rstrip(",").strip("\"'")
    if literal in DETECTOR_SIGNAL_LITERAL_WORDS:
        return True
    if "signal_counts.get(" in stripped:
        return True
    if "reasons.append(" in stripped:
        return True
    if '"signal_id":' in stripped:
        return True
    return False


def find_related_records(
    repo_index: dict[str, Any], feature_key: str, area_id: str, candidate_paths: list[str]
) -> list[FileRecord]:
    tokens = extract_tokens(feature_key, *[Path(path).stem for path in candidate_paths])
    path_set = set(candidate_paths)
    related: list[FileRecord] = []
    for record in repo_index["records"]:
        same_area = classify_area(Path(record.relative_path)) == area_id
        if record.relative_path in path_set:
            related.append(record)
            continue
        if not same_area:
            continue
        haystack = f"{record.relative_path}\n{record.content}".lower()
        if any(token in haystack for token in tokens):
            related.append(record)
    return related


def build_call_flow(
    repo_index: dict[str, Any], symbol_name: str | None, related_records: list[FileRecord]
) -> dict[str, Any]:
    if not symbol_name:
        return {
            "entrypoint": None,
            "definition": None,
            "callers": [],
            "status": "unknown",
            "summary": "심볼을 특정하지 못해 호출 흐름을 추론하지 못함",
        }

    symbol_pattern = re.compile(rf"\b{re.escape(symbol_name)}\b")
    definition: dict[str, Any] | None = None
    callers: list[dict[str, Any]] = []

    for record in repo_index["records"]:
        for definition_candidate in record.definitions:
            if definition_candidate.name != symbol_name:
                continue
            definition = {
                "path": record.relative_path,
                "line": definition_candidate.line,
                "symbol_kind": definition_candidate.symbol_kind,
            }
            break
        if definition:
            break

    for record in related_records:
        for index, line in enumerate(record.lines, start=1):
            if not symbol_pattern.search(line):
                continue
            if definition and record.relative_path == definition["path"] and index == definition["line"]:
                continue
            callers.append(
                {
                    "path": record.relative_path,
                    "line": index,
                    "excerpt": normalize_excerpt(line),
                }
            )
            if len(callers) >= 6:
                break
        if len(callers) >= 6:
            break

    status = "linked" if definition and callers else "defined_only" if definition else "unresolved"
    if status == "linked":
        summary = "정의와 참조가 둘 다 보여 실제 호출 흐름을 따라갈 수 있음"
    elif status == "defined_only":
        summary = "정의는 보이지만 관련 호출 흔적이 약해 배선 누락 가능성이 남음"
    else:
        summary = "정의나 호출 흐름을 안정적으로 찾지 못해 추가 확인이 필요함"

    return {
        "entrypoint": callers[0] if callers else None,
        "definition": definition,
        "callers": callers,
        "status": status,
        "summary": summary,
    }


def build_test_evidence(
    repo_index: dict[str, Any], feature_key: str, symbol_name: str | None, candidate_paths: list[str]
) -> dict[str, Any]:
    search_terms = unique_sorted(
        extract_tokens(feature_key, symbol_name or "", *[Path(path).stem for path in candidate_paths])
    )
    matching_tests: list[dict[str, Any]] = []

    for record in repo_index["test_records"]:
        haystack = f"{record.relative_path}\n{record.content}".lower()
        if not search_terms:
            continue
        if not any(term in haystack for term in search_terms):
            continue
        matching_tests.append(
            {
                "path": record.relative_path,
                "matched_terms": [term for term in search_terms if term in haystack][:5],
            }
        )

    missing_tests = len(matching_tests) == 0
    summary = (
        "연결된 테스트 파일을 찾지 못해 기능 공백 회귀 방어가 약함"
        if missing_tests
        else "관련 테스트 흔적이 있어 기능 공백 여부를 추가 검증할 수 있음"
    )
    return {
        "search_terms": search_terms,
        "matched_test_files": matching_tests,
        "missing_tests": missing_tests,
        "summary": summary,
    }


def assess_gap(
    candidates: list[dict[str, Any]], call_flow: dict[str, Any], test_evidence: dict[str, Any]
) -> dict[str, Any]:
    signal_counts = summarize_signals(candidates)
    explicit_signals = sum(
        signal_counts.get(signal_id, 0)
        for signal_id in ("missing_handler", "missing_api_integration", "unwired_ui", "not_implemented")
    )
    weak_signals = sum(signal_counts.get(signal_id, 0) for signal_id in ("todo", "placeholder", "stub"))

    reasons: list[str] = []
    score = 0

    if explicit_signals > 0:
        score += 2
        reasons.append("명시적인 미구현/누락 신호가 확인됨")
    if weak_signals > 1:
        score += 1
        reasons.append("같은 기능 후보에 반복 신호가 누적됨")
    if call_flow.get("status") in {"defined_only", "unresolved"}:
        score += 1
        reasons.append("호출 흐름이 끝까지 연결되지 않음")
    if test_evidence.get("missing_tests"):
        score += 1
        reasons.append("관련 테스트 흔적이 없음")

    if score >= 4:
        decision = "confirmed_gap"
        confidence = "high"
        summary = "증거가 겹쳐 보여 실제 기능 공백으로 우선 취급해도 되는 후보"
    elif score >= 2:
        decision = "likely_gap"
        confidence = "medium"
        summary = "기능 공백 가능성이 높지만 호출 흐름/테스트 확인이 더 있으면 좋음"
    else:
        decision = "needs_review"
        confidence = "low"
        summary = "신호는 있으나 실제 공백으로 단정하기엔 근거가 약함"

    return {
        "decision": decision,
        "confidence": confidence,
        "summary": summary,
        "reasons": reasons,
        "score": score,
    }
