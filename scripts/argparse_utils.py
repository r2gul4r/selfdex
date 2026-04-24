"""Shared argparse option helpers for Selfdex command-line scripts."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def add_root_argument(
    parser: argparse.ArgumentParser,
    *,
    default: str = ".",
    help_text: str = "Repository root.",
) -> None:
    parser.add_argument("--root", default=default, help=help_text)


def add_format_argument(
    parser: argparse.ArgumentParser,
    *,
    choices: Sequence[str] = ("json", "markdown"),
    default: str = "json",
    help_text: str = "Output format. Defaults to json.",
) -> None:
    parser.add_argument("--format", choices=tuple(choices), default=default, help=help_text)


def add_pretty_argument(
    parser: argparse.ArgumentParser,
    *,
    help_text: str = "Pretty-print JSON output.",
) -> None:
    parser.add_argument("--pretty", action="store_true", help=help_text)
