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

try:
    from markdown_utils import clean_markdown_value, extract_markdown_section
except ModuleNotFoundError:
    from scripts.markdown_utils import clean_markdown_value, extract_markdown_section


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
    max_subagent_threads: int | None
    subagent_runtime: str
    hard_approval_zones: list[str]
    model_usage_policy: dict[str, str]
    first_app_surface: dict[str, str]
    subagent_permission_policy: dict[str, str]
    source: str


@dataclass(frozen=True)
class StateContract:
    task: str
    phase: str
    selected_agents: list[str]
    subagent_permission: str
    write_paths: list[str]
    source: str


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


@dataclass(frozen=True)
class MirrorWarning:
    warning_id: str
    source: str
    field: str
    canonical: str
    mirror: str

    def to_dict(self) -> dict[str, str]:
        return {
            "warning_id": self.warning_id,
            "source": self.source,
            "field": self.field,
            "canonical": self.canonical,
            "mirror": self.mirror,
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


def parse_list_field(lines: list[str], field_name: str) -> list[str]:
    values: list[str] = []
    in_field = False
    field_pattern = re.compile(rf"^\s*-\s*{re.escape(field_name)}:\s*$")
    item_pattern = re.compile(r"^\s+-\s*`?(.+?)`?\s*$")
    for line in lines:
        if field_pattern.match(line):
            in_field = True
            continue
        if in_field:
            if re.match(r"^\s*-\s*[A-Za-z0-9_.-]+:", line):
                break
            match = item_pattern.match(line)
            if match:
                values.append(clean_markdown_value(match.group(1)))
    return values


def parse_key_value_section(text: str, heading: str) -> dict[str, str]:
    values: dict[str, str] = {}
    pattern = re.compile(r"^\s*-\s*([A-Za-z0-9_.-]+):\s*(.+?)\s*$")
    for line in extract_markdown_section(text, heading):
        match = pattern.match(line)
        if match:
            values[match.group(1)] = clean_markdown_value(match.group(2))
    return values


def contract_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value)


