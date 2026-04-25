from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from script_loader_utils import load_script


coverage_signal = load_script("check_coverage_signal.py")


class CoverageSignalTests(unittest.TestCase):
    def test_build_payload_normalizes_raw_tool_results(self) -> None:
        payload = {
            "results": [
                {
                    "tool": "pytest",
                    "command": "pytest --cov=tests",
                    "exit_code": 0,
                    "stdout": "Lines: 80.0% (8/10)\nBranches: 50.0% (1/2)",
                    "stderr": "",
                }
            ]
        }

        result = coverage_signal.build_payload(
            payload,
            input_path="sample.json",
            minimum_tools=1,
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["input_payload_kind"], "raw_tool_results")
        self.assertEqual(result["coverage_tool_count"], 1)
        self.assertEqual(result["coverage_tools"], ["pytest"])
        self.assertEqual(result["issues"], [])

    def test_build_payload_consumes_normalized_tool_results(self) -> None:
        payload = {
            "schema_version": 1,
            "analysis_kind": "tool_results",
            "result_count": 1,
            "coverage_tool_count": 1,
            "coverage_tools": ["pytest"],
            "results": [],
        }

        with patch.object(coverage_signal, "normalize_payload", side_effect=AssertionError):
            result = coverage_signal.build_payload(
                payload,
                input_path="normalized.json",
                minimum_tools=1,
            )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["input_payload_kind"], "normalized_tool_results")
        self.assertEqual(result["normalized_analysis_kind"], "tool_results")
        self.assertEqual(result["coverage_tools"], ["pytest"])

    def test_build_payload_fails_without_coverage_tool(self) -> None:
        payload = {
            "schema_version": 1,
            "analysis_kind": "tool_results",
            "result_count": 1,
            "coverage_tool_count": 0,
            "coverage_tools": [],
            "results": [
                {
                    "tool": "unittest",
                    "command": "python -m unittest discover -s tests",
                    "exit_code": 0,
                    "stdout": "OK",
                    "stderr": "",
                }
            ]
        }

        result = coverage_signal.build_payload(
            payload,
            input_path="sample.json",
            minimum_tools=1,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["input_payload_kind"], "normalized_tool_results")
        self.assertEqual(result["coverage_tool_count"], 0)
        self.assertEqual(result["issues"][0]["code"], "coverage_signal_missing")

    def test_build_payload_rejects_invalid_minimum(self) -> None:
        result = coverage_signal.build_payload(
            {"results": []},
            input_path="sample.json",
            minimum_tools=0,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["issues"][0]["code"], "invalid_minimum_tools")

    def test_render_markdown_reports_status_and_count(self) -> None:
        payload = {
            "status": "passed",
            "input_path": "sample.json",
            "input_payload_kind": "normalized_tool_results",
            "minimum_tools": 1,
            "coverage_tool_count": 1,
            "coverage_tools": ["pytest"],
            "issues": [],
        }

        output = coverage_signal.render_markdown(payload)

        self.assertIn("- status: `passed`", output)
        self.assertIn("- coverage_tool_count: `1`", output)
        self.assertIn("- coverage_tools: `pytest`", output)

    def test_main_returns_failure_for_missing_coverage(self) -> None:
        output = io.StringIO()
        with patch.object(
            coverage_signal,
            "load_payload",
            return_value={"results": [{"tool": "unittest", "exit_code": 0, "stdout": "OK"}]},
        ):
            with redirect_stdout(output):
                exit_code = coverage_signal.main(["--input", "sample.json", "--format", "json"])

        self.assertEqual(exit_code, 1)
        self.assertIn('"status": "failed"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
