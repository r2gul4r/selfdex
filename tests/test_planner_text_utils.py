from __future__ import annotations

import unittest
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]


planner_text_utils = load_script("planner_text_utils.py")


class PlannerTextUtilsTests(unittest.TestCase):
    def test_parses_campaign_goal_and_queue_items(self) -> None:
        text = """# Campaign State

## Campaign

- name: `demo`
- goal: `Build a planner that can plan and record work.`

## Candidate Queue

- Add real unit tests for `scripts/plan_next_task.py`.
- Add a run recorder.
"""

        self.assertEqual(
            planner_text_utils.parse_campaign_goal(text),
            "Build a planner that can plan and record work.",
        )
        self.assertEqual(
            planner_text_utils.parse_campaign_queue(text),
            [
                "Add real unit tests for scripts/plan_next_task.py.",
                "Add a run recorder.",
            ],
        )

    def test_campaign_goal_matches_normalized_tokens(self) -> None:
        matches = planner_text_utils.campaign_goal_matches(
            "Build a harness that records verified improvements.",
            "Add record verification improvement checks.",
        )

        self.assertEqual(matches, ["improvement", "record"])

    def test_classify_work_type_uses_existing_priority_order(self) -> None:
        cases = {
            "Fix broken scan fallback.": "repair",
            "Add fixture-based tests for candidate extractors.": "hardening",
            "Add a run recorder.": "automation",
            "Add a project registry.": "capability",
            "Refactor duplicate ranking code.": "improvement",
            "Polish small wording.": "fallback",
        }

        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(planner_text_utils.classify_work_type(title, default="fallback"), expected)


if __name__ == "__main__":
    unittest.main()
