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


if __name__ == "__main__":
    unittest.main()
