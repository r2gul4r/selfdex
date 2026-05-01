#!/usr/bin/env python3
"""Check whether the local Selfdex setup is ready to use."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from cli_output_utils import write_json_or_markdown
except ModuleNotFoundError:
    from scripts.cli_output_utils import write_json_or_markdown


PLUGIN_NAME = "selfdex"
ROOT_CONFIG_NAME = "selfdex-root.json"
GITHUB_PLUGIN_REL = Path("plugins") / "cache" / "openai-curated" / "github"
CHATGPT_APPS_PLUGIN_REL = Path("plugins") / "cache" / "openai-curated" / "chatgpt-apps"
CODEX_POLICY_FILES = (
    (
        "codex-config",
        Path(".codex") / "config.toml",
        (
            "multi_agent = true",
            "[agents.explorer]",
            "[agents.worker]",
            "[agents.reviewer]",
            "[agents.docs_researcher]",
        ),
    ),
    (
        "codex-agent-explorer",
        Path(".codex") / "agents" / "explorer.toml",
        (),
    ),
    (
        "codex-agent-worker",
        Path(".codex") / "agents" / "worker.toml",
        ("frozen task slice", "declared write boundary"),
    ),
    (
        "codex-agent-reviewer",
        Path(".codex") / "agents" / "reviewer.toml",
        (),
    ),
    (
        "codex-agent-docs-researcher",
        Path(".codex") / "agents" / "docs-researcher.toml",
        (),
    ),
)
CODEX_AGENT_VALUES = {
    Path(".codex") / "agents" / "explorer.toml": {
        "name": "explorer",
        "model": "gpt-5.5",
        "model_reasoning_effort": "low",
        "sandbox_mode": "read-only",
    },
    Path(".codex") / "agents" / "worker.toml": {
        "name": "worker",
        "model": "gpt-5.5",
        "model_reasoning_effort": "high",
    },
    Path(".codex") / "agents" / "reviewer.toml": {
        "name": "reviewer",
        "model": "gpt-5.5",
        "model_reasoning_effort": "xhigh",
        "sandbox_mode": "read-only",
    },
    Path(".codex") / "agents" / "docs-researcher.toml": {
        "name": "docs_researcher",
        "model": "gpt-5.5",
        "model_reasoning_effort": "medium",
        "sandbox_mode": "read-only",
    },
}


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    category: str
    status: str
    severity: str
    summary: str
    path: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "status": self.status,
            "severity": self.severity,
            "summary": self.summary,
            "path": self.path,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Selfdex setup readiness.")
    parser.add_argument("--root", default=".", help="Selfdex checkout root.")
    parser.add_argument(
        "--home",
        default="",
        help="Plugin home directory that owns plugins and marketplace files. Defaults to CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--codex-home",
        default="",
        help="Codex home directory. Defaults to CODEX_HOME or ~/.codex.",
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown", help="Output format.")
    return parser.parse_args(argv)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def codex_home_from(home: Path, override: str = "") -> Path:
    if override:
        return Path(override).expanduser().resolve()
    env_value = ""
    try:
        import os

        env_value = os.environ.get("CODEX_HOME", "")
    except OSError:
        env_value = ""
    return Path(env_value).expanduser().resolve() if env_value else (home / ".codex").resolve()


def plugin_home_from(override: str, codex_home: Path) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return codex_home.resolve()


def marketplace_has_selfdex(path: Path) -> bool:
    if not path.exists():
        return False
    payload = read_json(path)
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        return False
    return any(isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME for entry in plugins)


def command_result(command_names: list[str], *, check_id: str, summary: str) -> CheckResult:
    for command in command_names:
        resolved = shutil.which(command)
        if resolved:
            return CheckResult(check_id, "runtime", "pass", "info", summary, resolved)
    return CheckResult(
        check_id,
        "runtime",
        "fail",
        "high",
        f"Missing required command. Tried: {', '.join(command_names)}.",
    )


def plugin_cache_result(codex_home: Path, rel_path: Path, *, check_id: str, label: str) -> CheckResult:
    path = codex_home / rel_path
    if path.exists():
        return CheckResult(check_id, "recommended_integration", "pass", "info", f"{label} plugin appears available.", str(path))
    return CheckResult(
        check_id,
        "recommended_integration",
        "manual_action",
        "medium",
        f"{label} plugin was not found in the local Codex plugin cache; install/connect it in Codex if that workflow is needed.",
        str(path),
    )


def codex_policy_result(root: Path, check_id: str, rel_path: Path, required_snippets: tuple[str, ...]) -> CheckResult:
    path = root / rel_path
    if not path.exists():
        return CheckResult(
            check_id,
            "subagent_policy",
            "fail",
            "high",
            f"Project-scoped Codex subagent policy file is missing: {rel_path.as_posix()}",
            str(path),
        )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult(
            check_id,
            "subagent_policy",
            "fail",
            "high",
            f"Project-scoped Codex subagent policy file could not be read: {exc}",
            str(path),
        )
    missing = [snippet for snippet in required_snippets if snippet not in text]
    expected_values = CODEX_AGENT_VALUES.get(rel_path)
    if expected_values:
        try:
            parsed = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            return CheckResult(
                check_id,
                "subagent_policy",
                "fail",
                "high",
                f"Project-scoped Codex subagent policy file is invalid TOML: {exc}",
                str(path),
            )
        for key, expected in expected_values.items():
            actual = parsed.get(key)
            if actual != expected:
                expected_text = f'"{expected}"' if isinstance(expected, str) else repr(expected)
                missing.append(f"{key} = {expected_text} (actual: {actual!r})")
    if missing:
        return CheckResult(
            check_id,
            "subagent_policy",
            "fail",
            "high",
            f"Project-scoped Codex subagent policy file is stale; missing: {', '.join(missing)}",
            str(path),
        )
    return CheckResult(
        check_id,
        "subagent_policy",
        "pass",
        "info",
        f"Project-scoped Codex subagent policy file is present: {rel_path.as_posix()}",
        str(path),
    )


def build_payload(root: Path, home: Path, *, codex_home: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    home = home.expanduser().resolve()
    resolved_codex_home = codex_home.resolve() if codex_home is not None else codex_home_from(home)
    target_plugin = home / "plugins" / PLUGIN_NAME
    target_skill = home / "skills" / PLUGIN_NAME / "SKILL.md"
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    root_config_path = target_plugin / ROOT_CONFIG_NAME

    checks: list[CheckResult] = [
        command_result(["git"], check_id="git-command", summary="Git is available for checkout updates."),
        CheckResult("python-command", "runtime", "pass", "info", "Python is available for Selfdex scripts.", sys.executable),
    ]

    for rel_path in (
        Path("scripts") / "plan_external_project.py",
        Path("scripts") / "run_target_codex.py",
        Path("scripts") / "check_github_actions_status.py",
    ):
        path = root / rel_path
        checks.append(
            CheckResult(
                f"selfdex-source-{rel_path.name}",
                "core",
                "pass" if path.exists() else "fail",
                "info" if path.exists() else "high",
                f"Required Selfdex source file {'exists' if path.exists() else 'is missing'}: {rel_path.as_posix()}",
                str(path),
            )
        )

    for check_id, rel_path, required_snippets in CODEX_POLICY_FILES:
        checks.append(codex_policy_result(root, check_id, rel_path, required_snippets))

    checks.append(
        CheckResult(
            "selfdex-plugin-directory",
            "core",
            "pass" if target_plugin.exists() else "fail",
            "info" if target_plugin.exists() else "high",
            "Codex plugin home @selfdex directory is installed."
            if target_plugin.exists()
            else "Codex plugin home @selfdex directory is missing.",
            str(target_plugin),
        )
    )
    checks.append(
        CheckResult(
            "selfdex-marketplace-entry",
            "core",
            "pass" if marketplace_has_selfdex(marketplace_path) else "fail",
            "info" if marketplace_has_selfdex(marketplace_path) else "high",
            "Codex plugin home marketplace includes the selfdex plugin entry."
            if marketplace_has_selfdex(marketplace_path)
            else "Codex plugin home marketplace is missing the selfdex plugin entry.",
            str(marketplace_path),
        )
    )
    checks.append(
        CheckResult(
            "selfdex-global-skill",
            "core",
            "pass" if target_skill.exists() else "fail",
            "info" if target_skill.exists() else "high",
            "Codex global skill @selfdex entry is installed."
            if target_skill.exists()
            else "Codex global skill @selfdex entry is missing; @ mention may fall back to file search.",
            str(target_skill),
        )
    )

    root_config_status = "missing"
    if root_config_path.exists():
        try:
            root_config = read_json(root_config_path)
            root_config_status = "match" if Path(str(root_config.get("selfdex_root", ""))).resolve() == root else "mismatch"
        except (json.JSONDecodeError, ValueError, OSError):
            root_config_status = "invalid"
    checks.append(
        CheckResult(
            "selfdex-root-config",
            "core",
            "pass" if root_config_status == "match" else "fail",
            "info" if root_config_status == "match" else "high",
            f"Installed plugin root config status: {root_config_status}.",
            str(root_config_path),
        )
    )

    checks.append(
        CheckResult(
            "github-actions-fallback",
            "fallback",
            "pass" if (root / "scripts" / "check_github_actions_status.py").exists() else "fail",
            "info" if (root / "scripts" / "check_github_actions_status.py").exists() else "medium",
            "GitHub Actions API fallback checker is available."
            if (root / "scripts" / "check_github_actions_status.py").exists()
            else "GitHub Actions API fallback checker is missing.",
            str(root / "scripts" / "check_github_actions_status.py"),
        )
    )
    checks.append(plugin_cache_result(resolved_codex_home, GITHUB_PLUGIN_REL, check_id="github-plugin", label="GitHub"))
    checks.append(
        plugin_cache_result(
            resolved_codex_home,
            CHATGPT_APPS_PLUGIN_REL,
            check_id="chatgpt-apps-plugin",
            label="ChatGPT Apps",
        )
    )
    checks.append(
        CheckResult(
            "gpt-pro-direction-review",
            "account_capability",
            "manual_action",
            "medium",
            "GPT Pro / GPT-5.5 direction review is an account/model entitlement and remains user-approved only.",
        )
    )
    checks.append(
        CheckResult(
            "gmail-not-required",
            "integration_boundary",
            "pass",
            "info",
            "Gmail is not required for setup or GitHub CI feedback.",
        )
    )

    high_failures = [check for check in checks if check.status == "fail" and check.severity == "high"]
    manual_actions = [check for check in checks if check.status == "manual_action"]
    readiness = "ready" if not high_failures else "blocked"
    if readiness == "ready" and manual_actions:
        readiness = "ready_with_recommended_actions"

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_setup_check",
        "status": "pass" if not high_failures else "fail",
        "readiness": readiness,
        "root": str(root),
        "home": str(home),
        "codex_home": str(resolved_codex_home),
        "check_count": len(checks),
        "manual_action_count": len(manual_actions),
        "high_failure_count": len(high_failures),
        "checks": [check.to_dict() for check in checks],
        "next_step": next_step(readiness, manual_actions),
    }


def next_step(readiness: str, manual_actions: list[CheckResult]) -> str:
    if readiness == "blocked":
        return "Fix the failed core checks, then rerun selfdex doctor."
    if manual_actions:
        return "Core setup is usable. Connect recommended integrations in Codex when those workflows are needed."
    return "Core setup and recommended integrations look ready. Invoke @selfdex from a target project session."


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Selfdex Doctor",
        "",
        f"- status: `{payload['status']}`",
        f"- readiness: `{payload['readiness']}`",
        f"- root: `{payload['root']}`",
        f"- codex_home: `{payload['codex_home']}`",
        "",
    ]
    categories = [
        ("core", "Core"),
        ("subagent_policy", "Subagent Policy"),
        ("runtime", "Runtime"),
        ("recommended_integration", "Recommended Integrations"),
        ("fallback", "Fallbacks"),
        ("account_capability", "Account Capabilities"),
        ("integration_boundary", "Integration Boundary"),
    ]
    checks = payload["checks"]
    for category, title in categories:
        category_checks = [check for check in checks if check["category"] == category]
        if not category_checks:
            continue
        lines.extend([f"## {title}", ""])
        for check in category_checks:
            lines.append(f"- `{check['status']}` {check['check_id']}: {check['summary']}")
        lines.append("")
    lines.extend(["## Next Step", "", payload["next_step"], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    resolved_codex_home = codex_home_from(Path.home(), args.codex_home)
    home = plugin_home_from(args.home, resolved_codex_home)
    try:
        payload = build_payload(Path(args.root), home, codex_home=resolved_codex_home)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json_or_markdown(payload, args.format, render_markdown)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
