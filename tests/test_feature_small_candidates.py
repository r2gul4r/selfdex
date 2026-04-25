from __future__ import annotations

import unittest
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]


feature_small_candidates = load_script("feature_small_candidates.py")


def feature_group(
    *,
    key: str = "run_task",
    decision: str = "confirmed_gap",
    missing_tests: bool = True,
    related_paths: list[str] | None = None,
) -> dict[str, object]:
    paths = related_paths or ["scripts/tool.py"]
    return {
        "feature_key": key,
        "title": f"Root tooling / {key}",
        "candidate_count": 1,
        "signal_counts": {"not_implemented": 1},
        "related_paths": paths,
        "gap_assessment": {
            "decision": decision,
            "reasons": ["명시적인 미구현/누락 신호가 확인됨"],
            "score": 4 if decision == "confirmed_gap" else 2,
        },
        "evidence_bundle": {
            "related_file_paths": paths,
            "code_locations": [{"path": paths[0], "line": 4, "symbol_name": key, "symbol_kind": "function"}],
            "call_flow": {
                "status": "defined_only",
                "definition": {"path": paths[0], "line": 4},
                "callers": [],
            },
            "tests": {
                "missing_tests": missing_tests,
                "matched_test_files": [] if missing_tests else [{"path": "tests/test_tool.py"}],
            },
        },
    }


class FeatureSmallCandidateTests(unittest.TestCase):
    def test_build_small_feature_candidate_preserves_scoring_shape(self) -> None:
        candidate = feature_small_candidates.build_small_feature_candidate(
            "root_tooling",
            feature_group(),
        )

        self.assertEqual(candidate["candidate_kind"], "small_feature")
        self.assertEqual(candidate["decision"], "pick")
        self.assertEqual(candidate["priority_grade"], "A")
        self.assertEqual(candidate["priority_score"], 46)
        self.assertEqual(candidate["small_feature_rubric"]["specific_score"], 12)
        self.assertEqual(candidate["common_axes"]["goal_alignment"], "pass")
        self.assertIn("implementation_scope", candidate)
        self.assertIn("selection_rationale", candidate)

    def test_build_small_feature_candidates_filters_non_aligned_areas(self) -> None:
        areas = [
            {
                "area_id": "examples_and_snapshots",
                "feature_groups": [feature_group(key="demo", decision="likely_gap")],
            },
            {"area_id": "root_tooling", "feature_groups": [feature_group(key="tool")]},
        ]

        candidates = feature_small_candidates.build_small_feature_candidates(areas)

        self.assertEqual([candidate["linked_feature_key"] for candidate in candidates], ["tool"])

    def test_feature_extractor_reexports_moved_small_candidate_helpers(self) -> None:
        feature_gap = load_script("extract_feature_gap_candidates.py")

        self.assertEqual(feature_gap.build_small_feature_candidate.__name__, "build_small_feature_candidate")
        self.assertEqual(feature_gap.build_small_feature_candidates.__name__, "build_small_feature_candidates")
        self.assertEqual(feature_gap.determine_small_feature_decision.__name__, "determine_small_feature_decision")
        self.assertEqual(
            feature_gap.determine_small_feature_decision(
                {
                    "goal_alignment": "pass",
                    "gap_relevance": "high",
                    "safety": "safe",
                    "reversibility": "strong",
                    "structural_impact": "low",
                    "leverage": "high",
                },
                3,
                3,
                3,
                3,
                40,
            ),
            ("pick", "A"),
        )


if __name__ == "__main__":
    unittest.main()
