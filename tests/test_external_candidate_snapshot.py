from __future__ import annotations

import io
import importlib.util
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

try:
    from external_validation_test_utils import (
        write_external_registry,
        write_file,
        write_goal_cycle_fixture,
        write_multi_external_registry,
    )
except ModuleNotFoundError:
    from tests.external_validation_test_utils import (
        write_external_registry,
        write_file,
        write_goal_cycle_fixture,
        write_multi_external_registry,
    )


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_external_candidate_snapshot.py"
SPEC = importlib.util.spec_from_file_location("build_external_candidate_snapshot", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
build_external_candidate_snapshot = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_external_candidate_snapshot
SPEC.loader.exec_module(build_external_candidate_snapshot)


class ExternalCandidateSnapshotTests(unittest.TestCase):
    def test_build_snapshot_scans_registered_read_only_external_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_external_registry(root, external)
            write_goal_cycle_fixture(external)

            payload = build_external_candidate_snapshot.build_snapshot(root, limit=3)

        project = payload["projects"][0]
        candidate = project["top_candidates"][0]

        self.assertEqual(payload["analysis_kind"], "selfdex_external_candidate_snapshot")
        self.assertEqual(payload["validation_mode"], "read_only")
        self.assertFalse(payload["external_value_proven"])
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(project["project_id"], "external_one")
        self.assertEqual(project["status"], "scanned")
        self.assertEqual(candidate["source"], "project_direction")
        self.assertEqual(candidate["title"], "Close one autonomous feedback loop with evidence")
        self.assertIn("cluster", candidate)
        self.assertIn("evidence", candidate["source_signals"])
        self.assertIn("purpose", project["project_direction"])
        self.assertEqual(
            project["scanner_summaries"][0]["scanner"],
            "project_direction",
        )

    def test_requested_non_read_only_project_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_external_registry(root, external, write_policy="write-enabled")

            payload = build_external_candidate_snapshot.build_snapshot(
                root,
                project_ids=["external_one"],
                limit=3,
            )

        project = payload["projects"][0]

        self.assertEqual(project["status"], "skipped")
        self.assertEqual(project["skip_reason"], "not_external_read_only")
        self.assertEqual(project["candidate_count"], 0)

    def test_requested_project_id_scans_only_selected_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external_one = root / "external-one"
            external_two = root / "external-two"
            external_one.mkdir()
            external_two.mkdir()
            write_multi_external_registry(root, {"external_one": external_one, "external_two": external_two})
            write_goal_cycle_fixture(external_two)

            payload = build_external_candidate_snapshot.build_snapshot(
                root,
                project_ids=["external_two"],
                limit=3,
            )

        self.assertEqual(payload["selection"]["mode"], "explicit")
        self.assertEqual(payload["selection"]["requested_project_ids"], ["external_two"])
        self.assertEqual(payload["selection"]["selected_project_ids"], ["external_two"])
        self.assertEqual(payload["selection"]["missing_project_ids"], [])
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(payload["projects"][0]["project_id"], "external_two")

    def test_missing_requested_project_id_is_visible_and_cli_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_external_registry(root, external)

            payload = build_external_candidate_snapshot.build_snapshot(
                root,
                project_ids=["missing"],
                limit=3,
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = build_external_candidate_snapshot.main(
                    ["--root", str(root), "--project-id", "missing", "--format", "json"]
                )

        self.assertEqual(payload["selection"]["missing_project_ids"], ["missing"])
        self.assertEqual(payload["project_count"], 0)
        self.assertEqual(exit_code, 2)
        self.assertIn('"missing_project_ids"', stdout.getvalue())

    def test_scanner_errors_are_recorded_per_project(self) -> None:
        def broken_scan(_project_root: Path, _limit: int):
            raise RuntimeError("boom")

        project = {
            "project_id": "external_one",
            "path": "./external-one",
            "resolved_path": str(Path.cwd()),
            "path_exists": True,
            "write_policy": "read-only",
        }

        snapshot = build_external_candidate_snapshot.build_project_snapshot(
            project,
            limit=3,
            scan_steps=(("broken", broken_scan),),
        )

        self.assertEqual(snapshot["status"], "error")
        self.assertEqual(snapshot["scanner_errors"][0]["scanner"], "broken")
        self.assertIn("boom", snapshot["scanner_errors"][0]["error"])

    def test_failed_run_history_penalizes_repeated_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runs = root / "runs" / "external_one"
            runs.mkdir(parents=True)
            write_file(
                root,
                "runs/external_one/20260430-failed.md",
                "# Target Codex Run\n\n- status: `blocked`\n\n## Selected Candidate\n\n- title: Repeat me\n",
            )
            candidate = build_external_candidate_snapshot.Candidate(
                source="refactor",
                work_type="improvement",
                title="Repeat me",
                decision="pick",
                priority_score=20,
                risk="medium",
                rationale=[],
                suggested_checks=[],
            )

            adjusted = build_external_candidate_snapshot.apply_run_history_penalty(
                [candidate],
                root,
                "external_one",
            )[0]

        self.assertLess(adjusted.priority_score, candidate.priority_score)
        self.assertTrue(adjusted.source_signals["run_history"]["previous_failed_or_blocked"])

    def test_markdown_keeps_human_review_pending(self) -> None:
        payload = {
            "validation_mode": "read_only",
            "external_value_proven": False,
            "project_count": 0,
            "candidate_count": 0,
            "scanner_error_count": 0,
            "human_review_status": "pending",
            "selection": {
                "mode": "explicit",
                "requested_project_ids": ["external_one"],
                "selected_project_ids": ["external_one"],
                "missing_project_ids": [],
            },
            "projects": [],
        }

        markdown = build_external_candidate_snapshot.render_markdown(payload)

        self.assertIn("# External Candidate Snapshot", markdown)
        self.assertIn("- human_review_status: `pending`", markdown)
        self.assertIn("- selected_project_ids: `external_one`", markdown)


if __name__ == "__main__":
    unittest.main()
