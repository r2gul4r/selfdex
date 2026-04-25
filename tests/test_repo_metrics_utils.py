from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from script_smoke_utils import run_script_and_module


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "repo_metrics_utils.py"
SPEC = importlib.util.spec_from_file_location("repo_metrics_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
repo_metrics_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = repo_metrics_utils
SPEC.loader.exec_module(repo_metrics_utils)


class RepoMetricsUtilsTests(unittest.TestCase):
    def test_analyze_python_file_counts_code_comments_and_complexity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script = root / "scripts" / "sample.py"
            script.parent.mkdir()
            script.write_text(
                "# module comment\n"
                "\n"
                "class Sample:\n"
                "    def run(self, value):\n"
                "        if value and value > 1:\n"
                "            return value\n",
                encoding="utf-8",
            )

            metrics = repo_metrics_utils.analyze_file(root, script)

        self.assertEqual(metrics.path, "scripts/sample.py")
        self.assertEqual(metrics.language, "python")
        self.assertEqual(metrics.total_lines, 6)
        self.assertEqual(metrics.blank_lines, 1)
        self.assertEqual(metrics.comment_lines, 1)
        self.assertEqual(metrics.code_lines, 4)
        self.assertEqual(metrics.function_like_blocks, 1)
        self.assertEqual(metrics.class_like_blocks, 1)
        self.assertGreaterEqual(metrics.decision_points, 2)
        self.assertEqual(metrics.cyclomatic_estimate, metrics.decision_points + 1)

    def test_markdown_block_comments_are_excluded_from_normalized_lines(self) -> None:
        lines = [
            "# Title",
            "<!--",
            "hidden duplicate",
            "-->",
            "Visible text",
        ]

        normalized = repo_metrics_utils.collect_normalized_code_lines("markdown", lines)

        self.assertEqual([item.original_line for item in normalized], [1, 5])
        self.assertEqual([item.normalized for item in normalized], ["# Title", "Visible text"])

    def test_file_metrics_to_dict_keeps_schema_shape(self) -> None:
        metrics = repo_metrics_utils.FileMetrics(
            path="README.md",
            language="markdown",
            bytes_size=10,
            total_lines=2,
            blank_lines=0,
            comment_lines=0,
            code_lines=2,
            max_line_length=7,
            function_like_blocks=0,
            class_like_blocks=0,
            decision_points=0,
            cyclomatic_estimate=1,
            max_indent_level=0,
            duplication_group_count=1,
            duplicated_line_instances=3,
            max_duplicate_block_lines=3,
            git_history=repo_metrics_utils.GitHistoryMetrics(commit_count=2),
        )

        payload = metrics.to_dict()

        self.assertEqual(payload["module_size"]["bytes"], 10)
        self.assertEqual(payload["complexity"]["cyclomatic_estimate"], 1)
        self.assertEqual(payload["duplication"]["group_count"], 1)
        self.assertEqual(payload["change_frequency"]["commit_count"], 2)

    def test_duplicate_group_to_dict_keeps_modules_shape(self) -> None:
        group = repo_metrics_utils.DuplicateGroup(
            fingerprint="abc123",
            normalized_line_count=3,
            token_count=9,
            occurrences=(
                repo_metrics_utils.DuplicateOccurrence(
                    path="a.py",
                    start_index=0,
                    line_count=3,
                    start_line=1,
                    end_line=3,
                ),
            ),
            excerpt_lines=("x = 1",),
        )

        payload = group.to_dict()

        self.assertEqual(payload["fingerprint"], "abc123")
        self.assertEqual(payload["occurrence_count"], 1)
        self.assertEqual(payload["modules"][0]["path"], "a.py")
        self.assertEqual(payload["excerpt"], ["x = 1"])

    def test_collect_repo_metrics_runs_as_script_and_module(self) -> None:
        script_output, module_output = run_script_and_module(
            repo_root=ROOT,
            script_name="collect_repo_metrics.py",
            module_name="collect_repo_metrics",
            args=[
                "--root",
                str(ROOT),
                "--paths",
                "scripts/collect_repo_metrics.py",
            ],
        )

        script_payload = json.loads(script_output.stdout)
        module_payload = json.loads(module_output.stdout)

        self.assertEqual(script_payload["schema_version"], 1)
        self.assertEqual(module_payload["schema_version"], 1)
        self.assertEqual(script_payload["files"][0]["path"], "scripts/collect_repo_metrics.py")
        self.assertEqual(module_payload["files"][0]["path"], "scripts/collect_repo_metrics.py")


if __name__ == "__main__":
    unittest.main()
