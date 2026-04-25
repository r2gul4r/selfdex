"""Shared directory exclusions for repository scanners."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


DEFAULT_SCAN_EXCLUDED_DIRS = frozenset(
    {
        ".codex",
        ".codex-backups",
        ".git",
        ".mypy_cache",
        ".next",
        ".nuxt",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "env",
        "node_modules",
        "venv",
    }
)


def parts_include_excluded_dir(
    parts: Iterable[str],
    excluded_dirs: Iterable[str] = DEFAULT_SCAN_EXCLUDED_DIRS,
) -> bool:
    excluded = set(excluded_dirs)
    return any(part in excluded for part in parts)


def path_has_excluded_dir(
    path: Path,
    *,
    root: Path | None = None,
    excluded_dirs: Iterable[str] = DEFAULT_SCAN_EXCLUDED_DIRS,
) -> bool:
    if root is not None:
        try:
            path = path.resolve().relative_to(root.resolve())
        except (OSError, ValueError):
            pass
    return parts_include_excluded_dir(path.parts, excluded_dirs)
