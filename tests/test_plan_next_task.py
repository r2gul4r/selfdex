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


def imported_refactor_payload() -> dict[str, Any]:
    return {
        "refactor_candidates": [
            {
                "title": "Refactor imported script",
                "decision": "pick",
                "priority_score": 47,
                "selection_rationale": ["scan-based hotspot"],
            }
        ]
    }


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
                refactor_payload=imported_refactor_payload(),
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

    def test_recommended_agents_records_subagent_use_and_write_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(
                root,
                "Build a harness that can use native agents and record work.",
                ["Add a native subagent planner that records selected agents."],
            )
            write_extractors(root)

            payload = plan_next_task.choose_candidate(root)
            markdown = plan_next_task.render_markdown(payload)

        agents = payload["recommended_agents"]
        fit = agents["subagent_fit"]
        self.assertEqual(
            agents["subagent_use"],
            "use_subagents_after_contract_freeze",
        )
        self.assertEqual(fit["task_size_class"], "large")
        self.assertEqual(fit["subagent_value"], "use_subagents")
        self.assertIn("main", agents["selected_agents"])
        self.assertIn("worker", agents["selected_agents"])
        self.assertIn("main: own state", agents["write_boundaries"][0])
        self.assertIn("- subagent_use: `use_subagents_after_contract_freeze`", markdown)
        self.assertIn("## Subagent Fit", markdown)
        self.assertIn("- subagent_value: `use_subagents`", markdown)
        self.assertIn("## Write Boundaries", markdown)

    def test_small_refactor_candidate_stays_main_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(root, "Build a harness that can improve safely.", [])
            write_extractors(
                root,
                refactor_payload={
                    "refactor_candidates": [
                        {
                            "title": "extract_markdown_section 중복 정리",
                            "decision": "pick",
                            "priority_score": 50,
                            "selection_rationale": ["small helper duplicate"],
                            "source_signals": {
                                "candidate_source": "duplicate_block",
                                "paths": ["scripts/check_doc_drift.py", "scripts/markdown_utils.py"],
                                "normalized_line_count": 10,
                                "occurrence_count": 2,
                            },
                        }
                    ]
                },
            )

            payload = plan_next_task.choose_candidate(root)

        agents = payload["recommended_agents"]
        fit = agents["subagent_fit"]
        self.assertEqual(fit["task_size_class"], "small")
        self.assertEqual(fit["coordination_cost"], "high")
        self.assertEqual(fit["subagent_value"], "main_only")
        self.assertEqual(agents["subagent_use"], "main_only")
        self.assertEqual(agents["selected_agents"], ["main"])

    def test_large_single_file_hotspot_uses_sidecars_not_parallel_workers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(root, "Build a harness that can improve safely.", [])
            write_extractors(
                root,
                refactor_payload={
                    "refactor_candidates": [
                        {
                            "title": "scripts/collect_repo_metrics.py 책임 분리와 경계 정리",
                            "decision": "pick",
                            "priority_score": 50,
                            "selection_rationale": ["single-file hotspot"],
                            "source_signals": {
                                "candidate_source": "complexity_hotspot",
                                "path": "scripts/collect_repo_metrics.py",
                                "code_lines": 700,
                                "cyclomatic_estimate": 120,
                            },
                        }
                    ]
                },
            )

            payload = plan_next_task.choose_candidate(root)

        agents = payload["recommended_agents"]
        fit = agents["subagent_fit"]
        self.assertEqual(fit["task_size_class"], "large")
        self.assertEqual(fit["write_collision_risk"], "high")
        self.assertEqual(fit["subagent_value"], "use_readonly_subagents_first")
        self.assertEqual(agents["subagent_use"], "use_readonly_subagents_first")
        self.assertEqual(agents["selected_agents"], ["main", "explorer", "reviewer"])

    def test_guarded_docs_candidate_keeps_docs_researcher_and_reviewer(self) -> None:
        candidate = plan_next_task.Candidate(
            source="feature_gap",
            work_type="capability",
            title="Clarify ChatGPT Apps MCP API behavior",
            decision="needs_approval",
            priority_score=30,
            risk="guarded",
            rationale=["official docs needed"],
            suggested_checks=["python scripts/plan_next_task.py --root . --format json"],
            source_signals={"api_behavior_uncertain": True, "surface": "ChatGPT Apps"},
        )

        agents = plan_next_task.recommend_agents(candidate)

        self.assertEqual(agents["subagent_use"], "main_plus_readonly_if_needed")
        self.assertIn("docs_researcher", agents["selected_agents"])
        self.assertIn("reviewer", agents["selected_agents"])
        self.assertNotIn("worker", agents["selected_agents"])

    def test_large_disjoint_duplicate_can_recommend_concurrent_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(root, "Build a harness that can improve safely.", [])
            write_extractors(
                root,
                refactor_payload={
                    "refactor_candidates": [
                        {
                            "title": "three extractor duplicate cleanup",
                            "decision": "pick",
                            "priority_score": 50,
                            "selection_rationale": ["disjoint duplicate paths"],
                            "source_signals": {
                                "candidate_source": "duplicate_block",
                                "paths": [
                                    "scripts/a.py",
                                    "scripts/b.py",
                                    "scripts/c.py",
                                ],
                                "normalized_line_count": 30,
                                "occurrence_count": 3,
                            },
                        }
                    ]
                },
            )

            payload = plan_next_task.choose_candidate(root)

        agents = payload["recommended_agents"]
        fit = agents["subagent_fit"]
        self.assertEqual(fit["task_size_class"], "large")
        self.assertEqual(fit["estimated_write_boundary_count"], 3)
        self.assertEqual(fit["write_collision_risk"], "low")
        self.assertEqual(fit["subagent_value"], "use_subagents")
        self.assertEqual(agents["subagent_use"], "use_subagents_after_contract_freeze")

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
                refactor_payload=imported_refactor_payload(),
            )

            payload = plan_next_task.choose_candidate(root)

        self.assertEqual(payload["campaign_queue_candidate_count"], 0)
        self.assertEqual(payload["selected"]["source"], "refactor")
        self.assertEqual(payload["selected"]["work_type"], "improvement")
        self.assertEqual(payload["selected"]["title"], "Refactor imported script")
        self.assertIn("cluster", payload["selected"])

    def test_failed_run_history_penalizes_repeated_local_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_campaign(root, "Build a harness that can improve safely.", [])
            runs = root / "runs" / "selfdex"
            runs.mkdir(parents=True)
            (runs / "20260430-failed.md").write_text(
                "# Target Codex Run\n\n- status: `failed`\n\n## Selected Candidate\n\n- title: Refactor imported script\n",
                encoding="utf-8",
            )
            write_extractors(root, refactor_payload=imported_refactor_payload())

            payload = plan_next_task.choose_candidate(root)

        candidate = payload["selected"]
        self.assertEqual(candidate["title"], "Refactor imported script")
        self.assertTrue(candidate["source_signals"]["run_history"]["previous_failed_or_blocked"])
        self.assertLess(candidate["priority_score"], 47)


if __name__ == "__main__":
    unittest.main()
