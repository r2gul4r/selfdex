"""File-record and symbol helpers for refactor candidate extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CODE_LANGUAGES = {"python", "shell", "powershell", "makefile", "rules", "toml"}

PYTHON_DEF_PATTERN = re.compile(r"^\s*(def|class)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b")
SHELL_DEF_PATTERN = re.compile(
    r"^\s*(?:function\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?:\(\))?\s*\{"
)
POWERSHELL_DEF_PATTERN = re.compile(r"^\s*function\s+(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\b", re.IGNORECASE)


@dataclass(frozen=True)
class SymbolLocation:
    name: str
    line: int
    symbol_kind: str


@dataclass(frozen=True)
class FileRecord:
    path: str
    language: str
    lines: list[str]
    definitions: list[SymbolLocation]


def read_text_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()


def extract_definitions(language: str, lines: list[str]) -> list[SymbolLocation]:
    definitions: list[SymbolLocation] = []
    if language == "python":
        for index, line in enumerate(lines, start=1):
            match = PYTHON_DEF_PATTERN.match(line)
            if not match:
                continue
            definitions.append(
                SymbolLocation(
                    name=match.group("name"),
                    line=index,
                    symbol_kind="class" if match.group(1) == "class" else "function",
                )
            )
        return definitions

    if language == "shell":
        for index, line in enumerate(lines, start=1):
            match = SHELL_DEF_PATTERN.match(line)
            if not match:
                continue
            definitions.append(SymbolLocation(name=match.group("name"), line=index, symbol_kind="function"))
        return definitions

    if language == "powershell":
        for index, line in enumerate(lines, start=1):
            match = POWERSHELL_DEF_PATTERN.match(line)
            if not match:
                continue
            definitions.append(SymbolLocation(name=match.group("name"), line=index, symbol_kind="function"))
        return definitions

    return definitions


def build_file_records(root: Path, metrics: dict[str, Any]) -> dict[str, FileRecord]:
    records: dict[str, FileRecord] = {}
    for item in metrics.get("files", []):
        path = item["path"]
        language = item["language"]
        if language not in CODE_LANGUAGES:
            continue
        lines = read_text_lines(root / path)
        records[path] = FileRecord(
            path=path,
            language=language,
            lines=lines,
            definitions=extract_definitions(language, lines),
        )
    return records


def find_enclosing_symbol(record: FileRecord, line_number: int) -> SymbolLocation | None:
    active: SymbolLocation | None = None
    for definition in record.definitions:
        if definition.line > line_number:
            break
        active = definition
    return active


def symbol_spans(record: FileRecord) -> list[tuple[SymbolLocation, int]]:
    spans: list[tuple[SymbolLocation, int]] = []
    total_lines = len(record.lines)
    for index, definition in enumerate(record.definitions):
        next_line = record.definitions[index + 1].line if index + 1 < len(record.definitions) else total_lines + 1
        spans.append((definition, max(next_line - definition.line, 1)))
    return sorted(spans, key=lambda item: (-item[1], item[0].line, item[0].name))
