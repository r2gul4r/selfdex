#!/usr/bin/env python3
"""Run one target-project Codex task from a Selfdex plan."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import target_codex_app_server as app_server
    from argparse_utils import add_format_argument, add_root_argument
    from cli_output_utils import write_json_or_markdown
    from plan_external_project import build_plan, slugify
except ModuleNotFoundError:
    from scripts import target_codex_app_server as app_server
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.plan_external_project import build_plan, slugify


SCHEMA_VERSION = 1
AppServerCodexRunner = app_server.AppServerCodexRunner
AppServerProtocolError = app_server.AppServerProtocolError
AppServerTimeoutError = app_server.AppServerTimeoutError
CodexRunResult = app_server.CodexRunResult
CodexRunner = app_server.CodexRunner
FINAL_STATUSES = app_server.FINAL_STATUSES
STDERR_TAIL_LIMIT = app_server.STDERR_TAIL_LIMIT
_AppServerSession = app_server._AppServerSession
_Deadline = app_server._Deadline
_LineQueueReader = app_server._LineQueueReader
_StderrTailReader = app_server._StderrTailReader
blocked_result = app_server.blocked_result
git_changed_files = app_server.git_changed_files
terminate_process = app_server.terminate_process


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan and run one target-project Codex task.")
    add_root_argument(parser, help_text="Selfdex repository root.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--project-id", help="Registered project id from PROJECT_REGISTRY.md.")
    target.add_argument("--project-root", help="Ad-hoc target project path.")
    parser.add_argument("--project-name", help="Project label for --project-root output.")
    parser.add_argument("--candidate-index", type=int, default=1, help="1-based candidate index. Defaults to 1.")
    parser.add_argument("--limit", type=int, default=5, help="Top candidate scan limit. Defaults to 5.")
    parser.add_argument("--timestamp", help="Run artifact timestamp in YYYYMMDD-HHMMSS format.")
    parser.add_argument("--model", default="gpt-5.4", help="Codex model for app-server thread/start.")
    parser.add_argument("--timeout-seconds", type=int, default=1800, help="Codex app-server timeout budget.")
    parser.add_argument("--execute", action="store_true", help="Actually create a branch and run Codex app-server.")
    parser.add_argument("--branch-name", help="Optional target branch name. Defaults to selfdex/<project>/<timestamp>-<slug>.")
    add_format_argument(parser, default="markdown", help_text="Output format. Defaults to markdown.")
    return parser.parse_args(argv)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def local_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def project_key_from_payload(payload: dict[str, Any]) -> str:
    project = payload.get("project", {})
    project_id = str(project.get("project_id") or "").strip()
    if project_id:
        return slugify(project_id)
    resolved = str(project.get("resolved_path") or "").strip()
    if resolved:
        return slugify(Path(resolved).name)
    return "project"


def candidate_slug(payload: dict[str, Any]) -> str:
    contract = payload.get("task_contract") or {}
    candidate = contract.get("selected_candidate") or {}
    return slugify(str(candidate.get("title") or "target-codex-run"))


def run_artifact_path(root: Path, project_key: str, timestamp: str, task_slug: str) -> Path:
    return root / "runs" / project_key / f"{timestamp}-{task_slug}.md"


def default_branch_name(project_key: str, timestamp: str, task_slug: str) -> str:
    return f"selfdex/{project_key}/{timestamp}-{task_slug}"


def git_output(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def git_is_repo(cwd: Path) -> bool:
    return git_output(cwd, ["rev-parse", "--is-inside-work-tree"]).returncode == 0


def git_dirty_paths(cwd: Path) -> list[str]:
    process = git_output(cwd, ["status", "--short"])
    if process.returncode != 0:
        return ["<git status failed>"]
    return [line.strip() for line in process.stdout.splitlines() if line.strip()]


def git_current_branch(cwd: Path) -> str:
    process = git_output(cwd, ["branch", "--show-current"])
    if process.returncode == 0 and process.stdout.strip():
        return process.stdout.strip()
    process = git_output(cwd, ["rev-parse", "--short", "HEAD"])
    if process.returncode == 0:
        return process.stdout.strip()
    return ""


def create_branch(cwd: Path, branch_name: str) -> tuple[bool, str]:
    process = git_output(cwd, ["switch", "-c", branch_name])
    if process.returncode == 0:
        return True, ""
    return False, process.stderr.strip() or process.stdout.strip() or "git switch failed"


def switch_branch(cwd: Path, branch_name: str) -> tuple[bool, str]:
    process = git_output(cwd, ["switch", branch_name])
    if process.returncode == 0:
        return True, ""
    return False, process.stderr.strip() or process.stdout.strip() or "git switch failed"


def outcome_class_for_result(*, execute: bool, result: CodexRunResult) -> str:
    if not execute:
        return "dry_run"
    if result.outcome_class:
        return result.outcome_class
    if result.status == "completed":
        return "success"
    if result.status in {"failed", "stopped"}:
        return "runtime_failure"
    return "blocked_by_policy"


def exit_code_for_payload(payload: dict[str, Any]) -> int:
    if payload.get("status") == "completed":
        return 0
    if not payload.get("execute_requested"):
        return 0 if payload.get("outcome_class") == "dry_run" else 1
    if payload.get("status") in {"blocked", "failed", "stopped"}:
        return 2
    return 1


def build_orchestration_payload(
    root: Path,
    *,
    project_id: str | None = None,
    project_root: str | None = None,
    project_name: str | None = None,
    candidate_index: int = 1,
    limit: int = 5,
    timestamp: str | None = None,
    model: str = "gpt-5.4",
    timeout_seconds: int = 1800,
    execute: bool = False,
    branch_name: str | None = None,
    runner: CodexRunner | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    timestamp = timestamp or local_timestamp()
    plan = build_plan(
        root,
        project_id=project_id,
        project_root=project_root,
        project_name=project_name,
        candidate_index=candidate_index,
        limit=limit,
    )
    project_key = project_key_from_payload(plan)
    task_slug = candidate_slug(plan)
    branch = branch_name or default_branch_name(project_key, timestamp, task_slug)
    artifact = run_artifact_path(root, project_key, timestamp, task_slug)
    result = blocked_result("not executed; pass --execute to create a branch and run target Codex")
    target_root = Path(str(plan.get("project", {}).get("resolved_path") or ""))
    branch_created = False
    branch_before = ""
    branch_after = ""
    restore_attempted = False
    restore_result = "not_needed"

    if plan.get("status") != "ready":
        result = blocked_result(str(plan.get("blocker") or "plan is not ready"))
    elif execute:
        if not target_root.exists():
            result = blocked_result("target project path does not exist")
        elif not git_is_repo(target_root):
            result = blocked_result("target project is not a git repository")
        else:
            branch_before = git_current_branch(target_root)
            branch_after = branch_before
            dirty = git_dirty_paths(target_root)
            if dirty:
                result = blocked_result("target project worktree is dirty: " + "; ".join(dirty))
            else:
                ok, error = create_branch(target_root, branch)
                branch_created = ok
                branch_after = git_current_branch(target_root)
                if not ok:
                    result = blocked_result(f"could not create target branch: {error}")
                else:
                    codex_runner = runner or AppServerCodexRunner()
                    prompt = str(plan["task_contract"]["codex_execution_prompt"])
                    try:
                        result = codex_runner.run(
                            cwd=target_root,
                            prompt=prompt,
                            model=model,
                            timeout_seconds=timeout_seconds,
                        )
                    except Exception as exc:  # pragma: no cover - defensive runner guard
                        result = blocked_result(f"codex runner failed: {exc}", outcome_class="runtime_failure")
                    dirty_after = git_dirty_paths(target_root)
                    actual_changed_files = git_changed_files(target_root)
                    if actual_changed_files and not result.changed_files:
                        result = replace(result, changed_files=actual_changed_files)
                    if result.status != "completed":
                        if branch_before and not dirty_after:
                            restore_attempted = True
                            restored, restore_error = switch_branch(target_root, branch_before)
                            if restored:
                                restore_result = f"restored to {branch_before}"
                            else:
                                restore_result = f"restore failed: {restore_error}"
                        elif not branch_before:
                            restore_result = "skipped; original branch unknown"
                        else:
                            restore_result = "skipped; target worktree has changes: " + "; ".join(dirty_after)
                    branch_after = git_current_branch(target_root)

    outcome_class = outcome_class_for_result(execute=execute, result=result)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_target_codex_run",
        "generated_at": utc_timestamp(),
        "status": result.status,
        "outcome_class": outcome_class,
        "execute_requested": execute,
        "root": str(root),
        "project_key": project_key,
        "project": plan.get("project", {}),
        "candidate_index": candidate_index,
        "branch": branch,
        "branch_before": branch_before,
        "branch_created": branch_created,
        "branch_after": branch_after,
        "restore_attempted": restore_attempted,
        "restore_result": restore_result,
        "codex": {
            "model": model,
            "timeout_seconds": timeout_seconds,
            "thread_id": result.thread_id,
            "session_id": result.session_id,
            "final_response": result.final_response,
            "raw_event_count": len(result.raw_events),
            "process_returncode": result.process_returncode,
            "stderr_tail": result.stderr_tail,
        },
        "changed_files": result.changed_files,
        "verification_results": result.verification_results,
        "repair_attempts": result.repair_attempts,
        "stop_reason": result.stop_reason,
        "task_contract": plan.get("task_contract"),
        "plan_status": plan.get("status"),
        "plan_blocker": plan.get("blocker"),
        "recorded_run_path": str(artifact),
    }
    write_run_artifact(artifact, payload)
    return payload


def write_run_artifact(path: Path, payload: dict[str, Any]) -> Path:
    if path.exists():
        raise FileExistsError(f"run artifact already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(payload), encoding="utf-8")
    return path


def render_markdown(payload: dict[str, Any]) -> str:
    project = payload.get("project", {})
    contract = payload.get("task_contract") or {}
    candidate = contract.get("selected_candidate") or {}
    lines = [
        "# Target Codex Run",
        "",
        f"- status: `{payload.get('status')}`",
        f"- outcome_class: `{payload.get('outcome_class')}`",
        f"- project_key: `{payload.get('project_key')}`",
        f"- project_id: `{project.get('project_id', '')}`",
        f"- project_root: `{project.get('resolved_path', '')}`",
        f"- branch: `{payload.get('branch')}`",
        f"- branch_before: `{payload.get('branch_before')}`",
        f"- branch_created: `{payload.get('branch_created')}`",
        f"- branch_after: `{payload.get('branch_after')}`",
        f"- restore_attempted: `{payload.get('restore_attempted')}`",
        f"- restore_result: `{payload.get('restore_result')}`",
        f"- execute_requested: `{payload.get('execute_requested')}`",
        f"- recorded_run_path: `{payload.get('recorded_run_path')}`",
        "",
        "## Selected Candidate",
        "",
        f"- title: {candidate.get('title', 'none')}",
        f"- source: `{candidate.get('source', '')}`",
        f"- work_type: `{candidate.get('work_type', '')}`",
        "",
        "## Codex",
        "",
        f"- model: `{payload.get('codex', {}).get('model')}`",
        f"- timeout_seconds: `{payload.get('codex', {}).get('timeout_seconds')}`",
        f"- thread_id: `{payload.get('codex', {}).get('thread_id')}`",
        f"- session_id: `{payload.get('codex', {}).get('session_id')}`",
        f"- process_returncode: `{payload.get('codex', {}).get('process_returncode')}`",
        f"- raw_event_count: `{payload.get('codex', {}).get('raw_event_count')}`",
        "",
        "## App Server Stderr Tail",
        "",
        *bullet_lines(payload.get("codex", {}).get("stderr_tail", [])),
        "",
        "## Changed Files",
        "",
        *bullet_lines(payload.get("changed_files", [])),
        "",
        "## Verification",
        "",
        *bullet_lines(payload.get("verification_results", [])),
        "",
        "## Repair Attempts",
        "",
        f"- {payload.get('repair_attempts', 0)}",
        "",
        "## Stop Or Failure Reason",
        "",
        f"- {payload.get('stop_reason') or 'none'}",
        "",
        "## Final Response",
        "",
        str(payload.get("codex", {}).get("final_response") or "none"),
        "",
    ]
    return "\n".join(lines)


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- `{item}`" for item in items] or ["- none"]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        payload = build_orchestration_payload(
            root,
            project_id=args.project_id,
            project_root=args.project_root,
            project_name=args.project_name,
            candidate_index=args.candidate_index,
            limit=args.limit,
            timestamp=args.timestamp,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
            execute=args.execute,
            branch_name=args.branch_name,
        )
    except (FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    write_json_or_markdown(payload, args.format, render_markdown)
    return exit_code_for_payload(payload)


if __name__ == "__main__":
    raise SystemExit(main())
