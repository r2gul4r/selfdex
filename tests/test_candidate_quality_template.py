from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "prepare_candidate_quality_template.py"
SPEC = importlib.util.spec_from_file_location("prepare_candidate_quality_template", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
prepare_candidate_quality_template = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare_candidate_quality_template
SPEC.loader.exec_module(prepare_candidate_quality_template)


PLANNER_PAYLOAD = {
    "schema_version": 1,
    "analysis_kind": "selfdex_next_task_plan",
    "top_candidates": [
        {
            "source": "refactor",
            "title": "split candidate extraction helpers",
            "rationale": ["Large file with duplicated logic."],
            "suggested_checks": ["python -m compileall -q scripts"],
        },
        {
            "source": "test_gap",
            "title": "add parser fixture coverage",
            "rationale": ["Parser edge case has no focused test."],
            "suggested_checks": ["python -m unittest discover -s tests"],
        },
    ],
}


EXTERNAL_SNAPSHOT_PAYLOAD = {
    "schema_version": 1,
    "analysis_kind": "selfdex_external_candidate_snapshot",
    "projects": [
        {
            "project_id": "external_one",
            "top_candidates": [
                {
                    "source": "refactor",
                    "title": "split external duplicate block",
                    "rationale": ["External duplicate evidence."],
                    "suggested_checks": ["npm test"],
                }
            ],
        },
        {
            "project_id": "external_two",
            "top_candidates": [
                {
                    "source": "test_gap",
                    "title": "add external smoke test",
                    "rationale": ["External test evidence."],
                    "suggested_checks": ["pytest"],
                }
            ],
        },
    ],
}


class CandidateQualityTemplateTests(unittest.TestCase):
    def test_build_template_from_top_candidates(self) -> None:
        payload = prepare_candidate_quality_template.build_template(
            PLANNER_PAYLOAD,
            "external_one",
        )

        first = payload["candidates"][0]

        self.assertEqual(payload["analysis_kind"], "candidate_quality_template")
        self.assertEqual(payload["candidate_count"], 2)
        self.assertEqual(first["source_project"], "external_one")
        self.assertEqual(first["scores"]["real_problem"], None)
        self.assertEqual(first["score_status"], "needs_human_scoring")
        self.assertEqual(first["suggested_verification"], "python -m compileall -q scripts")

    def test_uses_selected_when_top_candidates_missing(self) -> None:
        payload = prepare_candidate_quality_template.build_template(
            {
                "selected": {
                    "source": "refactor",
                    "title": "split selected helper",
                    "rationale": ["Selected candidate evidence."],
                    "suggested_checks": ["python -m compileall -q scripts"],
                }
            },
            "selfdex",
        )

        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["candidates"][0]["candidate"], "split selected helper")

    def test_build_template_flattens_external_snapshot_candidates(self) -> None:
        payload = prepare_candidate_quality_template.build_template(
            EXTERNAL_SNAPSHOT_PAYLOAD,
            "fallback_project",
        )

        self.assertEqual(payload["candidate_count"], 2)
        self.assertEqual(
            [candidate["source_project"] for candidate in payload["candidates"]],
            ["external_one", "external_two"],
        )
        self.assertEqual(payload["candidates"][0]["candidate"], "split external duplicate block")
        self.assertEqual(payload["candidates"][0]["scores"]["user_value"], None)
        self.assertEqual(payload["candidates"][0]["score_status"], "needs_human_scoring")

    def test_markdown_lists_dimensions_and_candidates(self) -> None:
        payload = prepare_candidate_quality_template.build_template(
            PLANNER_PAYLOAD,
            "external_one",
        )

        markdown = prepare_candidate_quality_template.render_markdown(payload)

        self.assertIn("# Candidate Quality Scoring Template", markdown)
        self.assertIn("`real_problem`: fill with `0-3`", markdown)
        self.assertIn("split candidate extraction helpers", markdown)


if __name__ == "__main__":
    unittest.main()