def parse_json_string_map(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    return {str(key): contract_value(value) for key, value in payload.items()}


def parse_campaign_budget(text: str, *, source: str = "CAMPAIGN_STATE.md") -> CampaignBudget:
    campaign_lines = extract_markdown_section(text, "Campaign")
    return CampaignBudget(
        max_subagent_threads=parse_int_field(campaign_lines, "max_subagent_threads"),
        subagent_runtime=parse_text_field(campaign_lines, "subagent_runtime"),
        hard_approval_zones=parse_list_section(text, "Hard Approval Zones"),
        model_usage_policy=parse_key_value_section(text, "Model Usage Policy"),
        first_app_surface=parse_key_value_section(text, "First App Surface"),
        subagent_permission_policy=parse_key_value_section(text, "Subagent Permission Policy"),
        source=source,
    )


def parse_campaign_budget_json(payload: dict[str, Any], *, source: str = "CAMPAIGN_STATE.json") -> CampaignBudget:
    campaign = payload.get("campaign")
    if not isinstance(campaign, dict):
        campaign = {}
    zones = payload.get("hard_approval_zones")
    if not isinstance(zones, list):
        zones = []
    return CampaignBudget(
        max_subagent_threads=int(campaign["max_subagent_threads"])
        if isinstance(campaign.get("max_subagent_threads"), int)
        else None,
        subagent_runtime=str(campaign.get("subagent_runtime") or ""),
        hard_approval_zones=[str(zone) for zone in zones],
        model_usage_policy=parse_json_string_map(payload.get("model_usage_policy")),
        first_app_surface=parse_json_string_map(payload.get("first_app_surface")),
        subagent_permission_policy=parse_json_string_map(payload.get("subagent_permission_policy")),
        source=source,
    )


def looks_like_path(value: str) -> bool:
    if not value or value in {".", ".."}:
        return False
    normalized = value.replace("\\", "/")
    if "/" in normalized:
        return True
    if normalized.startswith(".") and len(normalized) > 1:
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


def parse_state_contract(text: str, *, source: str = "STATE.md") -> StateContract:
    current_task_lines = extract_markdown_section(text, "Current Task")
    profile_lines = extract_markdown_section(text, "Orchestration Profile")
    return StateContract(
        task=parse_text_field(current_task_lines, "task"),
        phase=parse_text_field(current_task_lines, "phase"),
        selected_agents=parse_list_field(profile_lines, "selected_agents"),
        subagent_permission=parse_text_field(profile_lines, "subagent_permission"),
        write_paths=extract_write_paths(text),
        source=source,
    )


def parse_state_contract_json(payload: dict[str, Any], *, source: str = "STATE.json") -> StateContract:
    task = payload.get("current_task")
    if not isinstance(task, dict):
        task = {}
    profile = payload.get("orchestration_profile")
    if not isinstance(profile, dict):
        profile = {}
    writer_slot = payload.get("writer_slot")
    if not isinstance(writer_slot, dict):
        writer_slot = {}
    write_sets = writer_slot.get("write_sets")
    paths: list[str] = []
    seen: set[str] = set()
    if isinstance(write_sets, dict):
        for values in write_sets.values():
            if not isinstance(values, list):
                continue
            for value in values:
                cleaned = str(value)
                if looks_like_path(cleaned) and cleaned not in seen:
                    seen.add(cleaned)
                    paths.append(cleaned)
    selected_agents = profile.get("selected_agents")
    return StateContract(
        task=str(task.get("task") or ""),
        phase=str(task.get("phase") or ""),
        selected_agents=[str(agent) for agent in selected_agents] if isinstance(selected_agents, list) else [],
        subagent_permission=str(profile.get("subagent_permission") or ""),
        write_paths=paths,
        source=source,
    )


def read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def load_campaign_budget(root: Path) -> CampaignBudget:
    json_payload = read_json_object(root / "CAMPAIGN_STATE.json")
    if json_payload is not None:
        return parse_campaign_budget_json(json_payload)
    campaign_text = (root / "CAMPAIGN_STATE.md").read_text(encoding="utf-8")
    return parse_campaign_budget(campaign_text)


def load_state_contract(root: Path) -> StateContract:
    json_payload = read_json_object(root / "STATE.json")
    if json_payload is not None:
        return parse_state_contract_json(json_payload)
    state_text = (root / "STATE.md").read_text(encoding="utf-8")
    return parse_state_contract(state_text)


def compare_optional_values(
    *,
    warnings: list[MirrorWarning],
    source: str,
    field: str,
    canonical: object,
    mirror: object,
) -> None:
    if canonical == mirror:
        return
    warnings.append(
        MirrorWarning(
            warning_id="structured-markdown-mirror-drift",
            source=source,
            field=field,
            canonical=str(canonical),
            mirror=str(mirror),
        )
    )


def find_mirror_warnings(root: Path, campaign: CampaignBudget, contract: StateContract) -> list[MirrorWarning]:
    warnings: list[MirrorWarning] = []
    if campaign.source == "CAMPAIGN_STATE.json" and (root / "CAMPAIGN_STATE.md").exists():
        mirror = parse_campaign_budget(
            (root / "CAMPAIGN_STATE.md").read_text(encoding="utf-8"),
            source="CAMPAIGN_STATE.md",
        )
        compare_optional_values(
            warnings=warnings,
            source="CAMPAIGN_STATE.md",
            field="max_subagent_threads",
            canonical=campaign.max_subagent_threads,
            mirror=mirror.max_subagent_threads,
        )
        compare_optional_values(
            warnings=warnings,
            source="CAMPAIGN_STATE.md",
            field="subagent_runtime",
            canonical=campaign.subagent_runtime,
            mirror=mirror.subagent_runtime,
        )
        compare_optional_values(
            warnings=warnings,
            source="CAMPAIGN_STATE.md",
            field="hard_approval_zones",
            canonical=campaign.hard_approval_zones,
            mirror=mirror.hard_approval_zones,
        )
        compare_optional_values(
            warnings=warnings,
            source="CAMPAIGN_STATE.md",
            field="model_usage_policy",
            canonical=campaign.model_usage_policy,
            mirror=mirror.model_usage_policy,
        )
        compare_optional_values(
            warnings=warnings,
            source="CAMPAIGN_STATE.md",
            field="first_app_surface",
            canonical=campaign.first_app_surface,
            mirror=mirror.first_app_surface,
        )
        compare_optional_values(
            warnings=warnings,
            source="CAMPAIGN_STATE.md",
            field="subagent_permission_policy",
            canonical=campaign.subagent_permission_policy,
            mirror=mirror.subagent_permission_policy,
        )
    if contract.source == "STATE.json" and (root / "STATE.md").exists():
        mirror = parse_state_contract(
            (root / "STATE.md").read_text(encoding="utf-8"),
            source="STATE.md",
        )
        compare_optional_values(
            warnings=warnings,
            source="STATE.md",
            field="task",
            canonical=contract.task,
            mirror=mirror.task,
        )
        compare_optional_values(
            warnings=warnings,
            source="STATE.md",
            field="phase",
            canonical=contract.phase,
            mirror=mirror.phase,
        )
        compare_optional_values(
            warnings=warnings,
            source="STATE.md",
            field="selected_agents",
            canonical=contract.selected_agents,
            mirror=mirror.selected_agents,
        )
        compare_optional_values(
            warnings=warnings,
            source="STATE.md",
            field="subagent_permission",
            canonical=contract.subagent_permission,
            mirror=mirror.subagent_permission,
        )
        compare_optional_values(
            warnings=warnings,
            source="STATE.md",
            field="write_paths",
            canonical=sorted(contract.write_paths),
            mirror=sorted(mirror.write_paths),
        )
    return warnings


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
                    message="State contract write_sets contains a path outside the repository.",
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
    if lower_path.startswith("runs/"):
        return []
    matches: list[str] = []
    for key in zone_hint_keys(zones):
        hints = HARD_APPROVAL_HINTS[key]
        if any(hint in lower_path for hint in hints):
            matches.append(key)
    return matches


def git_changed_paths(root: Path) -> list[str]:
    paths: list[str] = []
    commands = (
        ("git", "-c", "core.quotePath=false", "diff", "--name-only"),
        ("git", "-c", "core.quotePath=false", "diff", "--name-only", "--cached"),
        ("git", "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard"),
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
    if campaign.source != "CAMPAIGN_STATE.json":
        violations.append(
            Violation(
                violation_id="missing-structured-campaign-contract",
                severity="high",
                message="CAMPAIGN_STATE.json is required as the campaign source of truth.",
                evidence=campaign.source,
            )
        )
    if contract.source != "STATE.json":
        violations.append(
            Violation(
                violation_id="missing-structured-state-contract",
                severity="high",
                message="STATE.json is required as the active task source of truth.",
                evidence=contract.source,
            )
        )
    if campaign.max_subagent_threads is None:
        violations.append(
            Violation(
                violation_id="missing-campaign-subagent-limit",
                severity="high",
                message="Campaign contract does not define max_subagent_threads.",
                evidence=campaign.source,
            )
        )
    if not contract.subagent_permission or not contract.selected_agents:
        violations.append(
            Violation(
                violation_id="missing-state-subagent-policy",
                severity="high",
                message="State contract must define native subagent permission and selected_agents.",
                evidence=contract.source,
            )
        )
    elif campaign.max_subagent_threads is not None and len(contract.selected_agents) > campaign.max_subagent_threads:
        violations.append(
            Violation(
                violation_id="state-subagent-count-exceeds-campaign-max",
                severity="high",
                message="State contract selected_agents exceeds campaign max_subagent_threads.",
                evidence=(
                    f"selected_agents={len(contract.selected_agents)}, "
                    f"max_subagent_threads={campaign.max_subagent_threads}"
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
    campaign = load_campaign_budget(root)
    contract = load_state_contract(root)
    mirror_warnings = find_mirror_warnings(root, campaign, contract)

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
                    message="Changed path is not declared in the state contract write_sets.",
                    evidence=relative,
                )
            )

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_campaign_budget_check",
        "root": str(root),
        "status": "pass" if not violations else "fail",
        "contract_sources": {
            "campaign": campaign.source,
            "state": contract.source,
        },
        "mirror_warning_count": len(mirror_warnings),
        "mirror_warnings": [warning.to_dict() for warning in mirror_warnings],
        "campaign_budget": {
            "max_subagent_threads": campaign.max_subagent_threads,
            "subagent_runtime": campaign.subagent_runtime,
            "hard_approval_zones": campaign.hard_approval_zones,
            "model_usage_policy": campaign.model_usage_policy,
            "first_app_surface": campaign.first_app_surface,
            "subagent_permission_policy": campaign.subagent_permission_policy,
        },
        "state_contract": {
            "task": contract.task,
            "phase": contract.phase,
            "selected_agents": contract.selected_agents,
            "subagent_permission": contract.subagent_permission,
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
        f"- mirror_warning_count: `{payload['mirror_warning_count']}`",
        f"- campaign_source: `{payload['contract_sources']['campaign']}`",
        f"- state_source: `{payload['contract_sources']['state']}`",
        f"- task: `{contract['task']}`",
        f"- phase: `{contract['phase']}`",
        f"- max_subagent_threads: `{budget['max_subagent_threads']}`",
        f"- subagent_runtime: `{budget['subagent_runtime']}`",
        f"- selected_agents: `{'; '.join(contract['selected_agents']) or 'none'}`",
        f"- subagent_permission: `{contract['subagent_permission'] or 'none'}`",
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
    lines.extend(["", "## Mirror Warnings", ""])
    for warning in payload["mirror_warnings"]:
        lines.append(
            f"- `{warning['warning_id']}` {warning['source']} {warning['field']}: "
            f"canonical=`{warning['canonical']}` mirror=`{warning['mirror']}`"
        )
    if not payload["mirror_warnings"]:
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
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
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
