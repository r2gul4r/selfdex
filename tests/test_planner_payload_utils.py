from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "planner_payload_utils.py"
SPEC = importlib.util.spec_from_file_location("planner_payload_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
planner_payload_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = planner_payload_utils
SPEC.loader.exec_module(planner_payload_utils)


class PlannerPayloadUtilsTests(unittest.TestCase):
    def test_load_json_reads_utf8_sig_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "planner.json"
            path.write_text("\ufeff" + json.dumps({"selected": {"title": "task"}}), encoding="utf-8")

            payload = planner_payload_utils.load_json(path)

        self.assertEqual(payload["selected"]["title"], "task")

    def test_planner_candidates_prefers_top_candidates(self) -> None:
        payload = {
            "top_candidates": [
                {"title": "first"},
                "ignored",
                {"title": "second"},
            ],
            "selected": {"title": "selected"},
        }

        candidates = planner_payload_utils.planner_candidates(payload)

        self.assertEqual([candidate["title"] for candidate in candidates], ["first", "second"])

    def test_planner_candidates_falls_back_to_selected(self) -> None:
        candidates = planner_payload_utils.planner_candidates({"selected": {"title": "selected"}})

        self.assertEqual(candidates, [{"title": "selected"}])

    def test_planner_candidates_flattens_external_snapshot_candidates(self) -> None:
        payload = {
            "analysis_kind": "selfdex_external_candidate_snapshot",
            "projects": [
                {
                    "project_id": "external_one",
                    "top_candidates": [{"title": "first", "source": "refactor"}],
                },
                {
                    "project_id": "external_two",
                    "top_candidates": [{"title": "second", "source": "test_gap"}],
                },
            ],
        }

        candidates = planner_payload_utils.planner_candidates(payload)

        self.assertEqual([candidate["title"] for candidate in candidates], ["first", "second"])
        self.assertEqual(
            [candidate["source_project"] for candidate in candidates],
            ["external_one", "external_two"],
        )

    def test_planner_candidates_returns_empty_for_missing_candidates(self) -> None:
        self.assertEqual(planner_payload_utils.planner_candidates({}), [])


if __name__ == "__main__":
    unittest.main()
