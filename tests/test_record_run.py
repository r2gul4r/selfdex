from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "record_run.py"
SPEC = importlib.util.spec_from_file_location("record_run", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
record_run = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = record_run
SPEC.loader.exec_module(record_run)


class RecordRunTests(unittest.TestCase):
    def test_sanitizes_slug_for_filename(self) -> None:
        self.assertEqual(record_run.sanitize_slug("Run Recorder! v1"), "run-recorder-v1")
        self.assertEqual(record_run.sanitize_slug("!!!"), "run")

    def test_writes_run_record_under_runs_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = record_run.write_run_record(
                root,
                record_run.RunRecord(
                    timestamp="20260424-131500",
                    project_key="Selfdex Core",
                    slug="Run Recorder!",
                    goal="Build recursive improvement.",
                    selected_candidate="Add a run recorder.",
                    agents_used=["main", "reviewer"],
                    subagent_permission="@selfdex invocation",
                    write_sets=["scripts/record_run.py", "tests/test_record_run.py"],
                    verification=["python -m unittest discover -s tests"],
                    repair_attempts="0",
                    result="passed",
                    next_candidate="Add project registry.",
                ),
            )

            content = result.read_text(encoding="utf-8")

        self.assertEqual(result.name, "20260424-131500-run-recorder.md")
        self.assertEqual(result.parent, root / "runs" / "selfdex-core")
        self.assertIn("- project_key: selfdex-core", content)
        self.assertIn("- goal: Build recursive improvement.", content)
        self.assertIn("- selected_candidate: Add a run recorder.", content)
        self.assertIn("- agents_used: main, reviewer", content)
        self.assertIn("- subagent_permission: @selfdex invocation", content)
        self.assertIn("- scripts/record_run.py", content)
        self.assertIn("- python -m unittest discover -s tests", content)

    def test_refuses_to_overwrite_existing_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = record_run.RunRecord(
                timestamp="20260424-131500",
                project_key="same-project",
                slug="same",
                goal="Goal",
                selected_candidate="Candidate",
                agents_used=["main"],
                subagent_permission="@selfdex invocation",
                write_sets=[],
                verification=[],
                repair_attempts="0",
                result="passed",
                next_candidate="Next",
            )
            record_run.write_run_record(root, record)

            with self.assertRaises(FileExistsError):
                record_run.write_run_record(root, record)

    def test_rejects_invalid_timestamp(self) -> None:
        with self.assertRaises(ValueError):
            record_run.validate_timestamp("2026-04-24")

    def test_sanitizes_unicode_project_key(self) -> None:
        self.assertEqual(record_run.sanitize_project_key("다보여 프로젝트!!"), "다보여-프로젝트")


if __name__ == "__main__":
    unittest.main()
