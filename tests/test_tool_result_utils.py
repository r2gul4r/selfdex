from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "tool_result_utils.py"
SPEC = importlib.util.spec_from_file_location("tool_result_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
tool_result_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool_result_utils
SPEC.loader.exec_module(tool_result_utils)


class ToolResultUtilsTests(unittest.TestCase):
    def test_parse_coverage_combines_line_and_branch_text(self) -> None:
        coverage = tool_result_utils.parse_coverage(
            {},
            "Lines: 80.0% (8/10)\nBranches: 50.0% (1/2)",
        )

        self.assertEqual(coverage["status"], "covered")
        self.assertEqual(coverage["percent"], 80.0)
        self.assertEqual(coverage["lines_covered"], 8)
        self.assertEqual(coverage["lines_total"], 10)
        self.assertEqual(coverage["branches_covered"], 1)
        self.assertEqual(coverage["branches_total"], 2)

    def test_normalize_result_detects_markdownlint_failure(self) -> None:
        normalized = tool_result_utils.normalize_result(
            {
                "command": "markdownlint README.md",
                "exit_code": 1,
                "stderr": "README.md:3 MD013/line-length Line length\n",
            }
        )

        self.assertEqual(normalized["tool"], "markdownlint")
        self.assertEqual(normalized["status"], "failed")
        self.assertEqual(normalized["failure_count"], 1)
        self.assertEqual(normalized["failures"][0]["path"], "README.md")
        self.assertEqual(normalized["failures"][0]["code"], "MD013/line-length")


if __name__ == "__main__":
    unittest.main()
