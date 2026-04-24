#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from repo_quality_signal_utils import (
        PRIORITY_SCORE_MAX,
        REPO_METRIC_CAPS,
        REPO_SIGNAL_AXIS_WEIGHTS,
        REPO_SIGNAL_WEIGHTS,
        normalize_repo_metric_file,
        repo_metric_observed_maxima,
        round_score,
    )
except ModuleNotFoundError:
    from scripts.repo_quality_signal_utils import (
        PRIORITY_SCORE_MAX,
        REPO_METRIC_CAPS,
        REPO_SIGNAL_AXIS_WEIGHTS,
        REPO_SIGNAL_WEIGHTS,
        normalize_repo_metric_file,
        repo_metric_observed_maxima,
        round_score,
    )

try:
    from tool_result_utils import as_text, normalize_result, parse_coverage
except ModuleNotFoundError:
    from scripts.tool_result_utils import as_text, normalize_result, parse_coverage


ANALYSIS_SCHEMA_VERSION = 1
HISTORY_SCHEMA_VERSION = 1
REPO_METRICS_SCHEMA_VERSION = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize quality-tool execution results into one shared JSON schema."
    )
    parser.add_argument(
        "--input",
        help="JSON file containing either a result object or {\"results\": [...]} payload.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the normalized JSON output.",
    )
    parser.add_argument(
        "--history",
        help="JSON file path used to append or query normalized analysis history.",
    )
    parser.add_argument(
        "--store",
        action="store_true",
        help="Append the normalized analysis to the history file given by --history.",
    )
    parser.add_argument(
        "--query",
        choices=("all", "latest", "summary"),
        help="Read stored analysis history from --history instead of normalizing fresh input.",
    )
    args = parser.parse_args()

    if args.store and not args.history:
        parser.error("--store requires --history")
    if args.query and not args.history:
        parser.error("--query requires --history")
    if args.query and args.store:
        parser.error("--query cannot be combined with --store")
    if args.query and args.input:
        parser.error("--query cannot be combined with --input")

    return args


def load_payload(path: str | None) -> Any:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    return json.load(sys.stdin)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_history_store(entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    normalized_entries = entries or []
    latest = normalized_entries[-1] if normalized_entries else None
    latest_entry_id = latest.get("entry_id") if latest else None
    latest_recorded_at = latest.get("recorded_at") if latest else None
    failed_entry_count = sum(
        1 for entry in normalized_entries if entry.get("analysis", {}).get("failed_tool_count", 0) > 0
    )
    warning_entry_count = sum(
        1 for entry in normalized_entries if entry.get("analysis", {}).get("warning_tool_count", 0) > 0
    )

    analysis_kind_occurrences: dict[str, int] = {}
    tool_occurrences: dict[str, int] = {}
    for entry in normalized_entries:
        analysis_kind = as_text(entry.get("analysis", {}).get("analysis_kind") or "tool_results").strip()
        if analysis_kind:
            analysis_kind_occurrences[analysis_kind] = analysis_kind_occurrences.get(analysis_kind, 0) + 1
        for result in entry.get("analysis", {}).get("results", []) or []:
            tool = as_text(result.get("tool")).strip()
            if not tool:
                continue
            tool_occurrences[tool] = tool_occurrences.get(tool, 0) + 1

    return {
        "history_schema_version": HISTORY_SCHEMA_VERSION,
        "analysis_schema_version": ANALYSIS_SCHEMA_VERSION,
        "entry_count": len(normalized_entries),
        "failed_entry_count": failed_entry_count,
        "warning_entry_count": warning_entry_count,
        "latest_entry_id": latest_entry_id,
        "latest_recorded_at": latest_recorded_at,
        "analysis_kind_occurrences": analysis_kind_occurrences,
        "tool_occurrences": tool_occurrences,
        "entries": normalized_entries,
    }


def load_history(path: str) -> dict[str, Any]:
    history_path = Path(path)
    if not history_path.exists():
        return build_history_store()
    if history_path.stat().st_size == 0:
        return build_history_store()

    with history_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise ValueError("History file must be a JSON object with an 'entries' array.")

    if payload.get("history_schema_version") != HISTORY_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported history schema version: {payload.get('history_schema_version')!r}"
        )

    entries = [entry for entry in payload.get("entries", []) if isinstance(entry, dict)]
    return build_history_store(entries)


