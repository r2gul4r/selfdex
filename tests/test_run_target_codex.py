from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_target_codex.py"
SPEC = importlib.util.spec_from_file_location("run_target_codex", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
run_target_codex = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_target_codex
SPEC.loader.exec_module(run_target_codex)


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_goal_cycle_fixture(root: Path) -> None:
    write_file(
        root,
        "CAMPAIGN_STATE.md",
        "# Campaign State\n\n## Campaign\n\n- goal: `Build a harness that can detect, plan, verify, and record work.`\n",
    )
    write_file(
        root,
        "docs/GOAL_COMPARISON_AREAS.md",
        "- candidate evidence for useful local planning\n",
    )
    write_file(root, "Makefile", "test:\n\tpython -m unittest discover -s tests\n")


def init_clean_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "selfdex@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Selfdex"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True, text=True)


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run(self, *, cwd: Path, prompt: str, model: str, timeout_seconds: int) -> run_target_codex.CodexRunResult:
        self.calls.append(
            {
                "cwd": cwd,
                "prompt": prompt,
                "model": model,
                "timeout_seconds": timeout_seconds,
            }
        )
        return run_target_codex.CodexRunResult(
            status="completed",
            thread_id="thr_fixture",
            session_id="sess_fixture",
            final_response="done",
            changed_files=["docs/GOAL_COMPARISON_AREAS.md"],
            verification_results=["python -m unittest discover -s tests: passed"],
            repair_attempts=0,
            stop_reason="",
            raw_events=[],
        )


class RunTargetCodexTests(unittest.TestCase):
    def test_dry_run_records_under_project_folder_without_target_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            target = Path(temp_dir) / "target project"
            root.mkdir()
            target.mkdir()
            write_goal_cycle_fixture(target)

            payload = run_target_codex.build_orchestration_payload(
                root,
                project_root=str(target),
                project_name="Target Project",
                timestamp="20260430-153000",
                limit=3,
            )

            artifact = Path(payload["recorded_run_path"])
            artifact_exists = artifact.exists()

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["project_key"], "target-project")
        self.assertEqual(artifact.parent.name, "target-project")
        self.assertTrue(artifact_exists)
        self.assertIn("not executed", payload["stop_reason"])

    def test_execute_creates_branch_and_uses_fake_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            target = Path(temp_dir) / "target"
            root.mkdir()
            target.mkdir()
            write_goal_cycle_fixture(target)
            init_clean_git_repo(target)
            runner = FakeRunner()

            payload = run_target_codex.build_orchestration_payload(
                root,
                project_root=str(target),
                project_name="target",
                timestamp="20260430-153001",
                execute=True,
                branch_name="selfdex/test-branch",
                runner=runner,
                limit=3,
            )

        self.assertEqual(payload["status"], "completed")
        self.assertTrue(payload["branch_created"])
        self.assertEqual(payload["branch"], "selfdex/test-branch")
        self.assertEqual(payload["codex"]["thread_id"], "thr_fixture")
        self.assertEqual(payload["changed_files"], ["docs/GOAL_COMPARISON_AREAS.md"])
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("Expected outcome:", str(runner.calls[0]["prompt"]))

    def test_unicode_project_name_uses_safe_project_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            target = Path(temp_dir) / "fallback"
            root.mkdir()
            target.mkdir()
            write_goal_cycle_fixture(target)

            payload = run_target_codex.build_orchestration_payload(
                root,
                project_root=str(target),
                project_name="다보여 Project!",
                timestamp="20260430-153002",
                limit=3,
            )

        self.assertEqual(payload["project_key"], "다보여-project")

    def test_different_projects_record_in_different_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            one = Path(temp_dir) / "one"
            two = Path(temp_dir) / "two"
            root.mkdir()
            one.mkdir()
            two.mkdir()
            write_goal_cycle_fixture(one)
            write_goal_cycle_fixture(two)

            first = run_target_codex.build_orchestration_payload(
                root,
                project_root=str(one),
                project_name="one",
                timestamp="20260430-153003",
                limit=3,
            )
            second = run_target_codex.build_orchestration_payload(
                root,
                project_root=str(two),
                project_name="two",
                timestamp="20260430-153004",
                limit=3,
            )

        self.assertNotEqual(Path(first["recorded_run_path"]).parent, Path(second["recorded_run_path"]).parent)


if __name__ == "__main__":
    unittest.main()
