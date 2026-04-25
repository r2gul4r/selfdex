#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from argparse_utils import add_format_argument
    from cli_output_utils import write_json_or_markdown
    from normalize_quality_signals import normalize_payload
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.normalize_quality_signals import normalize_payload


SCHEMA_VERSION = 1
DEFAULT_INPUT = "examples/quality_signal_samples.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that normalized quality signals include coverage data."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=f"Quality-tool result payload to normalize. Defaults to {DEFAULT_INPUT}.",
    )
    parser.add_argument(
        "--minimum-tools",
        type=int,
        default=1,
        help="Minimum number of tools that must expose parsed coverage data.",
    )
    add_format_argument(parser)
    return parser.parse_args(argv)


def load_payload(path: str) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def make_issue(code: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
    }


def is_normalized_tool_result_payload(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("analysis_kind") == "tool_results"
        and "coverage_tools" in payload
        and "results" in payload
    )


def coerce_normalized_payload(payload: Any) -> tuple[dict[str, Any], str]:
    if is_normalized_tool_result_payload(payload):
        return payload, "normalized_tool_results"
    return normalize_payload(payload), "raw_tool_results"


def coverage_count(normalized: dict[str, Any], coverage_tools: list[str]) -> int:
    raw_count = normalized.get("coverage_tool_count")
    if raw_count is None:
        return len(coverage_tools)
    try:
        return int(raw_count)
    except (TypeError, ValueError):
        return len(coverage_tools)


def build_payload(raw_payload: Any, *, input_path: str, minimum_tools: int = 1) -> dict[str, Any]:
    normalized, input_payload_kind = coerce_normalized_payload(raw_payload)
    coverage_tools = list(normalized.get("coverage_tools") or [])
    coverage_tool_count = coverage_count(normalized, coverage_tools)
    issues: list[dict[str, str]] = []

    if minimum_tools < 1:
        issues.append(
            make_issue(
                "invalid_minimum_tools",
                "--minimum-tools must be at least 1.",
            )
        )
    elif coverage_tool_count < minimum_tools:
        issues.append(
            make_issue(
                "coverage_signal_missing",
                f"Expected at least {minimum_tools} coverage-producing tool(s), found {coverage_tool_count}.",
            )
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "coverage_signal_check",
        "status": "failed" if issues else "passed",
        "input_path": input_path,
        "input_payload_kind": input_payload_kind,
        "minimum_tools": minimum_tools,
        "normalized_analysis_kind": normalized.get("analysis_kind"),
        "normalized_result_count": normalized.get("result_count", 0),
        "coverage_tool_count": coverage_tool_count,
        "coverage_tools": coverage_tools,
        "issues": issues,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Coverage Signal Check",
        "",
        f"- status: `{payload['status']}`",
        f"- input_path: `{payload['input_path']}`",
        f"- input_payload_kind: `{payload['input_payload_kind']}`",
        f"- minimum_tools: `{payload['minimum_tools']}`",
        f"- coverage_tool_count: `{payload['coverage_tool_count']}`",
        f"- coverage_tools: `{', '.join(payload['coverage_tools']) or 'none'}`",
    ]
    if payload["issues"]:
        lines.append("- issues:")
        for issue in payload["issues"]:
            lines.append(f"  - `{issue['code']}`: {issue['message']}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(
        load_payload(args.input),
        input_path=args.input,
        minimum_tools=args.minimum_tools,
    )
    write_json_or_markdown(payload, args.format, render_markdown)
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
