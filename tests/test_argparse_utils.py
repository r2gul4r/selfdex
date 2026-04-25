from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "argparse_utils.py"
SPEC = importlib.util.spec_from_file_location("argparse_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
argparse_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = argparse_utils
SPEC.loader.exec_module(argparse_utils)


class ArgparseUtilsTests(unittest.TestCase):
    def build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        argparse_utils.add_root_argument(parser, help_text="Root")
        argparse_utils.add_format_argument(parser)
        argparse_utils.add_pretty_argument(parser)
        return parser

    def test_common_arguments_keep_existing_defaults(self) -> None:
        args = self.build_parser().parse_args([])

        self.assertEqual(args.root, ".")
        self.assertEqual(args.format, "json")
        self.assertFalse(args.pretty)

    def test_common_arguments_parse_explicit_values(self) -> None:
        args = self.build_parser().parse_args(
            ["--root", "sample", "--format", "markdown", "--pretty"]
        )

        self.assertEqual(args.root, "sample")
        self.assertEqual(args.format, "markdown")
        self.assertTrue(args.pretty)

    def test_format_argument_allows_default_override(self) -> None:
        parser = argparse.ArgumentParser()
        argparse_utils.add_format_argument(parser, default="markdown")

        args = parser.parse_args([])

        self.assertEqual(args.format, "markdown")

    def test_validation_arguments_keep_existing_defaults(self) -> None:
        parser = argparse.ArgumentParser()
        argparse_utils.add_planner_argument(parser)
        argparse_utils.add_project_id_argument(parser)
        argparse_utils.add_format_argument(parser)

        args = parser.parse_args(["--planner", "planner.json"])

        self.assertEqual(args.planner, "planner.json")
        self.assertEqual(args.project_id, "selfdex")
        self.assertEqual(args.format, "json")

    def test_validation_arguments_parse_explicit_values(self) -> None:
        parser = argparse.ArgumentParser()
        argparse_utils.add_planner_argument(parser)
        argparse_utils.add_project_id_argument(parser)
        argparse_utils.add_format_argument(parser)

        args = parser.parse_args(
            [
                "--planner",
                "planner.json",
                "--project-id",
                "external_one",
                "--format",
                "markdown",
            ]
        )

        self.assertEqual(args.planner, "planner.json")
        self.assertEqual(args.project_id, "external_one")
        self.assertEqual(args.format, "markdown")

    def test_planner_report_arguments_keep_template_defaults(self) -> None:
        parser = argparse.ArgumentParser()
        argparse_utils.add_planner_report_arguments(parser)

        args = parser.parse_args(["--planner", "planner.json"])

        self.assertEqual(args.planner, "planner.json")
        self.assertEqual(args.project_id, "selfdex")
        self.assertEqual(args.format, "json")
        self.assertFalse(hasattr(args, "root"))
        self.assertFalse(hasattr(args, "quality"))

    def test_planner_report_arguments_can_include_root_and_quality(self) -> None:
        parser = argparse.ArgumentParser()
        argparse_utils.add_planner_report_arguments(parser, include_root=True, include_quality=True)

        args = parser.parse_args(
            [
                "--root",
                ".",
                "--planner",
                "planner.json",
                "--quality",
                "quality.json",
                "--project-id",
                "external_one",
                "--format",
                "markdown",
            ]
        )

        self.assertEqual(args.root, ".")
        self.assertEqual(args.planner, "planner.json")
        self.assertEqual(args.quality, "quality.json")
        self.assertEqual(args.project_id, "external_one")
        self.assertEqual(args.format, "markdown")

    def test_parse_planner_report_args_wraps_parser_creation(self) -> None:
        args = argparse_utils.parse_planner_report_args(
            "Report",
            [
                "--planner",
                "planner.json",
                "--project-id",
                "external_one",
                "--format",
                "markdown",
            ],
        )

        self.assertEqual(args.planner, "planner.json")
        self.assertEqual(args.project_id, "external_one")
        self.assertEqual(args.format, "markdown")


if __name__ == "__main__":
    unittest.main()
