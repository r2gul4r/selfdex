from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any
import unittest


def symbol_tuples(items: Iterable[Any]) -> list[tuple[str, int, str]]:
    return [(item.name, item.line, item.symbol_kind) for item in items]


def assert_standard_symbol_definitions(
    test_case: unittest.TestCase,
    extract_definitions: Callable[[str, list[str]], Iterable[Any]],
) -> None:
    python_defs = extract_definitions(
        "python",
        [
            "class Alpha:",
            "    pass",
            "def run():",
            "    return 1",
        ],
    )
    shell_defs = extract_definitions(
        "shell",
        [
            "start_bridge() {",
            "  echo ok",
            "}",
        ],
    )
    powershell_defs = extract_definitions(
        "powershell",
        [
            "function Stop-Bridge {",
            "  Write-Output ok",
            "}",
        ],
    )

    test_case.assertEqual(
        symbol_tuples(python_defs),
        [("Alpha", 1, "class"), ("run", 3, "function")],
    )
    test_case.assertEqual(
        symbol_tuples(shell_defs),
        [("start_bridge", 1, "function")],
    )
    test_case.assertEqual(
        symbol_tuples(powershell_defs),
        [("Stop-Bridge", 1, "function")],
    )