def write_json_atomic(path: str, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix=f".{output_path.name}.", dir=str(output_path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, output_path)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def build_history_entry(normalized: dict[str, Any], input_path: str | None, sequence: int) -> dict[str, Any]:
    return {
        "entry_id": f"analysis-{sequence:04d}",
        "recorded_at": utc_timestamp(),
        "source": {
            "input_kind": "file" if input_path else "stdin",
            "input_path": input_path,
        },
        "analysis": normalized,
    }


def append_history(path: str, normalized: dict[str, Any], input_path: str | None) -> dict[str, Any]:
    history = load_history(path)
    entries = list(history.get("entries", []))
    entry = build_history_entry(normalized, input_path, len(entries) + 1)
    entries.append(entry)
    stored = build_history_store(entries)
    write_json_atomic(path, stored)
    return entry


def query_history(path: str, mode: str) -> dict[str, Any]:
    history = load_history(path)
    if mode == "all":
        return history
    if mode == "latest":
        latest = history.get("entries", [])[-1] if history.get("entries") else None
        return {
            "history_schema_version": history["history_schema_version"],
            "analysis_schema_version": history["analysis_schema_version"],
            "entry_count": history["entry_count"],
            "latest": latest,
        }
    return {
        "history_schema_version": history["history_schema_version"],
        "analysis_schema_version": history["analysis_schema_version"],
        "entry_count": history["entry_count"],
        "failed_entry_count": history["failed_entry_count"],
        "warning_entry_count": history["warning_entry_count"],
        "latest_entry_id": history["latest_entry_id"],
        "latest_recorded_at": history["latest_recorded_at"],
        "analysis_kind_occurrences": history["analysis_kind_occurrences"],
        "tool_occurrences": history["tool_occurrences"],
    }


def detect_repo_metrics_payload(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("schema_version") == REPO_METRICS_SCHEMA_VERSION
        and isinstance(payload.get("files"), list)
        and isinstance(payload.get("summary"), dict)
    )


def normalize_repo_metrics_payload(payload: dict[str, Any]) -> dict[str, Any]:
    files = [item for item in payload.get("files", []) if isinstance(item, dict)]
    observed_maxima = repo_metric_observed_maxima(files)
    normalized_files = [normalize_repo_metric_file(item, observed_maxima) for item in files]
    ranked_files = sorted(
        normalized_files,
        key=lambda item: (
            -item["quality_signal"]["priority_score"],
            -item["quality_signal"]["weighted_score"],
            item["path"],
        ),
    )

    for index, item in enumerate(ranked_files, start=1):
        item["quality_signal"]["priority_rank"] = index

    grade_distribution = {grade: 0 for grade in ("A", "B", "C", "D")}
    decision_distribution = {"prioritize": 0, "monitor": 0, "low": 0}
    total_weighted_score = 0.0
    for item in ranked_files:
        grade_distribution[item["quality_signal"]["priority_grade"]] += 1
        decision_distribution[item["quality_signal"]["priority_decision"]] += 1
        total_weighted_score += item["quality_signal"]["weighted_score"]

    hotspot_count = min(5, len(ranked_files))
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "analysis_kind": "repo_metrics",
        "source_schema_version": payload.get("schema_version"),
        "result_count": len(ranked_files),
        "priority_count": len(ranked_files),
        "weights": {
            "priority_score_max": PRIORITY_SCORE_MAX,
            "axis_weights": REPO_SIGNAL_WEIGHTS,
            "metric_caps": REPO_METRIC_CAPS,
            "axis_metric_weights": REPO_SIGNAL_AXIS_WEIGHTS,
        },
        "summary": {
            "file_count": len(ranked_files),
            "average_weighted_score": round_score(
                total_weighted_score / len(ranked_files) if ranked_files else 0.0
            ),
            "max_priority_score": max(
                (item["quality_signal"]["priority_score"] for item in ranked_files),
                default=0.0,
            ),
            "priority_grade_distribution": grade_distribution,
            "priority_decision_distribution": decision_distribution,
        },
        "hotspots": [
            {
                "path": item["path"],
                "language": item["language"],
                "priority_rank": item["quality_signal"]["priority_rank"],
                "priority_score": item["quality_signal"]["priority_score"],
                "priority_grade": item["quality_signal"]["priority_grade"],
                "priority_decision": item["quality_signal"]["priority_decision"],
                "top_signal": item["quality_signal"]["top_signals"][0]["metric"],
                "summary": item["quality_signal"]["summary"],
            }
            for item in ranked_files[:hotspot_count]
        ],
        "results": ranked_files,
    }


def normalize_payload(payload: Any) -> dict[str, Any]:
    if detect_repo_metrics_payload(payload):
        return normalize_repo_metrics_payload(payload)

    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        items = payload["results"]
    elif isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = [payload]
    else:
        raise ValueError("Input must be a JSON object, a list, or an object with a 'results' array.")

    normalized = [normalize_result(item) for item in items if isinstance(item, dict)]
    failed_tools = [item["tool"] for item in normalized if item["status"] == "failed"]
    warning_tools = [item["tool"] for item in normalized if item["status"] == "warning"]
    coverage_tools = [
        item["tool"]
        for item in normalized
        if item.get("coverage") and item["coverage"].get("percent") is not None
    ]

    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "analysis_kind": "tool_results",
        "result_count": len(normalized),
        "failed_tool_count": len(failed_tools),
        "warning_tool_count": len(warning_tools),
        "coverage_tool_count": len(coverage_tools),
        "failed_tools": failed_tools,
        "warning_tools": warning_tools,
        "coverage_tools": coverage_tools,
        "results": normalized,
    }


def main() -> int:
    args = parse_args()
    if args.query:
        output = query_history(args.history, args.query)
    else:
        payload = load_payload(args.input)
        normalized = normalize_payload(payload)
        output = append_history(args.history, normalized, args.input) if args.store else normalized

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
