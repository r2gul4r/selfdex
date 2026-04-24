from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "repo_quality_signal_utils.py"
SPEC = importlib.util.spec_from_file_location("repo_quality_signal_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
repo_quality_signal_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = repo_quality_signal_utils
SPEC.loader.exec_module(repo_quality_signal_utils)


class RepoQualitySignalUtilsTests(unittest.TestCase):
    def test_metric_inputs_ignore_recent_rate_for_single_commit_files(self) -> None:
        inputs = repo_quality_signal_utils.build_repo_metric_inputs(
            {
                "module_size": {"code_lines": "20"},
                "complexity": {},
                "duplication": {},
                "change_frequency": {
                    "commit_count": "1",
                    "commits_per_30_days": "12.5",
                    "author_count": "1",
                },
            }
        )

        self.assertEqual(inputs["commit_count"], 1.0)
        self.assertEqual(inputs["commits_per_30_days"], 0.0)
        self.assertEqual(inputs["code_lines"], 20.0)

    def test_priority_grade_and_decision_boundaries(self) -> None:
        cases = [
            (40, "A", "prioritize"),
            (32, "B", "prioritize"),
            (24, "C", "monitor"),
            (23.99, "D", "low"),
        ]

        for score, grade, decision in cases:
            with self.subTest(score=score):
                self.assertEqual(repo_quality_signal_utils.grade_repo_priority(score), grade)
                self.assertEqual(repo_quality_signal_utils.repo_priority_decision(grade), decision)

    def test_normalize_repo_metric_file_builds_quality_signal_shape(self) -> None:
        item = {
            "path": "scripts/hotspot.py",
            "language": "python",
            "module_size": {"bytes": 20000, "code_lines": 500, "max_line_length": 140},
            "complexity": {
                "max_indent_level": 6,
                "cyclomatic_estimate": 50,
                "decision_points": 60,
                "function_like_blocks": 25,
            },
            "duplication": {
                "group_count": 4,
                "duplicated_line_instances": 60,
                "max_duplicate_block_lines": 12,
            },
            "change_frequency": {
                "commit_count": 4,
                "commits_per_30_days": 3.5,
                "author_count": 2,
            },
        }
        maxima = repo_quality_signal_utils.repo_metric_observed_maxima([item])

        normalized = repo_quality_signal_utils.normalize_repo_metric_file(item, maxima)

        self.assertEqual(normalized["path"], "scripts/hotspot.py")
        self.assertEqual(normalized["quality_signal"]["profile_version"], 1)
        self.assertIn(normalized["quality_signal"]["priority_grade"], {"A", "B", "C", "D"})
        self.assertEqual(len(normalized["quality_signal"]["top_signals"]), 3)
        self.assertIn("scripts/hotspot.py", normalized["quality_signal"]["summary"])


if __name__ == "__main__":
    unittest.main()
