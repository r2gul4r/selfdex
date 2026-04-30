"""Evidence collection helpers for project direction inference."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from repo_scan_excludes import path_has_excluded_dir
except ModuleNotFoundError:
    from scripts.repo_scan_excludes import path_has_excluded_dir


MAX_TEXT_BYTES = 80_000
MAX_DOC_FILES = 12
MAX_REPO_FILES = 1_500
TEXT_SUFFIXES = {
    ".css",
    ".gradle",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".py",
    ".rs",
    ".sql",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}
LOCAL_ARTIFACT_DIRS = {"runs"}
KEY_DOC_NAMES = {
    "agents.md",
    "autopilot.md",
    "project_harness.md",
    "readme.md",
    "state.md",
}


def safe_read_text(path: Path, max_bytes: int = MAX_TEXT_BYTES) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
    except OSError:
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if len(files) >= MAX_REPO_FILES:
            break
        if path_has_excluded_dir(path, root=root):
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = path.parts
        if any(part in LOCAL_ARTIFACT_DIRS for part in relative_parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def pick_doc_files(root: Path, files: list[Path]) -> list[Path]:
    docs = [
        path
        for path in files
        if path.suffix.lower() in {".md", ".txt"} and (path.name.lower() in KEY_DOC_NAMES or "docs" in path.parts)
    ]
    return sorted(docs, key=lambda path: (0 if path.name.lower() == "readme.md" else 1, len(path.parts), rel_path(root, path)))[
        :MAX_DOC_FILES
    ]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def first_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().strip("-*`")
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        if len(stripped) >= 24:
            return normalize_space(stripped)[:180]
    return ""


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def paths_matching(files: list[Path], root: Path, *patterns: str) -> list[str]:
    lowered_patterns = tuple(pattern.lower() for pattern in patterns)
    matches = []
    for path in files:
        relative = rel_path(root, path)
        lowered = relative.lower()
        if any(pattern in lowered for pattern in lowered_patterns):
            matches.append(relative)
    return matches[:5]


def evidence_objects(
    paths: list[str],
    *,
    signal_text: str,
    confidence: str = "medium",
    quote_map: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    quotes = quote_map or {}
    return [
        {
            "path": path,
            "signal": signal_text,
            "quote": quotes.get(path, ""),
            "confidence": confidence,
        }
        for path in paths[:5]
    ]


def signal(
    label: str,
    summary: str,
    paths: list[str],
    confidence: str = "medium",
    quote_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "label": label,
        "summary": summary,
        "confidence": confidence,
        "evidence_paths": paths[:5],
        "evidence": evidence_objects(paths, signal_text=summary, confidence=confidence, quote_map=quote_map),
    }


def quote_map_from_docs(root: Path, docs: list[tuple[Path, str]]) -> dict[str, str]:
    quotes: dict[str, str] = {}
    for path, text in docs:
        quote = first_meaningful_line(text) or first_heading(text)
        if quote:
            quotes[rel_path(root, path)] = quote
    return quotes
