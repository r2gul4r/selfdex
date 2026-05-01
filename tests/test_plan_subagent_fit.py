from __future__ import annotations

import importlib.util
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_subagent_fit.py"
SPEC = importlib.util.spec_from_file_location("plan_subagent_fit", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
plan_subagent_fit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = plan_subagent_fit
SPEC.loader.exec_module(plan_subagent_fit)


@dataclass(frozen=True)
class Candidate:
    source: str
    work_type: str
    title: str
    source_signals: dict[str, Any] = field(default_factory=dict)


class PlanSubagentFitTests(unittest.TestCase):
    def test_none_candidate_is_main_only(self) -> None:
        fit = plan_subagent_fit.build_subagent_fit(None)

        self.assertEqual(fit.subagent_value, "main_only")
        self.assertEqual(plan_subagent_fit.recommended_agents_for_fit(fit, None), ["main"])

    def test_small_duplicate_is_main_only(self) -> None:
        candidate = Candidate(
            source="refactor",
            work_type="improvement",
            title="extract_markdown_section 중복 정리",
            source_signals={
                "candidate_source": "duplicate_block",
                "paths": ["scripts/a.py", "scripts/b.py"],
                "normalized_line_count": 10,
                "occurrence_count": 2,
            },
        )

        fit = plan_subagent_fit.build_subagent_fit(candidate)

        self.assertEqual(fit.task_size_class, "small")
        self.assertEqual(fit.subagent_value, "main_only")

    def test_large_disjoint_duplicate_uses_worker_and_reviewer(self) -> None:
        candidate = Candidate(
            source="refactor",
            work_type="improvement",
            title="three extractor duplicate cleanup",
            source_signals={
                "candidate_source": "duplicate_block",
                "paths": ["scripts/a.py", "scripts/b.py", "scripts/c.py"],
                "normalized_line_count": 30,
                "occurrence_count": 3,
            },
        )

        fit = plan_subagent_fit.build_subagent_fit(candidate)
        agents = plan_subagent_fit.recommended_agents_for_fit(fit, candidate)

        self.assertEqual(fit.subagent_value, "use_subagents")
        self.assertEqual(agents, ["main", "explorer", "worker", "reviewer"])

    def test_large_collision_uses_readonly_subagents_first(self) -> None:
        candidate = Candidate(
            source="refactor",
            work_type="improvement",
            title="scripts/collect_repo_metrics.py responsibility split",
            source_signals={
                "candidate_source": "complexity_hotspot",
                "path": "scripts/collect_repo_metrics.py",
                "code_lines": 700,
                "cyclomatic_estimate": 120,
            },
        )

        fit = plan_subagent_fit.build_subagent_fit(candidate)
        agents = plan_subagent_fit.recommended_agents_for_fit(fit, candidate)

        self.assertEqual(fit.write_collision_risk, "high")
        self.assertEqual(fit.subagent_value, "use_readonly_subagents_first")
        self.assertEqual(agents, ["main", "explorer", "reviewer"])

    def test_docs_researcher_is_recommended_for_api_or_apps_uncertainty(self) -> None:
        candidate = Candidate(
            source="campaign_queue",
            work_type="direction",
            title="Review ChatGPT Apps MCP direction with official docs",
            source_signals={
                "api_behavior_uncertain": True,
                "surface": "ChatGPT Apps",
            },
        )

        fit = plan_subagent_fit.build_subagent_fit(candidate)
        agents = plan_subagent_fit.recommended_agents_for_fit(fit, candidate)

        self.assertIn("docs_researcher", agents)
        self.assertEqual(agents[0], "main")


if __name__ == "__main__":
    unittest.main()
