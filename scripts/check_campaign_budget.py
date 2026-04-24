#!/usr/bin/env python3
"""Validate the active Selfdex campaign budget and write contract."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HARD_APPROVAL_HINTS = {
    "secret": (
        ".env",
        "credential",
        "credentials",
        "private-key",
        "private_key",
        "secret",
        "secrets/",
        "token",
    ),
    "deploy": (
        "deploy",
        "deployment",
        "fly.toml",
        "netlify.toml",
        "render.yaml",
        "vercel.json",
    ),
    "database": (
        "database",
        "db/",
        "migration",
        "migrations/",
        "schema.sql",
    ),
    "paid": (
        "billing",
        "paid-api",
        "stripe",
    ),
}


@dataclass(frozen=True)
class CampaignBudget:
    default_agent_budget: int | None
    max_agent_budget: int | None
    hard_approval_zones: list[str]


@dataclass(frozen=True)
class StateContract:
    task: str
    phase: str
    agent_budget: int | None
    write_paths: list[str]


@dataclass(frozen=True)
class Violation:
    violation_id: str
    severity: str
    message: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {
            "violation_id": self.violation_id,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Selfdex campaign budget constraints.")
    parser.add_argument("--root", default=".", help="Selfdex repository root.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="Changed path to validate against STATE.md write_sets. May be repeated.",
    )
    parser.add_argument(
        "--include-git-diff",
        action="store_true",
        help="Also validate paths from git diff --name-only and git diff --name-only --cached.",
    )
    parser.add_argument(
        "--allow-hard-approval",
        action="store_true",
        help="Do not fail hard-approval path hints. Use only after explicit approval.",
    )
    return parser.parse_args(argv)


def clean_markdown_value(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        value = value[1:-1]
    return value.replace("`", "").strip()


def extract_markdown_section(text: str, heading: str) -> list[str]:
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
    return lines


def parse_int_field(lines: list[str], field_name: str) -> int | None:
    pattern = re.compile(rf"^\s*-\s*{re.escape(field_name)}:\s*(.+?)\s*$")
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue
        value = clean_markdown_value(match.group(1))
        try:
            return int(value)
        except ValueError:
            return None
    return None


def parse_text_field(lines: list[str], field_name: str) -> str:
    pattern = re.compile(rf"^\s*-\s*{re.escape(field_name)}:\s*(.+?)\s*$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return clean_markdown_value(match.group(1))
    return ""


def parse_list_section(text: str, heading: str) -> list[str]:
    items: list[str] = []
    for line in extract_markdown_section(text, heading):
        match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if match:
            items.append(clean_markdown_value(match.group(1)))
    return items


def parse_campaign_budget(text: str) -> CampaignBudget:
    campaign_lines = extract_markdown_section(text, "Campaign")
    return CampaignBudget(
        default_agent_budget=parse_int_field(campaign_lines, "default_agent_budget"),
        max_agent_budget=parse_int_field(campaign_lines, "max_agent_budget"),
        hard_approval_zones=parse_list_section(text, "Hard Approval Zones"),
    )


def looks_like_path(value: str) -> bool:
    if not value or value in {".", ".."}:
        return False
    normalized = value.replace("\\", "/")
    if "/" in normalized:
        return True
    return bool(re.search(r"\.[A-Za-z0-9]{1,8}$", normalized))


def extract_write_paths(text: str) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for line in extract_markdown_section(text, "Writer Slot"):
        for value in re.findall(r"`([^`]+)`", line):
            cleaned = clean_markdown_value(value)
            if looks_like_path(cleaned) and cleaned not in seen:
                seen.add(cleaned)
                paths.append(cleaned)
    return paths


def parse_state_contract(text: str) -> StateContract:
    current_task_lines = extract_markdown_section(text, "Current Task")
    profile_lines = extract_markdown_section(text, "Orchestration Profile")
    return StateContract(
        task=parse_text_field(current_task_lines, "task"),
        phase=parse_text_field(current_task_lines, "phase"),
        agent_budget=parse_int_field(profile_lines, "agent_budget"),
        write_paths=extract_write_paths(text),
    )


def relative_to_root(root: Path, value: str) -> tuple[str | None, str | None]:
    raw = value.strip()
    if not raw:
        return None, "empty path"
    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (root / candidate).resolve()
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError:
        return None, f"path escapes repository root: {value}"
    return relative.as_posix(), None


def normalize_contract_paths(root: Path, paths: list[str]) -> tuple[list[str], list[Violation]]:
    normalized: list[str] = []
    violations: list[Violation] = []
    for path in paths:
        relative, error = relative_to_root(root, path)
        if error:
            violations.append(
                Violation(
                    violation_id="invalid-contract-path",
                    severity="high",
                    message="STATE.md write_sets contains a path outside the repository.",
                    evidence=f"{path}: {error}",
                )
            )
            continue
        if relative and relative not in normalized:
            normalized.append(relative)
    return normalized, violations


def is_path_allowed(path: str, allowed_paths: list[str]) -> bool:
    for allowed in allowed_paths:
        if path == allowed:
            return True
        if allowed.endswith("/") and path.startswith(allowed):
            return True
        if path.startswith(f"{allowed}/"):
            return True
    return False


def zone_hint_keys(zones: list[str]) -> list[str]:
    keys: list[str] = []
    joined_zones = " ".join(zones).lower()
    for key in HARD_APPROVAL_HINTS:
        if key in joined_zones:
            keys.append(key)
    return keys


def hard_approval_matches(path: str, zones: list[str]) -> list[str]:
    lower_path = path.lower().replace("\\", "/")
    matches: list[str] = []
    for key in zone_hint_keys(zones):
        hints = HARD_APPROVAL_HINTS[key]
        if any(hint in lower_path for hint in hints):
            matches.append(key)
    return matches


def git_changed_paths(root: Path) -> list[str]:
    paths: list[str] = []
    commands = (
        ("git", "diff", "--name-only"),
        ("git", "diff", "--name-only", "--cached"),
    )
    for command in commands:
        process = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip() or f"{' '.join(command)} failed")
        for line in process.stdout.splitlines():
            path = line.strip()
            if path and path not in paths:
                paths.append(path)
    return paths


def check_budget(
    campaign: CampaignBudget,
    contract: StateContract,
) -> list[Violation]:
    violations: list[Violation] = []
    if campaign.max_agent_budget is None:
        violations.append(
            Violation(
                violation_id="missing-campaign-max-budget",
                severity="high",
                message="CAMPAIGN_STATE.md does not define max_agent_budget.",
                evidence="## Campaign",
            )
        )
    if campaign.default_agent_budget is not None and campaign.max_agent_budget is not None:
        if campaign.default_agent_budget > campaign.max_agent_budget:
            violations.append(
                Violation(
                    violation_id="campaign-default-budget-exceeds-max",
                    severity="high",
                    message="default_agent_budget exceeds max_agent_budget.",
                    evidence=(
                        f"default_agent_budget={campaign.default_agent_budget}, "
                        f"max_agent_budget={campaign.max_agent_budget}"
                    ),
                )
            )
    if contract.agent_budget is None:
        violations.append(
            Violation(
                violation_id="missing-state-agent-budget",
                severity="high",
                message="STATE.md does not define agent_budget.",
                evidence="## Orchestration Profile",
            )
        )
    elif contract.agent_budget < 0:
        violations.append(
            Violation(
                violation_id="negative-state-agent-budget",
                severity="high",
                message="STATE.md agent_budget must be non-negative.",
                evidence=f"agent_budget={contract.agent_budget}",
            )
        )
    elif campaign.max_agent_budget is not None and contract.agent_budget > campaign.max_agent_budget:
        violations.append(
            Violation(
                violation_id="state-agent-budget-exceeds-campaign-max",
                severity="high",
                message="STATE.md agent_budget exceeds CAMPAIGN_STATE.md max_agent_budget.",
                evidence=(
                    f"agent_budget={contract.agent_budget}, "
                    f"max_agent_budget={campaign.max_agent_budget}"
                ),
            )
        )
    return violations


def build_payload(
    root: Path,
    changed_paths: list[str] | None = None,
    *,
    include_git_diff: bool = False,
    allow_hard_approval: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    campaign_text = (root / "CAMPAIGN_STATE.md").read_text(encoding="utf-8")
    state_text = (root / "STATE.md").read_text(encoding="utf-8")
    campaign = parse_campaign_budget(campaign_text)
    contract = parse_state_contract(state_text)

    selected_paths = list(changed_paths or [])
    if include_git_diff:
        for path in git_changed_paths(root):
            if path not in selected_paths:
                selected_paths.append(path)

    allowed_paths, violations = normalize_contract_paths(root, contract.write_paths)
    violations.extend(check_budget(campaign, contract))

    changed_path_reports: list[dict[str, Any]] = []
    for raw_path in selected_paths:
        relative, error = relative_to_root(root, raw_path)
        matches = hard_approval_matches(relative or raw_path, campaign.hard_approval_zones)
        in_contract = bool(relative and is_path_allowed(relative, allowed_paths))
        changed_path_reports.append(
            {
                "input": raw_path,
                "normalized": relative,
                "in_contract": in_contract,
                "hard_approval_matches": matches,
            }
        )
        if error:
            violations.append(
                Violation(
                    violation_id="cross-workspace-path",
                    severity="high",
                    message="Changed path escapes the repository root.",
                    evidence=f"{raw_path}: {error}",
                )
            )
            continue
        if relative and matches and not allow_hard_approval:
            violations.append(
                Violation(
                    violation_id="hard-approval-path",
                    severity="high",
                    message="Changed path matches a hard approval zone.",
                    evidence=f"{relative}: {', '.join(matches)}",
                )
            )
        if relative and not in_contract:
            violations.append(
                Violation(
                    violation_id="out-of-contract-path",
                    severity="high",
                    message="Changed path is not declared in STATE.md write_sets.",
                    evidence=relative,
                )
            )

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_campaign_budget_check",
        "root": str(root),
        "status": "pass" if not violations else "fail",
        "campaign_budget": {
            "default_agent_budget": campaign.default_agent_budget,
            "max_agent_budget": campaign.max_agent_budget,
            "hard_approval_zones": campaign.hard_approval_zones,
        },
        "state_contract": {
            "task": contract.task,
            "phase": contract.phase,
            "agent_budget": contract.agent_budget,
            "write_paths": allowed_paths,
        },
        "changed_paths": changed_path_reports,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    budget = payload["campaign_budget"]
    contract = payload["state_contract"]
    lines = [
        "# Campaign Budget Check",
        "",
        f"- status: `{payload['status']}`",
        f"- violation_count: `{payload['violation_count']}`",
        f"- task: `{contract['task']}`",
        f"- phase: `{contract['phase']}`",
        f"- agent_budget: `{contract['agent_budget']}`",
        f"- max_agent_budget: `{budget['max_agent_budget']}`",
        "",
        "## Write Contract",
        "",
    ]
    for path in contract["write_paths"]:
        lines.append(f"- `{path}`")
    if not contract["write_paths"]:
        lines.append("- none")

    lines.extend(["", "## Changed Paths", ""])
    for path in payload["changed_paths"]:
        lines.append(
            f"- `{path['input']}` -> `{path['normalized']}` "
            f"in_contract=`{path['in_contract']}` "
            f"hard_approval_matches=`{', '.join(path['hard_approval_matches']) or 'none'}`"
        )
    if not payload["changed_paths"]:
        lines.append("- none")

    lines.extend(["", "## Violations", ""])
    for violation in payload["violations"]:
        lines.append(
            f"- `{violation['violation_id']}` {violation['message']} "
            f"({violation['evidence']})"
        )
    if not payload["violations"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        payload = build_payload(
            root,
            args.changed_path,
            include_git_diff=args.include_git_diff,
            allow_hard_approval=args.allow_hard_approval,
        )
    except (FileNotFoundError, RuntimeError) as exc:
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
