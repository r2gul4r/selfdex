from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "normalize_quality_signals.py"
SPEC = importlib.util.spec_from_file_location("normalize_quality_signals", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
normalize_quality_signals = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = normalize_quality_signals
SPEC.loader.exec_module(normalize_quality_signals)


class NormalizeQualitySignalsTests(unittest.TestCase):
    def test_repo_metrics_normalization_keeps_quality_signal_shape(self) -> None:
        payload = {
            "schema_version": 1,
            "summary": {"file_count": 2},
            "files": [
                {
                    "path": "scripts/hotspot.py",
                    "language": "python",
                    "module_size": {
                        "bytes": 20000,
                        "code_lines": 500,
                        "max_line_length": 140,
                    },
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
                },
                {
                    "path": "README.md",
                    "language": "markdown",
                    "module_size": {"bytes": 100, "code_lines": 10, "max_line_length": 60},
                    "complexity": {
                        "max_indent_level": 1,
                        "cyclomatic_estimate": 1,
                        "decision_points": 0,
                        "function_like_blocks": 0,
                    },
                    "duplication": {
                        "group_count": 0,
                        "duplicated_line_instances": 0,
                        "max_duplicate_block_lines": 0,
                    },
                    "change_frequency": {
                        "commit_count": 0,
                        "commits_per_30_days": 0,
                        "author_count": 0,
                    },
                },
            ],
        }

        normalized = normalize_quality_signals.normalize_payload(payload)

        self.assertEqual(normalized["analysis_kind"], "repo_metrics")
        self.assertEqual(normalized["hotspots"][0]["path"], "scripts/hotspot.py")
        self.assertEqual(normalized["results"][0]["quality_signal"]["priority_rank"], 1)
        self.assertEqual(
            set(normalized["results"][0]["quality_signal"]["axis_breakdown"]),
            {
                "size_pressure",
                "complexity_pressure",
                "duplication_pressure",
                "change_pressure",
            },
        )
        self.assertEqual(len(normalized["results"][0]["quality_signal"]["top_signals"]), 3)
        self.assertIn("scripts/hotspot.py", normalized["hotspots"][0]["summary"])


if __name__ == "__main__":
    unittest.main()
