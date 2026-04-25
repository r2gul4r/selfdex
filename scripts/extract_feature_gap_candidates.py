#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from argparse_utils import add_format_argument, add_pretty_argument, add_root_argument
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_pretty_argument, add_root_argument

try:
    from candidate_scoring_utils import COMMON_AXIS_POINTS, compute_common_score, grade_priority
except ModuleNotFoundError:
    from scripts.candidate_scoring_utils import COMMON_AXIS_POINTS, compute_common_score, grade_priority

try:
    import feature_file_records as feature_records
    import feature_gap_evidence as gap_evidence
    import feature_small_candidates as small_candidates
except ModuleNotFoundError:
    from scripts import feature_file_records as feature_records
    from scripts import feature_gap_evidence as gap_evidence
    from scripts import feature_small_candidates as small_candidates

try:
    from repo_area_utils import AREA_LABELS, classify_area
except ModuleNotFoundError:
    from scripts.repo_area_utils import AREA_LABELS, classify_area


SCHEMA_VERSION = 3

FileRecord = feature_records.FileRecord
SymbolLocation = feature_records.SymbolLocation
build_file_record = feature_records.build_file_record
build_repo_index = feature_records.build_repo_index
extract_definitions = feature_records.extract_definitions
find_enclosing_symbol = feature_records.find_enclosing_symbol
infer_language = feature_records.infer_language
is_test_file = feature_records.is_test_file
is_text_file = feature_records.is_text_file
iter_repo_files = feature_records.iter_repo_files
normalize_excerpt = feature_records.normalize_excerpt
read_text_lines = feature_records.read_text_lines

STOPWORDS = gap_evidence.STOPWORDS
TOKEN_PATTERN = gap_evidence.TOKEN_PATTERN
assess_gap = gap_evidence.assess_gap
build_call_flow = gap_evidence.build_call_flow
build_test_evidence = gap_evidence.build_test_evidence
extract_tokens = gap_evidence.extract_tokens
find_related_records = gap_evidence.find_related_records
is_detector_self_reference = gap_evidence.is_detector_self_reference
summarize_related_paths = gap_evidence.summarize_related_paths
summarize_signals = gap_evidence.summarize_signals
unique_sorted = gap_evidence.unique_sorted

GOAL_ALIGNMENT_AREA_SCORES = small_candidates.GOAL_ALIGNMENT_AREA_SCORES
assess_common_axes = small_candidates.assess_common_axes
build_implementation_scope = small_candidates.build_implementation_scope
build_selection_rationale = small_candidates.build_selection_rationale
build_small_feature_candidate = small_candidates.build_small_feature_candidate
build_small_feature_candidates = small_candidates.build_small_feature_candidates
determine_small_feature_decision = small_candidates.determine_small_feature_decision
score_to_common_goal_alignment = small_candidates.score_to_common_goal_alignment
summarize_implementation_cost = small_candidates.summarize_implementation_cost
summarize_ripple_effect = small_candidates.summarize_ripple_effect
summarize_small_feature_goal_alignment = small_candidates.summarize_small_feature_goal_alignment
summarize_user_value = small_candidates.summarize_user_value


@dataclass(frozen=True)
class SignalSpec:
    signal_id: str
    gap_type: str
    label: str
    rationale: str
    pattern: re.Pattern[str]


