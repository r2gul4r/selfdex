#!/usr/bin/env python3
"""Check Selfdex docs for drift from generated-report files."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CORE_PATHS = (
    "AGENTS.md",
    "AUTOPILOT.md",
    "CAMPAIGN_STATE.md",
    "STATE.md",
    "PROJECT_REGISTRY.md",
    "docs/SELFDEX_FINAL_GOAL.md",
    "runs/",
)

QUICK_START_REPORT_COMMANDS = (
    "scripts/plan_next_task.py",
    "scripts/check_campaign_budget.py",
    "scripts/check_doc_drift.py",
    "scripts/collect_repo_metrics.py",
    "scripts/extract_test_gap_candidates.py",
)


@dataclass(frozen=True)
class DriftFinding:
    finding_id: str
    severity: str
    path: str
    summary: str

    def to_dict(self) -> dict[str, str]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "path": self.path,
            "summary": self.summary,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Selfdex documentation drift.")
    parser.add_argument("--root", default=".", help="Selfdex repository root.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args(argv)


def extract_markdown_section(text: str, heading: str) -> str:
    lines: list[str] = []
    in_section = False
    heading_level = 0
    heading_pattern = re.compile(r"^(#+)\s+(.+?)\s*$")

    for line in text.splitlines():
        match = heading_pattern.match(line)
        if match:
            level = len(match.group(1))
            name = match.group(2).strip().lower()
            if in_section and level <= heading_level:
                break
            if name == heading.lower():
                in_section = True
                heading_level = level
                continue
        if in_section:
            lines.append(line)
    return "\n".join(lines)


def documented_code_paths(text: str) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    inline_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for value in re.findall(r"`([^`\n]+)`", inline_text):
        if not looks_like_path_or_pattern(value):
            continue
        normalized = value.replace("\\", "/")
        if normalized not in seen:
            seen.add(normalized)
            paths.append(normalized)
    return paths


def looks_like_path_or_pattern(value: str) -> bool:
    if not value or " " in value:
        return False
    normalized = value.replace("\\", "/")
    if "/" in normalized:
        return True
    if "*" in normalized:
        return True
    return bool(re.search(r"\.[A-Za-z0-9*]{1,12}$", normalized))


def is_documented(path: str, documented_paths: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    for documented in documented_paths:
        if normalized == documented:
            return True
        if "*" in documented and fnmatch.fnmatch(normalized, documented):
            return True
        if documented.endswith("/") and normalized.startswith(documented):
            return True
    return False


def generated_report_scripts(root: Path) -> list[str]:
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in scripts_dir.iterdir()
        if path.is_file() and path.suffix == ".py"
    )


def existing_core_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for value in CORE_PATHS:
        path = root / value
        if value.endswith("/"):
            if path.is_dir():
                paths.append(value)
        elif path.exists():
            paths.append(value)
    return paths


def find_doc_drift(root: Path) -> tuple[list[DriftFinding], dict[str, Any]]:
    readme_path = root / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    documented_paths = documented_code_paths(readme_text)
    quick_start = extract_markdown_section(readme_text, "Quick Start")
    core_paths = existing_core_paths(root)
    report_scripts = generated_report_scripts(root)

    findings: list[DriftFinding] = []
    for path in core_paths:
        if not is_documented(path, documented_paths):
            findings.append(
                DriftFinding(
                    finding_id="undocumented-core-path",
                    severity="medium",
                    path=path,
                    summary=f"README.md does not document required core path `{path}`.",
                )
            )

    for path in report_scripts:
        if not is_documented(path, documented_paths):
            findings.append(
                DriftFinding(
                    finding_id="undocumented-generated-report-script",
                    severity="high",
                    path=path,
                    summary=f"README.md does not document generated-report script `{path}`.",
                )
            )

    for command in QUICK_START_REPORT_COMMANDS:
        if command in report_scripts and command not in quick_start:
            findings.append(
                DriftFinding(
                    finding_id="missing-quick-start-report-command",
                    severity="low",
                    path=command,
                    summary=f"README.md Quick Start does not include `{command}`.",
                )
            )

    metadata = {
        "readme_path": str(readme_path),
        "documented_paths": documented_paths,
        "core_paths": core_paths,
        "generated_report_scripts": report_scripts,
        "quick_start_report_commands": [
            command for command in QUICK_START_REPORT_COMMANDS if command in report_scripts
        ],
    }
    return findings, metadata


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings, metadata = find_doc_drift(root)
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_doc_drift_check",
        "root": str(root),
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
        "findings": [finding.to_dict() for finding in findings],
        **metadata,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Doc Drift Check",
        "",
        f"- status: `{payload['status']}`",
        f"- finding_count: `{payload['finding_count']}`",
        f"- generated_report_script_count: `{len(payload['generated_report_scripts'])}`",
        "",
        "## Generated Report Scripts",
        "",
    ]
    for path in payload["generated_report_scripts"]:
        lines.append(f"- `{path}`")
    if not payload["generated_report_scripts"]:
        lines.append("- none")

    lines.extend(["", "## Findings", ""])
    for finding in payload["findings"]:
        lines.append(
            f"- `{finding['finding_id']}` {finding['path']}: {finding['summary']}"
        )
    if not payload["findings"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        payload = build_payload(root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(payload))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
