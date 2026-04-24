from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_next_task.py"
SPEC = importlib.util.spec_from_file_location("plan_next_task", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
plan_next_task = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = plan_next_task
SPEC.loader.exec_module(plan_next_task)


def write_campaign(root: Path, goal: str, queue_items: list[str]) -> None:
    queue = "\n".join(f"- {item}" for item in queue_items)
    (root / "CAMPAIGN_STATE.md").write_text(
        f"""# Campaign State

## Campaign

- name: `test`
- goal: `{goal}`

## Candidate Queue

{queue}

## Latest Run

- status: `test`
""",
        encoding="utf-8",
    )


def write_extractor(root: Path, name: str, payload: dict[str, Any]) -> None:
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    (scripts_dir / name).write_text(
        "import json\n"
        f"print(json.dumps({payload!r}, ensure_ascii=False))\n",
        encoding="utf-8",
    )


def write_extractors(
    root: Path,
    *,
    test_payload: dict[str, Any] | None = None,
    refactor_payload: dict[str, Any] | None = None,
    feature_payload: dict[str, Any] | None = None,
) -> None:
    write_extractor(root, "extract_test_gap_candidates.py", test_payload or {"findings": []})
    write_extractor(
        root,
        "extract_refactor_candidates.py",
        refactor_payload or {"refactor_candidates": []},
    )
    write_extractor(
        root,
        "extract_feature_gap_candidates.py",
        feature_payload or {"small_feature_candidates": []},
    )


class PlanNextTaskTests(unittest.TestCase):
    def test_parses_campaign_goal_and_queue_items(self) -> None:
        text = """# Campaign State

## Campaign

- name: `demo`
- goal: `Build a planner that can plan and record work.`

## Candidate Queue

- Add real unit tests for `scripts/plan_next_task.py`.
- Add a run recorder.

## Latest Run

- status: `ok`
"""

        self.assertEqual(
            plan_next_task.parse_campaign_goal(text),
            "Build a planner that can plan and record work.",
        )
        self.assertEqual(
            plan_next_task.parse_campaign_queue(text),
            [
                "Add real unit tests for scripts/plan_next_task.py.",
                "Add a run recorder.",
            ],
        )

    def test_campaign_queue_candidate_beats_imported_refactor_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(
                root,
                "Build a harness that can plan and verify work.",
                ["Add real unit tests for `scripts/plan_next_task.py`."],
            )
            write_extractors(
                root,
                refactor_payload={
                    "refactor_candidates": [
                        {
                            "title": "Refactor imported script",
                            "decision": "pick",
                            "priority_score": 47,
                            "selection_rationale": ["scan-based hotspot"],
                        }
                    ]
                },
            )

            payload = plan_next_task.choose_candidate(root)

        self.assertEqual(payload["campaign_queue_candidate_count"], 1)
        self.assertEqual(payload["selected"]["source"], "campaign_queue")
        self.assertEqual(
            payload["selected"]["title"],
            "Add real unit tests for scripts/plan_next_task.py.",
        )

    def test_campaign_goal_match_bonus_can_change_queue_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(
                root,
                "Build a harness that can record repository improvements.",
                ["Add general guard checks.", "Add record run file."],
            )
            write_extractors(root)

            payload = plan_next_task.choose_candidate(root)

        self.assertEqual(payload["selected"]["source"], "campaign_queue")
        self.assertEqual(payload["selected"]["title"], "Add record run file.")
        self.assertGreater(
            payload["top_candidates"][0]["priority_score"],
            payload["top_candidates"][1]["priority_score"],
        )

    def test_json_payload_and_markdown_render_campaign_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(
                root,
                "Build a harness that can plan repository improvements.",
                ["Add planner tests."],
            )
            write_extractors(root)

            payload = plan_next_task.choose_candidate(root)
            markdown = plan_next_task.render_markdown(payload)

        self.assertEqual(payload["selected"]["source"], "campaign_queue")
        self.assertEqual(payload["selected"]["work_type"], "hardening")
        self.assertIn("- source: `campaign_queue`", markdown)
        self.assertIn("- work_type: `hardening`", markdown)
        self.assertIn("campaign_queue [hardening]: Add planner tests.", markdown)

    def test_socratic_evaluation_is_in_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(
                root,
                "Build a harness that can classify and verify candidates.",
                ["Add classify candidate checks."],
            )
            write_extractors(root)

            payload = plan_next_task.choose_candidate(root)
            markdown = plan_next_task.render_markdown(payload)

        evaluation = payload["selected"]["socratic_evaluation"]
        self.assertGreaterEqual(len(evaluation), 6)
        self.assertEqual(
            evaluation[0]["question"],
            "Does this serve the current campaign goal?",
        )
        self.assertIn("classify", evaluation[0]["answer"])
        self.assertIn("## Socratic Evaluation", markdown)
        self.assertIn("What kind of work is this?", markdown)

    def test_recommended_topology_records_spawn_decision_and_write_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(
                root,
                "Build a harness that can orchestrate and record work.",
                ["Add an orchestration planner that records spawn decisions."],
            )
            write_extractors(root)

            payload = plan_next_task.choose_candidate(root)
            markdown = plan_next_task.render_markdown(payload)

        topology = payload["recommended_topology"]
        self.assertEqual(
            topology["spawn_decision"],
            "spawn_worthy_when_write_sets_are_disjoint",
        )
        self.assertIn("main: freeze contract and own integration", topology["write_sets"])
        self.assertIn("- spawn_decision: `spawn_worthy_when_write_sets_are_disjoint`", markdown)
        self.assertIn("## Write Sets", markdown)

    def test_campaign_titles_are_classified_by_work_type(self) -> None:
        cases = {
            "Fix broken scan fallback.": "repair",
            "Add fixture-based tests for candidate extractors.": "hardening",
            "Add a run recorder.": "automation",
            "Add a project registry.": "capability",
            "Refactor duplicate ranking code.": "improvement",
        }

        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(plan_next_task.classify_work_type(title), expected)

    def test_empty_campaign_queue_falls_back_to_scan_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(
                root,
                "Build a harness that can plan repository improvements.",
                [],
            )
            write_extractors(
                root,
                refactor_payload={
                    "refactor_candidates": [
                        {
                            "title": "Refactor imported script",
                            "decision": "pick",
                            "priority_score": 47,
                            "selection_rationale": ["scan-based hotspot"],
                        }
                    ]
                },
            )

            payload = plan_next_task.choose_candidate(root)

        self.assertEqual(payload["campaign_queue_candidate_count"], 0)
        self.assertEqual(payload["selected"]["source"], "refactor")
        self.assertEqual(payload["selected"]["work_type"], "improvement")
        self.assertEqual(payload["selected"]["title"], "Refactor imported script")


if __name__ == "__main__":
    unittest.main()