SIGNAL_SPECS = (
    SignalSpec(
        signal_id="missing_handler",
        gap_type="feature_gap",
        label="미구현 핸들러",
        rationale="핸들러/콜백 맥락에서 미구현 신호가 보여 실제 동작 배선이 빠졌을 가능성이 큼",
        pattern=re.compile(
            r"(?i)(handler|callback|submit|click|resume|start|run).*(todo|stub|placeholder|not implemented|미구현)"
        ),
    ),
    SignalSpec(
        signal_id="missing_api_integration",
        gap_type="feature_gap",
        label="누락된 API 연동",
        rationale="API/연동 맥락에서 미구현 신호가 보여 외부 호출 또는 내부 연동이 비어 있을 가능성이 큼",
        pattern=re.compile(
            r"(?i)(api|client|endpoint|fetch|request|integration|연동).*(todo|stub|placeholder|not implemented|미구현|missing)"
        ),
    ),
    SignalSpec(
        signal_id="unwired_ui",
        gap_type="feature_gap",
        label="미연결 UI/화면",
        rationale="UI/화면 맥락에서 미구현 신호가 보여 사용자 흐름이 끝까지 연결되지 않았을 가능성이 큼",
        pattern=re.compile(
            r"(?i)(ui|screen|page|button|dialog|view).*(todo|stub|placeholder|coming soon|not implemented|미구현|미연결)"
        ),
    ),
    SignalSpec(
        signal_id="not_implemented",
        gap_type="feature_gap",
        label="미구현 로직",
        rationale="명시적인 not-implemented 신호가 있어 실제 기능 로직이 빠져 있음",
        pattern=re.compile(r"(?i)(notimplemented(error)?|not implemented|unimplemented|미구현)"),
    ),
    SignalSpec(
        signal_id="stub",
        gap_type="feature_gap",
        label="stub/임시 구현",
        rationale="stub 표시가 있어 실제 기능 구현이 임시 상태에 머물러 있음",
        pattern=re.compile(r"(?i)\bstub(?:bed)?\b"),
    ),
    SignalSpec(
        signal_id="todo",
        gap_type="feature_gap",
        label="TODO/FIXME",
        rationale="TODO/FIXME 주석이 있어 후속 구현 또는 연결 작업이 남아 있음",
        pattern=re.compile(r"(?i)\b(todo|fixme)\b"),
    ),
    SignalSpec(
        signal_id="placeholder",
        gap_type="feature_gap",
        label="placeholder 출력/템플릿",
        rationale="placeholder 문자열이 실제 값 대신 남아 있어 사용 시점에 필요한 기능 채움이 빠져 있음",
        pattern=re.compile(r"(?i)\bplaceholder\b"),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract evidence-backed unfinished feature candidates from repository files."
    )
    add_root_argument(
        parser,
        help_text="Repository root to scan. Defaults to the current directory.",
    )
    add_pretty_argument(parser)
    add_format_argument(parser)
    return parser.parse_args()


def infer_feature_key(candidate: dict[str, Any]) -> str:
    symbol_name = candidate.get("code_location", {}).get("symbol_name")
    if isinstance(symbol_name, str) and symbol_name:
        return symbol_name

    evidence = candidate.get("evidence", {})
    path = str(evidence.get("path", ""))
    excerpt = str(evidence.get("excerpt", ""))
    stem = Path(path).stem
    tokens = extract_tokens(stem, excerpt)
    if tokens:
        return tokens[0]
    return f"{stem or 'feature'}-{evidence.get('line', 'unknown')}"


def build_candidate(
    *,
    root: Path,
    record: FileRecord,
    area_id: str,
    spec: SignalSpec,
    line_number: int,
    line_text: str,
) -> dict[str, Any]:
    start = max(0, line_number - 2)
    end = min(len(record.lines), line_number + 1)
    context = [normalize_excerpt(record.lines[index]) for index in range(start, end)]
    symbol = find_enclosing_symbol(record, line_number)
    code_location = {
        "path": record.relative_path,
        "line": symbol.line if symbol else line_number,
        "symbol_name": symbol.name if symbol else None,
        "symbol_kind": symbol.symbol_kind if symbol else None,
        "anchor": f"{record.relative_path}:{symbol.line if symbol else line_number}",
    }
    title_target = symbol.name if symbol else f"{record.relative_path}:{line_number}"
    return {
        "candidate_id": f"{area_id}:{record.relative_path}:{line_number}:{spec.signal_id}",
        "candidate_kind": spec.gap_type,
        "title": f"{spec.label}: {title_target}",
        "signal_id": spec.signal_id,
        "signal_label": spec.label,
        "feature_key": infer_feature_key(
            {
                "code_location": code_location,
                "evidence": {"path": record.relative_path, "line": line_number, "excerpt": line_text},
            }
        ),
        "functional_area": area_id,
        "functional_area_label": AREA_LABELS.get(area_id, area_id),
        "rationale": spec.rationale,
        "code_location": code_location,
        "evidence": {
            "path": record.relative_path,
            "line": line_number,
            "excerpt": normalize_excerpt(line_text),
            "context": context,
        },
    }


def scan_file(root: Path, record: FileRecord) -> list[dict[str, Any]]:
    if record.is_test_file:
        return []

    area_id = classify_area(Path(record.relative_path))
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    for index, line in enumerate(record.lines, start=1):
        if is_detector_self_reference(line):
            continue
        for spec in SIGNAL_SPECS:
            if not spec.pattern.search(line):
                continue
            dedupe_key = (index, spec.signal_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            candidates.append(
                build_candidate(
                    root=root,
                    record=record,
                    area_id=area_id,
                    spec=spec,
                    line_number=index,
                    line_text=line,
                )
            )
            break
    return candidates


def map_status_label(decision: str) -> str:
    return {
        "confirmed_gap": "확정 공백",
        "likely_gap": "유력 공백",
        "needs_review": "검토 필요",
    }.get(decision, decision)


def impact_score_to_level(score: int) -> tuple[str, str]:
    if score >= 4:
        return ("high", "높음")
    if score >= 2:
        return ("medium", "중간")
    return ("low", "낮음")


def build_status_summary(call_flow: dict[str, Any], test_evidence: dict[str, Any], assessment: dict[str, Any]) -> str:
    parts = [str(assessment.get("summary", "")).strip()]
    call_flow_summary = str(call_flow.get("summary", "")).strip()
    test_summary = str(test_evidence.get("summary", "")).strip()
    if call_flow_summary:
        parts.append(call_flow_summary)
    if test_summary:
        parts.append(test_summary)
    return " / ".join(part for part in parts if part)


def build_impact_summary(area_label: str, assessment: dict[str, Any], candidate_count: int) -> dict[str, str]:
    level_id, level_label = impact_score_to_level(int(assessment.get("score", 0)))
    confidence = str(assessment.get("confidence", "")).strip()
    reasons = [str(reason).strip() for reason in assessment.get("reasons", []) if str(reason).strip()]
    if reasons:
        reason_text = ", ".join(reasons[:2])
    else:
        reason_text = "현재 신호가 약해 영향도는 제한적으로 본다"
    summary = (
        f"{area_label}에서 {candidate_count}개 근거가 같은 공백 후보로 묶여 있고 "
        f"판정 신뢰도는 {confidence or 'unknown'}라서, 이 항목을 메우면 "
        f"해당 영역의 누락 상태 기록과 후속 개선 우선순위 정확도가 {level_label} 수준으로 좋아질 가능성이 있다. "
        f"주요 근거: {reason_text}"
    )
    return {
        "level": level_id,
        "level_label": level_label,
        "summary": summary,
    }


def build_documentation_evidence(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence_rows: list[dict[str, Any]] = []
    for candidate in candidates[:3]:
        evidence = candidate["evidence"]
        evidence_rows.append(
            {
                "path": evidence["path"],
                "line": evidence["line"],
                "excerpt": evidence["excerpt"],
                "signal_label": candidate["signal_label"],
            }
        )
    return evidence_rows


def build_documentation_entry(
    *,
    area_id: str,
    area_label: str,
    feature_key: str,
    candidates: list[dict[str, Any]],
    call_flow: dict[str, Any],
    test_evidence: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    status_label = map_status_label(str(assessment.get("decision", "")))
    evidence_rows = build_documentation_evidence(candidates)
    primary_evidence = evidence_rows[0] if evidence_rows else {}
    impact = build_impact_summary(area_label, assessment, len(candidates))
    return {
        "gap_id": f"{area_id}:{feature_key}",
        "functional_area": area_id,
        "functional_area_label": area_label,
        "title": f"{area_label} / {feature_key}",
        "evidence": {
            "summary": str(candidates[0].get("rationale", "")).strip() if candidates else "",
            "items": evidence_rows,
            "primary_reference": {
                "path": primary_evidence.get("path"),
                "line": primary_evidence.get("line"),
            },
        },
        "current_status": {
            "status": assessment.get("decision"),
            "status_label": status_label,
            "summary": build_status_summary(call_flow, test_evidence, assessment),
        },
        "expected_impact": impact,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Feature Gap Areas",
        "",
        "이 문서는 저장소에서 판별된 기능 공백과 그 근거를 바탕으로 뽑은 작은 기능 후보 목록이다.",
        "각 항목은 근거, 현재 상태, 사용자 가치, 구현 범위, 선정 근거를 함께 남겨 다음 계획 단계의 직접 입력으로 쓴다.",
        "",
        f"- schema_version: `{payload['schema_version']}`",
        f"- scanned_file_count: `{payload['scanned_file_count']}`",
        f"- documented_feature_gap_count: `{payload['documented_feature_gap_count']}`",
        f"- small_feature_candidate_count: `{payload['small_feature_candidate_count']}`",
        "",
    ]

    candidates = payload.get("small_feature_candidates", [])
    if candidates:
        lines.extend(
            [
                "## Small Feature Candidates",
                "",
            ]
        )
        for candidate in candidates:
            lines.extend(
                [
                    f"### {candidate['title']}",
                    "",
                    f"- 결정: `{candidate['decision']}` / 등급 `{candidate['priority_grade']}` / 점수 `{candidate['priority_score']}`",
                    f"- 사용자 가치: {candidate['user_value']}",
                ]
            )
            if candidate.get("implementation_scope"):
                lines.append("- 구현 범위:")
                for item in candidate["implementation_scope"]:
                    lines.append(f"  - {item}")
            if candidate.get("selection_rationale"):
                lines.append("- 선정 근거:")
                for item in candidate["selection_rationale"]:
                    lines.append(f"  - {item}")
            lines.append("")

    for area in payload["areas"]:
        entries = area.get("documented_feature_gaps", [])
        if not entries:
            continue
        lines.extend(
            [
                f"## {area['area_label']}",
                "",
                f"- area_id: `{area['area_id']}`",
                f"- scanned_file_count: `{area['scanned_file_count']}`",
                f"- documented_feature_gap_count: `{len(entries)}`",
                "",
            ]
        )
        for entry in entries:
            evidence_items = entry["evidence"]["items"]
            evidence_summary = entry["evidence"]["summary"]
            primary = evidence_items[0] if evidence_items else None
            primary_ref = (
                f"`{primary['path']}:{primary['line']}`"
                if primary and primary.get("path") and primary.get("line")
                else "`n/a`"
            )
            lines.extend(
                [
                    f"### {entry['title']}",
                    "",
                    f"- 근거: {evidence_summary}",
                    f"- 근거 위치: {primary_ref}",
                    f"- 현재 상태: {entry['current_status']['status_label']} / {entry['current_status']['summary']}",
                    (
                        f"- 예상 영향도: {entry['expected_impact']['level_label']} / "
                        f"{entry['expected_impact']['summary']}"
                    ),
                ]
            )
            if evidence_items:
                lines.append("- 세부 근거:")
                for item in evidence_items:
                    lines.append(
                        f"  - `{item['path']}:{item['line']}` {item['signal_label']} :: {item['excerpt']}"
                    )
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_feature_group(
    *,
    area_id: str,
    feature_key: str,
    candidates: list[dict[str, Any]],
    repo_index: dict[str, Any],
) -> dict[str, Any]:
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            item["evidence"]["path"],
            item["evidence"]["line"],
            item["signal_id"],
        ),
    )
    candidate_paths = [candidate["evidence"]["path"] for candidate in sorted_candidates]
    symbol_name = next(
        (
            str(candidate["code_location"]["symbol_name"])
            for candidate in sorted_candidates
            if candidate.get("code_location", {}).get("symbol_name")
        ),
        None,
    )
    related_records = find_related_records(repo_index, feature_key, area_id, candidate_paths)
    call_flow = build_call_flow(repo_index, symbol_name, related_records)
    test_evidence = build_test_evidence(repo_index, feature_key, symbol_name, candidate_paths)
    assessment = assess_gap(sorted_candidates, call_flow, test_evidence)

    related_paths = summarize_related_paths([record.relative_path for record in related_records])
    code_locations = []
    for candidate in sorted_candidates:
        location = candidate["code_location"]
        code_locations.append(
            {
                "path": location["path"],
                "line": location["line"],
                "symbol_name": location["symbol_name"],
                "symbol_kind": location["symbol_kind"],
            }
        )

    title_source = symbol_name or feature_key
    return {
        "feature_key": feature_key,
        "title": f"{AREA_LABELS.get(area_id, area_id)} / {title_source}",
        "candidate_count": len(sorted_candidates),
        "signal_counts": summarize_signals(sorted_candidates),
        "related_paths": related_paths,
        "evidence_bundle": {
            "related_file_paths": related_paths,
            "code_locations": code_locations,
            "call_flow": call_flow,
            "tests": test_evidence,
        },
        "gap_assessment": assessment,
        "documentation_entry": build_documentation_entry(
            area_id=area_id,
            area_label=AREA_LABELS.get(area_id, area_id),
            feature_key=feature_key,
            candidates=sorted_candidates,
            call_flow=call_flow,
            test_evidence=test_evidence,
            assessment=assessment,
        ),
        "candidates": sorted_candidates,
    }


def build_area_records(files: list[Path], root: Path, repo_index: dict[str, Any]) -> list[dict[str, Any]]:
    by_area: dict[str, dict[str, Any]] = {
        area_id: {
            "area_id": area_id,
            "area_label": label,
            "scanned_files": [],
            "candidates": [],
        }
        for area_id, label in AREA_LABELS.items()
    }

    for record in repo_index["records"]:
        area_id = classify_area(Path(record.relative_path))
        area = by_area.setdefault(
            area_id,
            {
                "area_id": area_id,
                "area_label": AREA_LABELS.get(area_id, area_id),
                "scanned_files": [],
                "candidates": [],
            },
        )
        area["scanned_files"].append(record.relative_path)
        area["candidates"].extend(scan_file(root, record))

    areas: list[dict[str, Any]] = []
    for area_id in sorted(by_area):
        record = by_area[area_id]
        candidates = sorted(
            record["candidates"],
            key=lambda item: (
                item["evidence"]["path"],
                item["evidence"]["line"],
                item["signal_id"],
            ),
        )

        grouped: dict[str, list[dict[str, Any]]] = {}
        for candidate in candidates:
            grouped.setdefault(str(candidate["feature_key"]), []).append(candidate)

        feature_groups = [
            build_feature_group(
                area_id=area_id,
                feature_key=feature_key,
                candidates=grouped_candidates,
                repo_index=repo_index,
            )
            for feature_key, grouped_candidates in sorted(grouped.items())
        ]

        areas.append(
            {
                "area_id": area_id,
                "area_label": record["area_label"],
                "scanned_file_count": len(record["scanned_files"]),
                "candidate_count": len(candidates),
                "feature_group_count": len(feature_groups),
                "documented_feature_gaps": [group["documentation_entry"] for group in feature_groups],
                "small_feature_candidates": [
                    candidate
                    for candidate in (
                        build_small_feature_candidate(area_id, group) for group in feature_groups
                    )
                    if candidate["common_axes"]["goal_alignment"] == "pass"
                ],
                "signal_counts": summarize_signals(candidates),
                "scanned_files": sorted(record["scanned_files"]),
                "feature_groups": feature_groups,
                "candidates": candidates,
            }
        )
    return areas


def extract_feature_gap_candidates(root: Path) -> dict[str, Any]:
    files = iter_repo_files(root, exclude_filename=Path(__file__).name)
    repo_index = build_repo_index(root, files)
    areas = build_area_records(files, root, repo_index)
    all_candidates = [candidate for area in areas for candidate in area["candidates"]]
    all_feature_groups = [group for area in areas for group in area["feature_groups"]]
    all_documented_gaps = [entry for area in areas for entry in area["documented_feature_gaps"]]
    small_feature_candidates = build_small_feature_candidates(areas)
    return {
        "schema_version": SCHEMA_VERSION,
        "repository_root": str(root.resolve()),
        "scanned_file_count": len(files),
        "candidate_count": len(all_candidates),
        "feature_group_count": len(all_feature_groups),
        "documented_feature_gap_count": len(all_documented_gaps),
        "small_feature_candidate_count": len(small_feature_candidates),
        "small_feature_candidates": small_feature_candidates,
        "areas": areas,
    }


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = extract_feature_gap_candidates(root)
    if args.format == "markdown":
        print(render_markdown_report(payload), end="")
        return

    indent = 2 if args.pretty else None
    print(json.dumps(payload, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
