from __future__ import annotations

import io
import importlib.util
import shutil
import subprocess
import sys
import unittest
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_target_codex.py"
TEST_TEMP_ROOT = ROOT / "tmp" / "test-run-target-codex"
SPEC = importlib.util.spec_from_file_location("run_target_codex", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
run_target_codex = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_target_codex
SPEC.loader.exec_module(run_target_codex)


@contextmanager
def temporary_workspace() -> Iterator[Path]:
    TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEST_TEMP_ROOT / f"case-{uuid.uuid4().hex}"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


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


def run_main_for_target(root: Path, target: Path, *, timestamp: str, execute: bool = False) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    args = [
        "--root",
        str(root),
        "--project-root",
        str(target),
        "--project-name",
        "target",
        "--timestamp",
        timestamp,
        "--limit",
        "3",
    ]
    if execute:
        args.append("--execute")
    args.extend(["--format", "json"])

    with redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = run_target_codex.main(args)

    return exit_code, stdout.getvalue(), stderr.getvalue()


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


class BlockedRunner:
    def run(self, *, cwd: Path, prompt: str, model: str, timeout_seconds: int) -> run_target_codex.CodexRunResult:
        return run_target_codex.CodexRunResult(
            status="blocked",
            thread_id="thr_blocked",
            session_id="sess_blocked",
            final_response="",
            changed_files=[],
            verification_results=[],
            repair_attempts=0,
            stop_reason="codex app-server timed out after 1 seconds",
            raw_events=[],
            outcome_class="runtime_failure",
        )


class HangingStream:
    def readline(self) -> str:
        import time

        time.sleep(1)
        return ""


class FiniteStream:
    def __init__(self, lines: list[str]) -> None:
        self.lines = list(lines)

    def readline(self) -> str:
        if not self.lines:
            return ""
        return self.lines.pop(0)


class KillRequiredProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False

    def poll(self) -> None:
        return None

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout: int) -> int:
        if not self.killed:
            raise subprocess.TimeoutExpired("fake", timeout)
        return -9

    def kill(self) -> None:
        self.killed = True


class RunTargetCodexTests(unittest.TestCase):
    def test_stdout_reader_times_out_without_blocking_on_hung_stream(self) -> None:
        reader = run_target_codex._LineQueueReader(HangingStream())  # noqa: SLF001
        reader.start()

        with self.assertRaises(run_target_codex.AppServerTimeoutError):
            reader.read_line(run_target_codex._Deadline(0))  # noqa: SLF001

    def test_terminate_process_kills_when_terminate_wait_times_out(self) -> None:
        process = KillRequiredProcess()

        returncode = run_target_codex.terminate_process(process)  # type: ignore[arg-type]

        self.assertEqual(returncode, -9)
        self.assertTrue(process.terminated)
        self.assertTrue(process.killed)

    def test_stderr_reader_captures_tail_without_blocking(self) -> None:
        reader = run_target_codex._StderrTailReader(FiniteStream(["first\n", "second\n"]))  # noqa: SLF001
        reader.start()
        reader.join(1)

        self.assertEqual(reader.lines(), ["first", "second"])

    def test_read_event_rejects_invalid_json_line(self) -> None:
        reader = run_target_codex._LineQueueReader(FiniteStream(["not json\n"]))  # noqa: SLF001
        reader.start()
        session = run_target_codex._AppServerSession(["codex", "app-server"], ROOT, 1)  # noqa: SLF001

        with self.assertRaises(run_target_codex.AppServerProtocolError):
            session._read_event(reader, run_target_codex._Deadline(1), "testing invalid json")  # noqa: SLF001

    def test_dry_run_records_under_project_folder_without_target_branch(self) -> None:
        with temporary_workspace() as temp_dir:
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
        self.assertEqual(payload["outcome_class"], "dry_run")
        self.assertEqual(payload["project_key"], "target-project")
        self.assertEqual(artifact.parent.name, "target-project")
        self.assertTrue(artifact_exists)
        self.assertIn("not executed", payload["stop_reason"])

    def test_execute_creates_branch_and_uses_fake_runner(self) -> None:
        with temporary_workspace() as temp_dir:
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
        self.assertEqual(payload["outcome_class"], "success")
        self.assertTrue(payload["branch_created"])
        self.assertEqual(payload["branch"], "selfdex/test-branch")
        self.assertTrue(payload["branch_before"])
        self.assertEqual(payload["branch_after"], "selfdex/test-branch")
        self.assertFalse(payload["restore_attempted"])
        self.assertEqual(payload["restore_result"], "not_needed")
        self.assertEqual(payload["codex"]["thread_id"], "thr_fixture")
        self.assertEqual(payload["changed_files"], ["docs/GOAL_COMPARISON_AREAS.md"])
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("Expected outcome:", str(runner.calls[0]["prompt"]))

    def test_execute_blocked_restores_created_branch_when_target_is_clean(self) -> None:
        with temporary_workspace() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            target = Path(temp_dir) / "target"
            root.mkdir()
            target.mkdir()
            write_goal_cycle_fixture(target)
            init_clean_git_repo(target)

            payload = run_target_codex.build_orchestration_payload(
                root,
                project_root=str(target),
                project_name="target",
                timestamp="20260430-153005",
                execute=True,
                branch_name="selfdex/blocked-branch",
                runner=BlockedRunner(),
                limit=3,
            )

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["outcome_class"], "runtime_failure")
        self.assertTrue(payload["branch_created"])
        self.assertTrue(payload["restore_attempted"])
        self.assertEqual(payload["branch_after"], payload["branch_before"])
        self.assertIn("restored to", payload["restore_result"])

    def test_unicode_project_name_uses_safe_project_folder(self) -> None:
        with temporary_workspace() as temp_dir:
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
        with temporary_workspace() as temp_dir:
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

    def test_exit_code_for_payload_keeps_success_zero(self) -> None:
        payload: dict[str, Any] = {
            "status": "completed",
            "execute_requested": True,
            "outcome_class": "success",
        }

        self.assertEqual(run_target_codex.exit_code_for_payload(payload), 0)

    def test_main_returns_zero_for_dry_run_blocked(self) -> None:
        with temporary_workspace() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            target = Path(temp_dir) / "target"
            root.mkdir()
            target.mkdir()
            write_goal_cycle_fixture(target)

            exit_code, stdout, stderr = run_main_for_target(root, target, timestamp="20260430-153006")

        self.assertEqual(exit_code, 0)
        self.assertIn('"outcome_class": "dry_run"', stdout)
        self.assertEqual(stderr, "")

    def test_main_returns_two_for_execute_blocked(self) -> None:
        with temporary_workspace() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            target = Path(temp_dir) / "target"
            root.mkdir()
            target.mkdir()
            write_goal_cycle_fixture(target)

            exit_code, stdout, stderr = run_main_for_target(
                root,
                target,
                timestamp="20260430-153007",
                execute=True,
            )

        self.assertEqual(exit_code, 2)
        self.assertIn('"status": "blocked"', stdout)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
