from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from repo_quality_signal_test_utils import repo_metrics_payload


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "normalize_quality_signals.py"
SPEC = importlib.util.spec_from_file_location("normalize_quality_signals", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
normalize_quality_signals = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = normalize_quality_signals
SPEC.loader.exec_module(normalize_quality_signals)


class NormalizeQualitySignalsTests(unittest.TestCase):
    def test_parse_coverage_preserves_explicit_coverage_payload(self) -> None:
        coverage = normalize_quality_signals.parse_coverage(
            {
                "coverage": {
                    "percent": "87.5",
                    "lines_covered": "7",
                    "lines_total": "8",
                    "raw": "",
                }
            },
            "",
        )

        self.assertEqual(coverage["percent"], 87.5)
        self.assertEqual(coverage["lines_covered"], 7)
        self.assertEqual(coverage["lines_total"], 8)
        self.assertIsNone(coverage["raw"])

    def test_parse_coverage_combines_line_and_branch_text(self) -> None:
        coverage = normalize_quality_signals.parse_coverage(
            {},
            "Lines: 80.0% (8/10)\nBranches: 50.0% (1/2)",
        )

        self.assertEqual(coverage["status"], "covered")
        self.assertEqual(coverage["percent"], 80.0)
        self.assertEqual(coverage["lines_covered"], 8)
        self.assertEqual(coverage["lines_total"], 10)
        self.assertEqual(coverage["branches_covered"], 1)
        self.assertEqual(coverage["branches_total"], 2)
        self.assertIn("Lines: 80.0%", coverage["raw"])
        self.assertIn("Branches: 50.0%", coverage["raw"])

    def test_repo_metrics_normalization_keeps_quality_signal_shape(self) -> None:
        normalized = normalize_quality_signals.normalize_payload(repo_metrics_payload())

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
