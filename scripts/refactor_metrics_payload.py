"""Metrics loading and filtering helpers for refactor candidate extraction."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from repo_scan_excludes import DEFAULT_SCAN_EXCLUDED_DIRS
except ModuleNotFoundError:
    from scripts.repo_scan_excludes import DEFAULT_SCAN_EXCLUDED_DIRS


SKIP_DIRS = set(DEFAULT_SCAN_EXCLUDED_DIRS) | {"runs"}
SKIP_FILENAMES = {
    "STATE.md",
    "MULTI_AGENT_LOG.md",
    "ERROR_LOG.md",
    "Cargo.lock",
    "Gemfile.lock",
    "Pipfile.lock",
    "composer.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "yarn.lock",
}


def should_skip_repo_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if any(part in SKIP_DIRS for part in parts):
        return True
    return bool(parts and parts[-1] in SKIP_FILENAMES)


def filter_metrics_payload(metrics_payload: dict[str, Any]) -> dict[str, Any]:
    files = [
        item
        for item in metrics_payload.get("files", [])
        if not should_skip_repo_path(str(item.get("path", "")))
    ]
    file_paths = {item["path"] for item in files}

    duplication = dict(metrics_payload.get("duplication", {}))
    groups: list[dict[str, Any]] = []
    for group in duplication.get("groups", []):
        modules = [
            module
            for module in group.get("modules", [])
            if module.get("path") in file_paths
        ]
        if len(modules) < 2:
            continue
        next_group = dict(group)
        next_group["modules"] = modules
        next_group["occurrence_count"] = len(modules)
        groups.append(next_group)
    duplication["groups"] = groups
    duplication["group_count"] = len(groups)

    summary = dict(metrics_payload.get("summary", {}))
    summary["file_count"] = len(files)

    filtered = dict(metrics_payload)
    filtered["files"] = files
    filtered["duplication"] = duplication
    filtered["summary"] = summary
    return filtered


def load_metrics(root: Path, metrics_input: str | None) -> dict[str, Any]:
    if metrics_input:
        with open(metrics_input, "r", encoding="utf-8") as handle:
            return json.load(handle)

    script_dir = Path(__file__).resolve().parent
    command = [sys.executable, str(script_dir / "collect_repo_metrics.py"), "--root", str(root), "--pretty"]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "scripts/collect_repo_metrics.py failed while building refactor candidates:\n"
            + completed.stderr.strip()
        )
    return json.loads(completed.stdout)
