"""Shared directory exclusions for repository scanners."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator


DEFAULT_SCAN_EXCLUDED_DIRS = frozenset(
    {
        ".codex",
        ".codex-backups",
        ".git",
        ".gradle",
        ".local",
        ".mypy_cache",
        ".next",
        ".nuxt",
        ".playwright-cli",
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
        "out",
        "target",
        "test-results",
        "tmp",
        "venv",
    }
)


def parts_include_excluded_dir(
    parts: Iterable[str],
    excluded_dirs: Iterable[str] = DEFAULT_SCAN_EXCLUDED_DIRS,
) -> bool:
    excluded = set(excluded_dirs)
    return any(part in excluded for part in parts)


def is_excluded_dir_name(
    name: str,
    excluded_dirs: Iterable[str] = DEFAULT_SCAN_EXCLUDED_DIRS,
) -> bool:
    return name in set(excluded_dirs)


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


def iter_pruned_files(
    root: Path,
    *,
    excluded_dirs: Iterable[str] = DEFAULT_SCAN_EXCLUDED_DIRS,
) -> Iterator[Path]:
    """Yield files while pruning generated directories before descent."""

    excluded = set(excluded_dirs)
    stack = [Path(root)]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda item: item.name.lower())
        except OSError:
            continue

        directories: list[Path] = []
        for entry in entries:
            try:
                if entry.is_dir():
                    if not is_excluded_dir_name(entry.name, excluded):
                        directories.append(entry)
                    continue
                if entry.is_file():
                    yield entry
            except OSError:
                continue

        stack.extend(reversed(directories))
