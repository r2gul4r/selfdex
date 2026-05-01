#!/usr/bin/env python3
"""Validate the repo-local Selfdex Codex plugin package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from cli_output_utils import write_json_or_markdown
except ModuleNotFoundError:
    from scripts.cli_output_utils import write_json_or_markdown


PLUGIN_PATH = Path("plugins/selfdex")
PLUGIN_JSON = PLUGIN_PATH / ".codex-plugin" / "plugin.json"
SKILL_PATH = PLUGIN_PATH / "skills" / "selfdex" / "SKILL.md"
COMMIT_GATE_SKILL_PATH = PLUGIN_PATH / "skills" / "selfdex-commit-gate" / "SKILL.md"
MARKETPLACE_PATH = Path(".agents/plugins/marketplace.json")
REQUIRED_SKILL_PHRASES = (
    "@selfdex",
    "explicit permission",
    "Codex native Subagents/MultiAgentV2",
    "main agent",
    "explorer",
    "docs_researcher",
    "worker",
    "reviewer",
    "current working directory",
    "SELFDEX_ROOT",
    "scripts/plan_external_project.py",
    "scripts/run_target_codex.py",
    "scripts/install_selfdex_plugin.py",
    "explicit approval",
    "External projects are read-only by default",
    "Do not install this plugin",
    "check_commit_gate.py",
)
REQUIRED_COMMIT_GATE_PHRASES = (
    "selfdex-commit-gate",
    "scripts/check_commit_gate.py",
    "scripts/check_github_actions_status.py",
    "Conventional Commits",
    "GitHub Actions",
    "Do not select the next candidate",
    "explicitly asks for it",
)
REQUIRED_TOOL_PATHS = (
    "scripts/plan_external_project.py",
    "scripts/run_target_codex.py",
    "scripts/install_selfdex_plugin.py",
    "scripts/check_commit_gate.py",
    "scripts/check_github_actions_status.py",
)
REQUIRED_CODEX_AGENT_FILES = (
    ".codex/config.toml",
    ".codex/agents/explorer.toml",
    ".codex/agents/worker.toml",
    ".codex/agents/reviewer.toml",
    ".codex/agents/docs-researcher.toml",
)
LEGACY_ACTIVE_RUNTIME_PATTERNS = (
    "Use lightweight `single-session` by default",
    "lightweight `single-session`",
    "frozen-contract `single-session`",
    "default_agent_budget",
    "max_agent_budget",
    "score_total",
    "agent_budget",
)


@dataclass(frozen=True)
class Finding:
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
    parser = argparse.ArgumentParser(description="Validate the Selfdex plugin package.")
    parser.add_argument("--root", default=".", help="Selfdex repository root.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args(argv)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.+?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def contains_todo(value: Any) -> bool:
    if isinstance(value, str):
        return "[TODO:" in value
    if isinstance(value, list):
        return any(contains_todo(item) for item in value)
    if isinstance(value, dict):
        return any(contains_todo(item) for item in value.values())
    return False


def plugin_marketplace_entry(payload: dict[str, Any]) -> dict[str, Any] | None:
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        return None
    for entry in plugins:
        if isinstance(entry, dict) and entry.get("name") == "selfdex":
            return entry
    return None


def validate(root: Path) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    plugin_path = root / PLUGIN_JSON
    skill_path = root / SKILL_PATH
    marketplace_path = root / MARKETPLACE_PATH

    for required_path in (
        plugin_path,
        skill_path,
        root / COMMIT_GATE_SKILL_PATH,
        marketplace_path,
        *(root / path for path in REQUIRED_CODEX_AGENT_FILES),
    ):
        if not required_path.exists():
            findings.append(
                Finding(
                    "missing-plugin-file",
                    "high",
                    required_path.relative_to(root).as_posix(),
                    "Required Selfdex plugin file is missing.",
                )
            )

    plugin: dict[str, Any] = {}
    if plugin_path.exists():
        plugin = read_json(plugin_path)
        if plugin.get("name") != "selfdex":
            findings.append(
                Finding("plugin-name-mismatch", "high", PLUGIN_JSON.as_posix(), "Plugin name must be selfdex.")
            )
        if plugin.get("skills") != "./skills/":
            findings.append(
                Finding("plugin-skills-path", "high", PLUGIN_JSON.as_posix(), "Plugin skills path must be ./skills/.")
            )
        if contains_todo(plugin):
            findings.append(
                Finding("plugin-placeholder", "medium", PLUGIN_JSON.as_posix(), "Plugin manifest still contains TODO placeholders.")
            )
        defaults = plugin.get("interface", {}).get("defaultPrompt", [])
        if not any(isinstance(item, str) and item.startswith("@selfdex") for item in defaults):
            findings.append(
                Finding("missing-at-selfdex-prompt", "medium", PLUGIN_JSON.as_posix(), "Default prompts should show @selfdex invocation.")
            )

    skill_text = ""
    if skill_path.exists():
        skill_text = skill_path.read_text(encoding="utf-8")
        metadata = frontmatter(skill_text)
        if metadata.get("name") != "selfdex":
            findings.append(
                Finding("skill-name-mismatch", "high", SKILL_PATH.as_posix(), "Skill frontmatter name must be selfdex.")
            )
        for phrase in REQUIRED_SKILL_PHRASES:
            if phrase not in skill_text:
                findings.append(
                    Finding("skill-missing-safety-phrase", "high", SKILL_PATH.as_posix(), f"Skill is missing required phrase: {phrase}")
                )
        for phrase in LEGACY_ACTIVE_RUNTIME_PATTERNS:
            if phrase in skill_text:
                findings.append(
                    Finding(
                        "skill-legacy-runtime-phrase",
                        "high",
                        SKILL_PATH.as_posix(),
                        f"Skill still contains legacy active runtime wording: {phrase}",
                    )
                )

    commit_gate_text = ""
    commit_gate_path = root / COMMIT_GATE_SKILL_PATH
    if commit_gate_path.exists():
        commit_gate_text = commit_gate_path.read_text(encoding="utf-8")
        metadata = frontmatter(commit_gate_text)
        if metadata.get("name") != "selfdex-commit-gate":
            findings.append(
                Finding(
                    "commit-gate-skill-name-mismatch",
                    "high",
                    COMMIT_GATE_SKILL_PATH.as_posix(),
                    "Commit gate skill frontmatter name must be selfdex-commit-gate.",
                )
            )
        for phrase in REQUIRED_COMMIT_GATE_PHRASES:
            if phrase not in commit_gate_text:
                findings.append(
                    Finding(
                        "commit-gate-missing-safety-phrase",
                        "high",
                        COMMIT_GATE_SKILL_PATH.as_posix(),
                        f"Commit gate skill is missing required phrase: {phrase}",
                    )
                )

    marketplace: dict[str, Any] = {}
    if marketplace_path.exists():
        marketplace = read_json(marketplace_path)
        entry = plugin_marketplace_entry(marketplace)
        if entry is None:
            findings.append(
                Finding("missing-marketplace-entry", "high", MARKETPLACE_PATH.as_posix(), "Marketplace must include the selfdex plugin entry.")
            )
        else:
            source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
            policy = entry.get("policy") if isinstance(entry.get("policy"), dict) else {}
            if source.get("path") != "./plugins/selfdex":
                findings.append(
                    Finding("marketplace-path-mismatch", "high", MARKETPLACE_PATH.as_posix(), "Marketplace path must be ./plugins/selfdex.")
                )
            if policy.get("installation") != "AVAILABLE":
                findings.append(
                    Finding("marketplace-installation-policy", "medium", MARKETPLACE_PATH.as_posix(), "Marketplace installation policy must be AVAILABLE.")
                )
            if policy.get("authentication") != "ON_INSTALL":
                findings.append(
                    Finding("marketplace-authentication-policy", "medium", MARKETPLACE_PATH.as_posix(), "Marketplace authentication policy must be ON_INSTALL.")
                )

    for path in REQUIRED_TOOL_PATHS:
        if not (root / path).exists():
            findings.append(
                Finding("missing-selfdex-command", "high", path, "Selfdex plugin references a missing command.")
            )
    for path in REQUIRED_CODEX_AGENT_FILES:
        if not (root / path).exists():
            findings.append(
                Finding("missing-codex-agent-config", "high", path, "Selfdex native subagent configuration is missing.")
            )

    metadata = {
        "plugin_path": PLUGIN_JSON.as_posix(),
        "skill_path": SKILL_PATH.as_posix(),
        "commit_gate_skill_path": COMMIT_GATE_SKILL_PATH.as_posix(),
        "marketplace_path": MARKETPLACE_PATH.as_posix(),
        "plugin_name": plugin.get("name"),
        "default_prompt_count": len(plugin.get("interface", {}).get("defaultPrompt", [])) if plugin else 0,
        "skill_phrase_count": sum(1 for phrase in REQUIRED_SKILL_PHRASES if phrase in skill_text),
        "commit_gate_phrase_count": sum(1 for phrase in REQUIRED_COMMIT_GATE_PHRASES if phrase in commit_gate_text),
        "codex_agent_file_count": sum(1 for path in REQUIRED_CODEX_AGENT_FILES if (root / path).exists()),
    }
    return findings, metadata


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings, metadata = validate(root)
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_plugin_check",
        "root": str(root),
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
        "findings": [finding.to_dict() for finding in findings],
        **metadata,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Selfdex Plugin Check",
        "",
        f"- status: `{payload['status']}`",
        f"- finding_count: `{payload['finding_count']}`",
        f"- plugin_path: `{payload['plugin_path']}`",
        f"- skill_path: `{payload['skill_path']}`",
        f"- commit_gate_skill_path: `{payload['commit_gate_skill_path']}`",
        f"- marketplace_path: `{payload['marketplace_path']}`",
        "",
        "## Findings",
        "",
    ]
    for finding in payload["findings"]:
        lines.append(f"- `{finding['finding_id']}` {finding['path']}: {finding['summary']}")
    if not payload["findings"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_payload(Path(args.root))
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json_or_markdown(payload, args.format, render_markdown)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
