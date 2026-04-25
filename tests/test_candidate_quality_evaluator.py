from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_candidate_quality.py"
SPEC = importlib.util.spec_from_file_location("evaluate_candidate_quality", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
evaluate_candidate_quality = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = evaluate_candidate_quality
SPEC.loader.exec_module(evaluate_candidate_quality)


def candidate(**scores: int) -> dict[str, object]:
    return {
        "candidate": "tighten external validation report",
        "source_project": "selfdex",
        "source_signal": "roadmap",
        "evidence": "external read-only validation needs a scoring record",
        "suggested_verification": "python scripts/evaluate_candidate_quality.py --format json",
        "scores": scores,
    }


class CandidateQualityEvaluatorTests(unittest.TestCase):
    def test_scores_strong_candidate(self) -> None:
        payload = evaluate_candidate_quality.evaluate_payload(
            candidate(
                real_problem=3,
                user_value=3,
                local_verifiability=3,
                scope_smallness=2,
                risk_reversibility=3,
            )
        )

        result = payload["results"][0]

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(result["total"], 14)
        self.assertEqual(result["verdict"], "strong")

    def test_scores_usable_candidate(self) -> None:
        payload = evaluate_candidate_quality.evaluate_payload(
            candidate(
                real_problem=2,
                user_value=1,
                local_verifiability=2,
                scope_smallness=2,
                risk_reversibility=2,
            )
        )

        self.assertEqual(payload["results"][0]["total"], 9)
        self.assertEqual(payload["results"][0]["verdict"], "usable")

    def test_defers_low_value_candidate(self) -> None:
        payload = evaluate_candidate_quality.evaluate_payload(
            candidate(
                real_problem=2,
                user_value=0,
                local_verifiability=3,
                scope_smallness=3,
                risk_reversibility=3,
            )
        )

        self.assertEqual(payload["results"][0]["verdict"], "defer")

    def test_splits_candidate_with_large_scope(self) -> None:
        payload = evaluate_candidate_quality.evaluate_payload(
            candidate(
                real_problem=3,
                user_value=3,
                local_verifiability=3,
                scope_smallness=1,
                risk_reversibility=3,
            )
        )

        self.assertEqual(payload["results"][0]["verdict"], "split")

    def test_accepts_candidates_array_payload(self) -> None:
        payload = evaluate_candidate_quality.evaluate_payload(
            {
                "candidates": [
                    candidate(
                        real_problem=3,
                        user_value=3,
                        local_verifiability=3,
                        scope_smallness=3,
                        risk_reversibility=3,
                    ),
                    candidate(
                        real_problem=1,
                        user_value=1,
                        local_verifiability=1,
                        scope_smallness=1,
                        risk_reversibility=1,
                    ),
                ]
            }
        )

        self.assertEqual(payload["candidate_count"], 2)
        self.assertEqual(payload["verdict_counts"]["strong"], 1)
        self.assertEqual(payload["verdict_counts"]["split"], 1)

    def test_rejects_invalid_scores(self) -> None:
        payload = evaluate_candidate_quality.evaluate_payload(
            candidate(
                real_problem=4,
                user_value=3,
                local_verifiability=3,
                scope_smallness=3,
                risk_reversibility=3,
            )
        )

        result = payload["results"][0]

        self.assertEqual(payload["status"], "fail")
        self.assertEqual(result["verdict"], "invalid")
        self.assertIn("real_problem must be between 0 and 3", result["issues"])

    def test_markdown_renders_verdicts(self) -> None:
        payload = evaluate_candidate_quality.evaluate_payload(
            candidate(
                real_problem=3,
                user_value=3,
                local_verifiability=3,
                scope_smallness=3,
                risk_reversibility=3,
            )
        )

        markdown = evaluate_candidate_quality.render_markdown(payload)

        self.assertIn("# Candidate Quality Evaluation", markdown)
        self.assertIn("- strong: `1`", markdown)
        self.assertIn("tighten external validation report", markdown)

    def test_load_payload_accepts_stdin_bom(self) -> None:
        raw = json.dumps(
            candidate(
                real_problem=3,
                user_value=3,
                local_verifiability=3,
                scope_smallness=3,
                risk_reversibility=3,
            )
        )

        with patch("sys.stdin") as stdin:
            stdin.read.return_value = "\ufeff" + raw
            payload = evaluate_candidate_quality.load_payload(None)

        self.assertEqual(payload["candidate"], "tighten external validation report")


if __name__ == "__main__":
    unittest.main()
