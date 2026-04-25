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


def add_planner_argument(
    parser: argparse.ArgumentParser,
    *,
    required: bool = True,
    help_text: str = "Planner JSON payload path.",
) -> None:
    parser.add_argument("--planner", required=required, help=help_text)


def add_project_id_argument(
    parser: argparse.ArgumentParser,
    *,
    default: str = "selfdex",
    help_text: str = "Project id the planner payload represents. Defaults to selfdex.",
) -> None:
    parser.add_argument("--project-id", default=default, help=help_text)


def add_quality_argument(
    parser: argparse.ArgumentParser,
    *,
    help_text: str = "Optional candidate quality evaluation JSON payload path.",
) -> None:
    parser.add_argument("--quality", help=help_text)


def add_planner_report_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_root: bool = False,
    include_quality: bool = False,
) -> None:
    if include_root:
        add_root_argument(parser, help_text="Selfdex repository root.")
    add_planner_argument(parser)
    if include_quality:
        add_quality_argument(parser)
    add_project_id_argument(parser)
    add_format_argument(parser)


def parse_planner_report_args(
    description: str,
    argv: list[str] | None = None,
    *,
    include_root: bool = False,
    include_quality: bool = False,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    add_planner_report_arguments(parser, include_root=include_root, include_quality=include_quality)
    return parser.parse_args(argv)
