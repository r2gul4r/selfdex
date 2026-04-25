from __future__ import annotations

import unittest
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]


candidate_scoring_utils = load_script("candidate_scoring_utils.py")


class CandidateScoringUtilsTests(unittest.TestCase):
    def test_compute_common_score_uses_shared_axis_points(self) -> None:
        axes = {
            "goal_alignment": "pass",
            "gap_relevance": "high",
            "safety": "safe",
            "reversibility": "strong",
            "structural_impact": "low",
            "leverage": "high",
        }

        score = candidate_scoring_utils.compute_common_score(axes)

        self.assertEqual(score, 18)

    def test_grade_priority_thresholds_match_existing_extractors(self) -> None:
        self.assertEqual(candidate_scoring_utils.grade_priority(40), "A")
        self.assertEqual(candidate_scoring_utils.grade_priority(39), "B")
        self.assertEqual(candidate_scoring_utils.grade_priority(32), "B")
        self.assertEqual(candidate_scoring_utils.grade_priority(31), "C")
        self.assertEqual(candidate_scoring_utils.grade_priority(24), "C")
        self.assertEqual(candidate_scoring_utils.grade_priority(23), "D")

    def test_common_axis_decision_handles_shared_gate_outcomes(self) -> None:
        base_axes = {
            "goal_alignment": "pass",
            "gap_relevance": "high",
            "safety": "safe",
            "reversibility": "strong",
            "structural_impact": "low",
            "leverage": "high",
        }

        self.assertIsNone(candidate_scoring_utils.determine_common_axis_decision(base_axes))

        cases = [
            ("goal_alignment", "fail", ("reject", "hold")),
            ("gap_relevance", "low", ("defer", "hold")),
            ("safety", "risky", ("defer", "hold")),
            ("reversibility", "weak", ("defer", "hold")),
            ("structural_impact", "high", ("needs_approval", "hold")),
        ]
        for axis_name, axis_value, expected in cases:
            with self.subTest(axis_name=axis_name):
                axes = dict(base_axes)
                axes[axis_name] = axis_value
                self.assertEqual(candidate_scoring_utils.determine_common_axis_decision(axes), expected)

    def test_extractors_reexport_shared_helpers_for_compatibility(self) -> None:
        refactor = load_script("extract_refactor_candidates.py")
        feature_gap = load_script("extract_feature_gap_candidates.py")

        self.assertIs(refactor.compute_common_score, candidate_scoring_utils.compute_common_score)
        self.assertIs(feature_gap.compute_common_score, candidate_scoring_utils.compute_common_score)
        self.assertIs(refactor.grade_priority, candidate_scoring_utils.grade_priority)
        self.assertIs(feature_gap.grade_priority, candidate_scoring_utils.grade_priority)


if __name__ == "__main__":
    unittest.main()
