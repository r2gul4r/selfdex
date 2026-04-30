from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from external_validation_test_utils import external_snapshot_payload, planner_candidate, planner_payload
except ModuleNotFoundError:
    from tests.external_validation_test_utils import external_snapshot_payload, planner_candidate, planner_payload


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_external_validation_report.py"
SPEC = importlib.util.spec_from_file_location("build_external_validation_report", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
build_external_validation_report = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_external_validation_report
SPEC.loader.exec_module(build_external_validation_report)


REGISTRY_TEXT = """# Project Registry

## Registered Projects

| project_id | path | role | write_policy | verification |
| :-- | :-- | :-- | :-- | :-- |
| selfdex | . | harness | selfdex-local writes only | python -m unittest |
| external_one | ./external-one | fixture | read-only | python -m test |
"""


PLANNER_PAYLOAD = planner_payload(
    [
        planner_candidate(
            work_type="improvement",
            decision="pick",
            priority_score=42.5,
            risk="medium",
        )
    ]
)


QUALITY_PAYLOAD = {
    "schema_version": 1,
    "analysis_kind": "candidate_quality_evaluation",
    "status": "pass",
    "results": [
        {
            "candidate": "split candidate extraction helpers",
            "total": 13,
            "verdict": "strong",
            "scores": {
                "real_problem": 3,
                "user_value": 2,
                "local_verifiability": 3,
                "scope_smallness": 2,
                "risk_reversibility": 3,
            },
            "issues": [],
        }
    ],
}


EXTERNAL_SNAPSHOT_PAYLOAD = external_snapshot_payload(
    [
        (
            "external_one",
            [
                planner_candidate(
                    work_type="improvement",
                    decision="pick",
                    priority_score=42.5,
                    risk="medium",
                )
            ],
        )
    ]
)


class ExternalValidationReportTests(unittest.TestCase):
    def test_build_report_matches_quality_by_candidate_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")

            report = build_external_validation_report.build_report(
                root,
                PLANNER_PAYLOAD,
                QUALITY_PAYLOAD,
                "external_one",
            )

        candidate = report["candidates"][0]

        self.assertEqual(report["analysis_kind"], "selfdex_external_validation_report")
        self.assertEqual(report["validation_mode"], "read_only")
        self.assertTrue(report["external_value_proven"])
        self.assertEqual(candidate["quality"]["status"], "scored")
        self.assertEqual(candidate["quality"]["total"], 13)
        self.assertEqual(candidate["human_review_status"], "pending")

    def test_missing_quality_score_is_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")

            report = build_external_validation_report.build_report(
                root,
                PLANNER_PAYLOAD,
                None,
                "external_one",
            )

        self.assertEqual(report["candidates"][0]["quality"]["status"], "missing")
        self.assertEqual(report["status"], "needs_scoring")
        finding_ids = {finding["finding_id"] for finding in report["findings"]}
        self.assertIn("candidate-quality-missing", finding_ids)

    def test_build_report_accepts_external_snapshot_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")

            report = build_external_validation_report.build_report(
                root,
                EXTERNAL_SNAPSHOT_PAYLOAD,
                None,
                "external_one",
            )

        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["status"], "needs_scoring")
        self.assertEqual(report["candidates"][0]["title"], "split candidate extraction helpers")
        self.assertEqual(report["candidates"][0]["quality"]["status"], "missing")
        finding_ids = {finding["finding_id"] for finding in report["findings"]}
        self.assertIn("candidate-quality-missing", finding_ids)

    def test_report_fails_for_unregistered_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")

            report = build_external_validation_report.build_report(
                root,
                PLANNER_PAYLOAD,
                QUALITY_PAYLOAD,
                "unknown",
            )

        self.assertEqual(report["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in report["findings"]}
        self.assertIn("project-not-registered", finding_ids)

    def test_markdown_output_includes_read_only_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")
            report = build_external_validation_report.build_report(
                root,
                PLANNER_PAYLOAD,
                QUALITY_PAYLOAD,
                "external_one",
            )

        markdown = build_external_validation_report.render_markdown(report)

        self.assertIn("# External Read-Only Validation Report", markdown)
        self.assertIn("- validation_mode: `read_only`", markdown)
        self.assertIn("split candidate extraction helpers", markdown)


if __name__ == "__main__":
    unittest.main()
