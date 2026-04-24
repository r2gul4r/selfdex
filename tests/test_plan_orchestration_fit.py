from __future__ import annotations

import importlib.util
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_orchestration_fit.py"
SPEC = importlib.util.spec_from_file_location("plan_orchestration_fit", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
plan_orchestration_fit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = plan_orchestration_fit
SPEC.loader.exec_module(plan_orchestration_fit)


@dataclass(frozen=True)
class CandidateStub:
    source: str
    work_type: str
    title: str
    source_signals: dict[str, Any] = field(default_factory=dict)


class PlanOrchestrationFitTests(unittest.TestCase):
    def test_none_candidate_returns_noop_fit(self) -> None:
        fit = plan_orchestration_fit.build_orchestration_fit(None)

        self.assertEqual(fit.task_size_class, "none")
        self.assertEqual(fit.estimated_write_set_count, 0)
        self.assertEqual(fit.orchestration_value, "low")

    def test_small_duplicate_refactor_stays_low_value(self) -> None:
        candidate = CandidateStub(
            source="refactor",
            work_type="improvement",
            title="extract_markdown_section 중복 정리",
            source_signals={
                "candidate_source": "duplicate_block",
                "paths": ["scripts/check_doc_drift.py", "scripts/markdown_utils.py"],
                "normalized_line_count": 10,
                "occurrence_count": 2,
            },
        )

        fit = plan_orchestration_fit.build_orchestration_fit(candidate)

        self.assertEqual(fit.task_size_class, "small")
        self.assertEqual(fit.handoff_cost, "high")
        self.assertEqual(fit.parallel_gain, "low")
        self.assertEqual(fit.orchestration_value, "low")

    def test_large_single_file_hotspot_uses_medium_value_sidecar_fit(self) -> None:
        candidate = CandidateStub(
            source="refactor",
            work_type="improvement",
            title="scripts/collect_repo_metrics.py 책임 분리와 경계 정리",
            source_signals={
                "candidate_source": "complexity_hotspot",
                "path": "scripts/collect_repo_metrics.py",
                "code_lines": 700,
                "cyclomatic_estimate": 120,
            },
        )

        fit = plan_orchestration_fit.build_orchestration_fit(candidate)

        self.assertEqual(fit.task_size_class, "large")
        self.assertEqual(fit.estimated_write_set_count, 2)
        self.assertEqual(fit.shared_file_collision_risk, "high")
        self.assertEqual(fit.parallel_gain, "medium")
        self.assertEqual(fit.orchestration_value, "medium")

    def test_disjoint_large_duplicate_has_high_orchestration_value(self) -> None:
        candidate = CandidateStub(
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

        fit = plan_orchestration_fit.build_orchestration_fit(candidate)
        payload = plan_orchestration_fit.orchestration_fit_to_dict(fit)

        self.assertEqual(fit.task_size_class, "large")
        self.assertEqual(fit.estimated_write_set_count, 3)
        self.assertEqual(fit.shared_file_collision_risk, "low")
        self.assertEqual(fit.orchestration_value, "high")
        self.assertEqual(payload["verification_independence"], "high")


if __name__ == "__main__":
    unittest.main()
