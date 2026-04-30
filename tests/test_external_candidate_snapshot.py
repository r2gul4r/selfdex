from __future__ import annotations

import io
import importlib.util
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_external_candidate_snapshot.py"
SPEC = importlib.util.spec_from_file_location("build_external_candidate_snapshot", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
build_external_candidate_snapshot = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_external_candidate_snapshot
SPEC.loader.exec_module(build_external_candidate_snapshot)


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_registry(root: Path, external: Path, *, write_policy: str = "read-only") -> None:
    (root / "PROJECT_REGISTRY.md").write_text(
        "# Project Registry\n\n"
        "## Registered Projects\n\n"
        "| project_id | path | role | write_policy | verification |\n"
        "| :-- | :-- | :-- | :-- | :-- |\n"
        "| selfdex | . | harness | selfdex-local writes only | python -m unittest |\n"
        f"| external_one | {external} | fixture | {write_policy} | read-only candidate generation |\n",
        encoding="utf-8",
    )


def write_multi_registry(root: Path, projects: dict[str, Path]) -> None:
    rows = [
        "| selfdex | . | harness | selfdex-local writes only | python -m unittest |",
    ]
    for project_id, path in projects.items():
        rows.append(f"| {project_id} | {path} | fixture | read-only | read-only candidate generation |")
    (root / "PROJECT_REGISTRY.md").write_text(
        "# Project Registry\n\n"
        "## Registered Projects\n\n"
        "| project_id | path | role | write_policy | verification |\n"
        "| :-- | :-- | :-- | :-- | :-- |\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )


def write_goal_cycle_fixture(root: Path) -> None:
    write_file(
        root,
        "CAMPAIGN_STATE.md",
        "# Campaign State\n\n## Campaign\n\n- goal: `Build a harness that can detect, plan, verify, and record work.`\n",
    )
    write_file(
        root,
        "docs/GOAL_COMPARISON_AREAS.md",
        "- 저장소가 자기 부족한 코드 품질과 기능 공백을 스스로 찾고, 개선안을 제안·구현·검증한다\n",
    )
    write_file(root, "Makefile", "test: test-installers\n\tpython -m unittest discover -s tests\n")


class ExternalCandidateSnapshotTests(unittest.TestCase):
    def test_build_snapshot_scans_registered_read_only_external_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_registry(root, external)
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
            write_registry(root, external, write_policy="write-enabled")

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
            write_multi_registry(root, {"external_one": external_one, "external_two": external_two})
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
            write_registry(root, external)

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
