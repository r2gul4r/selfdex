#!/usr/bin/env python3
"""Install the Selfdex Codex plugin into a Codex-discovered marketplace."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from cli_output_utils import write_json_or_markdown
except ModuleNotFoundError:
    from scripts.cli_output_utils import write_json_or_markdown


PLUGIN_NAME = "selfdex"
PLUGIN_REL = Path("plugins") / PLUGIN_NAME
PLUGIN_JSON_REL = PLUGIN_REL / ".codex-plugin" / "plugin.json"
SKILL_REL = PLUGIN_REL / "skills" / PLUGIN_NAME / "SKILL.md"
MARKETPLACE_REL = Path(".agents") / "plugins" / "marketplace.json"
ROOT_CONFIG_NAME = "selfdex-root.json"


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
    parser = argparse.ArgumentParser(
        description="Install the Selfdex plugin into a Codex-discovered marketplace."
    )
    parser.add_argument("--root", default=".", help="Selfdex checkout root.")
    parser.add_argument(
        "--home",
        default="",
        help="Plugin home directory that owns plugins/ and .agents/plugins/marketplace.json. Defaults to CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually write the home-local plugin and marketplace files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview planned writes. This is also the default when --yes is omitted.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow updating an existing home-local selfdex plugin directory or marketplace entry.",
    )
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def default_plugin_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "")
    if codex_home:
        return Path(codex_home).expanduser()
    return Path.home() / ".codex"


def plugin_home_from(override: str = "") -> Path:
    if override:
        return Path(override).expanduser()
    return default_plugin_home()


def validate_source(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    required_paths = (
        PLUGIN_JSON_REL,
        SKILL_REL,
        Path("scripts") / "plan_external_project.py",
        Path("scripts") / "run_target_codex.py",
        Path("CAMPAIGN_STATE.json"),
    )
    for rel_path in required_paths:
        if not (root / rel_path).exists():
            findings.append(
                Finding(
                    "missing-source-file",
                    "high",
                    rel_path.as_posix(),
                    "Required Selfdex installer source file is missing.",
                )
            )
    if (root / PLUGIN_JSON_REL).exists():
        plugin = read_json(root / PLUGIN_JSON_REL)
        if plugin.get("name") != PLUGIN_NAME:
            findings.append(
                Finding(
                    "plugin-name-mismatch",
                    "high",
                    PLUGIN_JSON_REL.as_posix(),
                    "Source plugin manifest name must be selfdex.",
                )
            )
    return findings


def marketplace_entry(source_path: str) -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": source_path,
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }


def load_marketplace(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": "selfdex-local",
            "interface": {
                "displayName": "Selfdex Local",
            },
            "plugins": [],
        }
    payload = read_json(path)
    if not isinstance(payload.get("plugins"), list):
        raise ValueError(f"{path} field 'plugins' must be an array")
    if not isinstance(payload.get("interface", {}), dict):
        raise ValueError(f"{path} field 'interface' must be an object")
    return payload


def update_marketplace(
    payload: dict[str, Any],
    *,
    source_path: str,
    marketplace_path: Path,
    force: bool,
) -> tuple[dict[str, Any], list[Finding], str]:
    findings: list[Finding] = []
    plugins = payload.setdefault("plugins", [])
    if not isinstance(plugins, list):
        raise ValueError(f"{marketplace_path} field 'plugins' must be an array")

    desired = marketplace_entry(source_path)
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict) or entry.get("name") != PLUGIN_NAME:
            continue
        if entry == desired:
            return payload, findings, "marketplace_entry_current"
        if not force:
            findings.append(
                Finding(
                    "existing-marketplace-entry",
                    "high",
                    str(marketplace_path),
                    "A selfdex marketplace entry already exists; rerun with --force to replace it.",
                )
            )
            return payload, findings, "marketplace_entry_blocked"
        plugins[index] = desired
        return payload, findings, "marketplace_entry_replaced"

    plugins.append(desired)
    return payload, findings, "marketplace_entry_added"


def relative_plugin_source(home: Path, target_plugin: Path) -> str:
    try:
        rel = target_plugin.resolve().relative_to(home.resolve())
    except ValueError as exc:
        raise ValueError("Target plugin path must be inside the selected --home directory") from exc
    return "./" + rel.as_posix()


def copied_files(source_plugin: Path) -> list[Path]:
    return sorted(path for path in source_plugin.rglob("*") if path.is_file())


def copy_plugin_files(source_plugin: Path, target_plugin: Path, *, selfdex_root: Path) -> int:
    count = 0
    for source_file in copied_files(source_plugin):
        rel_path = source_file.relative_to(source_plugin)
        target_file = target_plugin / rel_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        count += 1

    root_config = {
        "schema_version": 1,
        "selfdex_root": str(selfdex_root),
    }
    write_json(target_plugin / ROOT_CONFIG_NAME, root_config)
    append_installed_checkout(target_plugin / "skills" / PLUGIN_NAME / "SKILL.md", selfdex_root)
    return count + 1


def append_installed_checkout(skill_path: Path, selfdex_root: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")
    marker = "## Installed Checkout"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    text = (
        text.rstrip()
        + "\n\n"
        + marker
        + "\n\n"
        + "This plugin was installed from this Selfdex checkout:\n\n"
        + f"`{selfdex_root}`\n"
    )
    skill_path.write_text(text + "\n", encoding="utf-8")


def build_payload(root: Path, home: Path, *, yes: bool = False, dry_run: bool = False, force: bool = False) -> dict[str, Any]:
    root = root.resolve()
    home = home.expanduser().resolve()
    source_plugin = root / PLUGIN_REL
    target_plugin = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / MARKETPLACE_REL
    effective_dry_run = dry_run or not yes

    findings = validate_source(root)
    operations: list[dict[str, Any]] = []
    source_path = relative_plugin_source(home, target_plugin)
    if source_plugin.resolve() == target_plugin.resolve():
        findings.append(
            Finding(
                "source-target-overlap",
                "high",
                str(target_plugin),
                "Install target must not be the source plugin directory; choose a real home directory.",
            )
        )

    if target_plugin.exists() and not force:
        findings.append(
            Finding(
                "existing-plugin-directory",
                "high",
                str(target_plugin),
                    "Selfdex plugin directory already exists; rerun with --force to update it.",
            )
        )

    marketplace = load_marketplace(marketplace_path)
    marketplace, marketplace_findings, marketplace_status = update_marketplace(
        marketplace,
        source_path=source_path,
        marketplace_path=marketplace_path,
        force=force,
    )
    findings.extend(marketplace_findings)

    operations.append(
        {
            "action": "copy_plugin",
            "source": str(source_plugin),
            "target": str(target_plugin),
            "status": "planned" if effective_dry_run and not findings else "blocked" if findings else "ready",
        }
    )
    operations.append(
        {
            "action": "write_root_config",
            "target": str(target_plugin / ROOT_CONFIG_NAME),
            "status": "planned" if effective_dry_run and not findings else "blocked" if findings else "ready",
        }
    )
    operations.append(
        {
            "action": "update_marketplace",
            "target": str(marketplace_path),
            "status": marketplace_status if not findings else "blocked",
        }
    )

    files_copied = 0
    if not findings and not effective_dry_run:
        target_plugin.mkdir(parents=True, exist_ok=True)
        files_copied = copy_plugin_files(source_plugin, target_plugin, selfdex_root=root)
        write_json(marketplace_path, marketplace)
        for operation in operations:
            if operation["status"] in {"ready", marketplace_status}:
                operation["status"] = "done"

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_plugin_install",
        "status": "pass" if not findings else "fail",
        "dry_run": effective_dry_run,
        "writes_enabled": not effective_dry_run,
        "force": force,
        "root": str(root),
        "home": str(home),
        "source_plugin": str(source_plugin),
        "target_plugin": str(target_plugin),
        "marketplace_path": str(marketplace_path),
        "marketplace_source_path": source_path,
        "operation_count": len(operations),
        "operations": operations,
        "files_copied": files_copied,
        "finding_count": len(findings),
        "findings": [finding.to_dict() for finding in findings],
        "next_step": "Restart or refresh Codex plugin discovery, then invoke @selfdex from a target project session."
        if not effective_dry_run and not findings
        else "Rerun with --yes to install, or fix the findings first.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Selfdex Plugin Installer",
        "",
        f"- status: `{payload['status']}`",
        f"- dry_run: `{payload['dry_run']}`",
        f"- writes_enabled: `{payload['writes_enabled']}`",
        f"- target_plugin: `{payload['target_plugin']}`",
        f"- marketplace_path: `{payload['marketplace_path']}`",
        "",
        "## Operations",
        "",
    ]
    for operation in payload["operations"]:
        lines.append(f"- `{operation['action']}` {operation['status']}: `{operation['target']}`")
    lines.extend(["", "## Findings", ""])
    if payload["findings"]:
        for finding in payload["findings"]:
            lines.append(f"- `{finding['finding_id']}` {finding['path']}: {finding['summary']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Next Step", "", payload["next_step"]])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_payload(
            Path(args.root),
            plugin_home_from(args.home),
            yes=args.yes,
            dry_run=args.dry_run,
            force=args.force,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json_or_markdown(payload, args.format, render_markdown)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
