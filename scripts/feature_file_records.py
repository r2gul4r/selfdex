"""File-record and symbol helpers for feature-gap candidate extraction."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from repo_scan_excludes import DEFAULT_SCAN_EXCLUDED_DIRS, path_has_excluded_dir
except ModuleNotFoundError:
    from scripts.repo_scan_excludes import DEFAULT_SCAN_EXCLUDED_DIRS, path_has_excluded_dir

try:
    from symbol_definition_utils import SymbolLocation, extract_definitions
except ModuleNotFoundError:
    from scripts.symbol_definition_utils import SymbolLocation, extract_definitions


MAX_FILE_BYTES = 512 * 1024
TEXT_SAMPLE_BYTES = 4096
SKIP_DIRS = set(DEFAULT_SCAN_EXCLUDED_DIRS)
SCAN_SUFFIXES = {".py", ".sh", ".ps1", ".toml", ".rules"}
SKIP_FILENAMES = {"STATE.md", "MULTI_AGENT_LOG.md", "ERROR_LOG.md"}
SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
}
TEST_FILE_PATTERN = re.compile(r"(?i)(^test_|_test\.|tests?/)")


@dataclass(frozen=True)
class FileRecord:
    path: Path
    relative_path: str
    lines: list[str]
    content: str
    language: str
    is_test_file: bool
    definitions: list[SymbolLocation]


def infer_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix == ".sh":
        return "shell"
    if suffix == ".ps1":
        return "powershell"
    if suffix == ".toml":
        return "toml"
    if suffix == ".rules":
        return "rules"
    return "text"


def iter_repo_files(root: Path, *, exclude_filename: str | None = None) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path_has_excluded_dir(path, root=root, excluded_dirs=SKIP_DIRS):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.name in SKIP_FILENAMES:
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if exclude_filename and path.name == exclude_filename:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        if is_text_file(path):
            files.append(path)
    return sorted(files)


def is_text_file(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:TEXT_SAMPLE_BYTES]
    except OSError:
        return False
    if b"\x00" in sample:
        return False
    return True


def read_text_lines(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    return text.splitlines()


def normalize_excerpt(text: str) -> str:
    return " ".join(text.strip().split())


def is_test_file(path: Path) -> bool:
    return bool(TEST_FILE_PATTERN.search(path.as_posix()))


def build_file_record(root: Path, path: Path) -> FileRecord:
    lines = read_text_lines(path)
    language = infer_language(path)
    content = "\n".join(lines)
    relative_path = path.relative_to(root).as_posix()
    return FileRecord(
        path=path,
        relative_path=relative_path,
        lines=lines,
        content=content,
        language=language,
        is_test_file=is_test_file(path.relative_to(root)),
        definitions=extract_definitions(language, lines),
    )


def build_repo_index(root: Path, files: list[Path]) -> dict[str, Any]:
    records = [build_file_record(root, path) for path in files]
    by_relative_path = {record.relative_path: record for record in records}
    return {
        "records": records,
        "by_relative_path": by_relative_path,
        "test_records": [record for record in records if record.is_test_file],
    }


def find_enclosing_symbol(record: FileRecord, line_number: int) -> SymbolLocation | None:
    candidates = [definition for definition in record.definitions if definition.line <= line_number]
    if not candidates:
        return None
    return candidates[-1]
