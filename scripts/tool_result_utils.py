"""Tool-result issue and coverage parsing helpers."""

from __future__ import annotations

import re
from typing import Any


FAILURE_WORDS = ("error", "failed", "failure", "fatal", "exception")
WARNING_WORDS = ("warning", "warn", "deprecated", "caution")

MARKDOWNLINT_PATTERN = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+)(?::(?P<column>\d+))?\s+"
    r"(?P<code>MD\d{3}(?:/[^\s]+)?)\s+(?P<message>.+)$"
)
GENERIC_PATH_PATTERN = re.compile(
    r"^(?P<path>[^:\n]+):(?P<line>\d+)(?::(?P<column>\d+))?:\s+(?P<message>.+)$"
)
SHELLCHECK_PATTERN = re.compile(
    r"^In\s+(?P<path>.+?)\s+line\s+(?P<line>\d+):\s*$", re.MULTILINE
)
SHELLCHECK_CODE_PATTERN = re.compile(r"https://www\.shellcheck\.net/wiki/(?P<code>SC\d+)")
PYTEST_WARNING_PATTERN = re.compile(r"(?P<message>.+?)\s+warning[s]?$", re.IGNORECASE)
LINES_COVERAGE_PATTERN = re.compile(
    r"Lines:\s*(?P<percent>\d+(?:\.\d+)?)%\s*\((?P<covered>\d+)/(?P<total>\d+)\)",
    re.IGNORECASE,
)
BRANCHES_COVERAGE_PATTERN = re.compile(
    r"Branches:\s*(?P<percent>\d+(?:\.\d+)?)%\s*\((?P<covered>\d+)/(?P<total>\d+)\)",
    re.IGNORECASE,
)
TOTAL_COVERAGE_PATTERN = re.compile(
    r"^TOTAL\s+(?P<stmts>\d+)\s+(?P<miss>\d+)\s+(?P<percent>\d+(?:\.\d+)?)%\s*$",
    re.IGNORECASE | re.MULTILINE,
)
TABLE_COVERAGE_PATTERN = re.compile(
    r"^All files\s+\|(?P<body>.+?)\|\s*(?P<percent>\d+(?:\.\d+)?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(as_text(item) for item in value if item is not None)
    return str(value)


def coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def coerce_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def normalize_tool_name(result: dict[str, Any]) -> str:
    explicit = as_text(result.get("tool") or result.get("name")).strip().lower()
    if explicit:
        return explicit

    command = as_text(result.get("command")).lower()
    if "markdownlint" in command:
        return "markdownlint"
    if "shellcheck" in command:
        return "shellcheck"
    if "psscriptanalyzer" in command:
        return "psscriptanalyzer"
    if "pytest" in command:
        return "pytest"
    if "coverage" in command:
        return "coverage"
    if "bash -n" in command:
        return "bash-parse"
    if "powershell" in command or "pwsh" in command:
        return "powershell"
    return "unknown"


def stream_text(result: dict[str, Any]) -> str:
    parts = [
        as_text(result.get("stdout")),
        as_text(result.get("stderr")),
        as_text(result.get("output")),
    ]
    return "\n".join(part for part in parts if part).strip()


def infer_severity(message: str, default: str = "warning") -> str:
    lowered = message.lower()
    if any(word in lowered for word in FAILURE_WORDS):
        return "failure"
    if any(word in lowered for word in WARNING_WORDS):
        return "warning"
    return default


def make_issue(
    *,
    severity: str,
    message: str,
    path: str | None = None,
    line: int | None = None,
    column: int | None = None,
    code: str | None = None,
    raw: str | None = None,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "message": message.strip(),
        "path": path,
        "line": line,
        "column": column,
        "code": code,
        "raw": raw.strip() if raw else None,
    }


def parse_structured_issues(result: dict[str, Any]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for issue in result.get("issues", []) or []:
        if not isinstance(issue, dict):
            continue
        severity = infer_severity(as_text(issue.get("severity")), default="warning")
        if as_text(issue.get("severity")).strip().lower() in {"error", "failure", "fatal"}:
            severity = "failure"
        elif as_text(issue.get("severity")).strip().lower() in {"warning", "warn", "information"}:
            severity = "warning"

        path = as_text(issue.get("path") or issue.get("file")) or None
        line = coerce_int(issue.get("line"))
        column = coerce_int(issue.get("column"))
        code = as_text(issue.get("code") or issue.get("rule")) or None
        message = as_text(issue.get("message") or issue.get("text") or issue.get("detail"))
        if not message:
            continue
        parsed.append(
            make_issue(
                severity=severity,
                message=message,
                path=path,
                line=line,
                column=column,
                code=code,
                raw=as_text(issue.get("raw")),
            )
        )
    return parsed


def parse_markdownlint(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = MARKDOWNLINT_PATTERN.match(line.strip())
        if not match:
            continue
        issues.append(
            make_issue(
                severity="failure",
                path=match.group("path"),
                line=coerce_int(match.group("line")),
                column=coerce_int(match.group("column")),
                code=match.group("code"),
                message=match.group("message"),
                raw=line,
            )
        )
    return issues


def parse_shellcheck(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        header = SHELLCHECK_PATTERN.match(lines[index])
        if not header:
            index += 1
            continue
        path = header.group("path")
        line = coerce_int(header.group("line"))
        message = "ShellCheck issue"
        if index + 2 < len(lines):
            caret_line = lines[index + 2].strip()
            marker = re.search(r"\((?:warning|error)\):\s*(?P<message>.+)$", caret_line, re.IGNORECASE)
            if marker:
                message = marker.group("message")
        elif index + 1 < len(lines):
            message = lines[index + 1].strip()
        code = None
        window = "\n".join(lines[index : min(index + 6, len(lines))])
        code_match = SHELLCHECK_CODE_PATTERN.search(window)
        if code_match:
            code = code_match.group("code")
        issues.append(
            make_issue(
                severity="warning",
                path=path,
                line=line,
                code=code,
                message=message,
                raw=window,
            )
        )
        index += 1
    return issues


def parse_generic_path_issues(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = GENERIC_PATH_PATTERN.match(line.strip())
        if not match:
            continue
        message = match.group("message")
        issues.append(
            make_issue(
                severity=infer_severity(message),
                path=match.group("path"),
                line=coerce_int(match.group("line")),
                column=coerce_int(match.group("column")),
                message=message,
                raw=line,
            )
        )
    return issues


def parse_pytest_summary(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for line in text.splitlines():
        lowered = line.lower().strip()
        if not lowered:
            continue
        if " failed" in lowered or lowered.startswith("failed "):
            issues.append(make_issue(severity="failure", message=line.strip(), raw=line))
        elif "warnings summary" in lowered:
            continue
        elif " warning" in lowered:
            warning_match = PYTEST_WARNING_PATTERN.search(line.strip())
            message = warning_match.group("message") if warning_match else line.strip()
            issues.append(make_issue(severity="warning", message=message, raw=line))
    return issues


def dedupe_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for issue in issues:
        key = (
            issue.get("severity"),
            issue.get("path"),
            issue.get("line"),
            issue.get("column"),
            issue.get("code"),
            issue.get("message"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def normalize_explicit_coverage(result: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(result.get("coverage"), dict):
        coverage = result["coverage"].copy()
        percent = coerce_float(coverage.get("percent"))
        if percent is not None:
            coverage["percent"] = percent
        for key in ("lines_covered", "lines_total", "branches_covered", "branches_total"):
            coverage[key] = coerce_int(coverage.get(key))
        coverage["raw"] = coverage.get("raw") or None
        return coverage
    return None


def parse_primary_coverage_values(result: dict[str, Any], text: str) -> dict[str, Any]:
    lines_match = LINES_COVERAGE_PATTERN.search(text)
    total_match = TOTAL_COVERAGE_PATTERN.search(text)
    table_match = TABLE_COVERAGE_PATTERN.search(text)

    percent = None
    lines_covered = None
    lines_total = None
    branches_covered = None
    branches_total = None
    raw = None

    if lines_match:
        percent = coerce_float(lines_match.group("percent"))
        lines_covered = coerce_int(lines_match.group("covered"))
        lines_total = coerce_int(lines_match.group("total"))
        raw = lines_match.group(0)
    elif total_match:
        percent = coerce_float(total_match.group("percent"))
        statements = coerce_int(total_match.group("stmts"))
        missed = coerce_int(total_match.group("miss"))
        if statements is not None and missed is not None:
            lines_total = statements
            lines_covered = max(statements - missed, 0)
        raw = total_match.group(0)
    elif table_match:
        percent = coerce_float(table_match.group("percent"))
        raw = table_match.group(0)
    else:
        percent_hint = coerce_float(result.get("coverage_percent"))
        if percent_hint is not None:
            percent = percent_hint
            raw = f"coverage_percent={percent_hint}"

    return {
        "percent": percent,
        "lines_covered": lines_covered,
        "lines_total": lines_total,
        "branches_covered": branches_covered,
        "branches_total": branches_total,
        "raw": raw,
    }


def apply_branch_coverage(text: str, coverage: dict[str, Any]) -> dict[str, Any]:
    branches_match = BRANCHES_COVERAGE_PATTERN.search(text)
    if branches_match:
        coverage["branches_covered"] = coerce_int(branches_match.group("covered"))
        coverage["branches_total"] = coerce_int(branches_match.group("total"))
        coverage["raw"] = "\n".join(
            part for part in (coverage["raw"], branches_match.group(0)) if part
        )
    return coverage


def has_coverage_values(coverage: dict[str, Any]) -> bool:
    return any(
        coverage.get(key) is not None
        for key in ("lines_covered", "lines_total", "branches_covered", "branches_total")
    )


def parse_coverage_from_text(result: dict[str, Any], text: str) -> dict[str, Any] | None:
    coverage = apply_branch_coverage(text, parse_primary_coverage_values(result, text))
    if coverage["percent"] is None and not has_coverage_values(coverage):
        return None

    status = "covered" if coverage["percent"] is not None else "partial"
    return {
        "status": status,
        "percent": coverage["percent"],
        "lines_covered": coverage["lines_covered"],
        "lines_total": coverage["lines_total"],
        "branches_covered": coverage["branches_covered"],
        "branches_total": coverage["branches_total"],
        "raw": coverage["raw"],
    }


def parse_coverage(result: dict[str, Any], text: str) -> dict[str, Any] | None:
    explicit_coverage = normalize_explicit_coverage(result)
    if explicit_coverage is not None:
        return explicit_coverage
    return parse_coverage_from_text(result, text)


def build_summary(tool: str, status: str, failure_count: int, warning_count: int, coverage: dict[str, Any] | None) -> str:
    parts = [tool, status]
    parts.append(f"failures={failure_count}")
    parts.append(f"warnings={warning_count}")
    if coverage and coverage.get("percent") is not None:
        parts.append(f"coverage={coverage['percent']:.2f}%")
    return " | ".join(parts)


def normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    tool = normalize_tool_name(result)
    text = stream_text(result)
    issues = parse_structured_issues(result)

    if tool == "markdownlint":
        issues.extend(parse_markdownlint(text))
    elif tool == "shellcheck":
        issues.extend(parse_shellcheck(text))
    elif tool in {"pytest", "coverage"}:
        issues.extend(parse_pytest_summary(text))

    issues.extend(parse_generic_path_issues(text))
    issues = dedupe_issues(issues)

    failures = [issue for issue in issues if issue["severity"] == "failure"]
    warnings = [issue for issue in issues if issue["severity"] == "warning"]
    coverage = parse_coverage(result, text)

    exit_code = coerce_int(result.get("exit_code"))
    status = "ok"
    if exit_code not in (None, 0) or failures:
        status = "failed"
    elif warnings:
        status = "warning"

    return {
        "tool": tool,
        "command": as_text(result.get("command")) or None,
        "status": status,
        "exit_code": exit_code,
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "failures": failures,
        "warnings": warnings,
        "coverage": coverage,
        "summary": build_summary(tool, status, len(failures), len(warnings), coverage),
        "raw_excerpt": text[:500] if text else None,
    }
