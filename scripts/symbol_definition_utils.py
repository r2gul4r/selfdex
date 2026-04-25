"""Shared symbol definition extraction helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass


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


def extract_definitions(language: str, lines: list[str]) -> list[SymbolLocation]:
    definitions: list[SymbolLocation] = []
    if language == "python":
        symbol_map = {"def": "function", "class": "class"}
        for index, line in enumerate(lines, start=1):
            match = PYTHON_DEF_PATTERN.match(line)
            if not match:
                continue
            definitions.append(
                SymbolLocation(
                    name=match.group("name"),
                    line=index,
                    symbol_kind=symbol_map.get(match.group(1), "symbol"),
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
