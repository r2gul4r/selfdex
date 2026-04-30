#!/usr/bin/env python3
"""Run one target-project Codex task from a Selfdex plan."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from argparse_utils import add_format_argument, add_root_argument
    from cli_output_utils import write_json_or_markdown
    from plan_external_project import build_plan, slugify
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.plan_external_project import build_plan, slugify


SCHEMA_VERSION = 1
FINAL_STATUSES = {"completed", "failed", "blocked", "stopped"}


@dataclass(frozen=True)
class CodexRunResult:
    status: str
    thread_id: str
    session_id: str
    final_response: str
    changed_files: list[str]
    verification_results: list[str]
    repair_attempts: int
    stop_reason: str
    raw_events: list[dict[str, Any]]


class CodexRunner(Protocol):
    def run(self, *, cwd: Path, prompt: str, model: str, timeout_seconds: int) -> CodexRunResult:
        """Run Codex in cwd and return a normalized result."""


class AppServerCodexRunner:
    """Small JSON-RPC client for `codex app-server` stdio transport."""

    def __init__(self, command: list[str] | None = None) -> None:
        self.command = command or ["codex", "app-server"]

    def run(self, *, cwd: Path, prompt: str, model: str, timeout_seconds: int) -> CodexRunResult:
        client = _AppServerSession(self.command, cwd, timeout_seconds)
        return client.run(prompt=prompt, model=model)


class _AppServerSession:
    def __init__(self, command: list[str], cwd: Path, timeout_seconds: int) -> None:
        self.command = command
        self.cwd = cwd
        self.timeout_seconds = timeout_seconds
        self.next_id = 1
        self.events: list[dict[str, Any]] = []
        self.final_chunks: list[str] = []

    def run(self, *, prompt: str, model: str) -> CodexRunResult:
        try:
            process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except OSError as exc:
            return blocked_result(f"codex app-server failed to start: {exc}")

        try:
            self._send(process, "initialize", {"clientInfo": {"name": "selfdex", "title": "Selfdex", "version": "0.1.0"}})
            self._send_notification(process, "initialized", {})
            thread_response = self._send(process, "thread/start", {"model": model})
            thread_id = str(thread_response.get("result", {}).get("thread", {}).get("id") or "")
            if not thread_id:
                return blocked_result("codex app-server did not return a thread id", self.events)
            self._send(
                process,
                "turn/start",
                {
                    "threadId": thread_id,
                    "cwd": str(self.cwd),
                    "input": [{"type": "text", "text": prompt}],
                },
            )
            status, stop_reason = self._read_until_turn_done(process)
            return CodexRunResult(
                status=status,
                thread_id=thread_id,
                session_id=thread_id,
                final_response="".join(self.final_chunks).strip(),
                changed_files=git_changed_files(self.cwd),
                verification_results=[],
                repair_attempts=0,
                stop_reason=stop_reason,
                raw_events=self.events,
            )
        finally:
            terminate_process(process)

    def _send(self, process: subprocess.Popen[str], method: str, params: dict[str, Any]) -> dict[str, Any]:
        message_id = self.next_id
        self.next_id += 1
        self._write(process, {"method": method, "id": message_id, "params": params})
        return self._read_response(process, message_id)

    def _send_notification(self, process: subprocess.Popen[str], method: str, params: dict[str, Any]) -> None:
        self._write(process, {"method": method, "params": params})

    def _write(self, process: subprocess.Popen[str], message: dict[str, Any]) -> None:
        if process.stdin is None:
            raise RuntimeError("codex app-server stdin is unavailable")
        process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def _read_response(self, process: subprocess.Popen[str], message_id: int) -> dict[str, Any]:
        if process.stdout is None:
            return {"error": {"message": "codex app-server stdout is unavailable"}}
        while True:
            line = process.stdout.readline()
            if not line:
                return {"error": {"message": "codex app-server closed stdout"}}
            event = json.loads(line)
            self._capture_event(event)
            if event.get("id") == message_id:
                return event

    def _read_until_turn_done(self, process: subprocess.Popen[str]) -> tuple[str, str]:
        if process.stdout is None:
            return "failed", "codex app-server stdout is unavailable"
        while True:
            line = process.stdout.readline()
            if not line:
                return "failed", "codex app-server closed stdout before turn completed"
            event = json.loads(line)
            self._capture_event(event)
            if event.get("method") == "turn/completed":
                params = event.get("params", {})
                turn = params.get("turn", {}) if isinstance(params, dict) else {}
                status = str(turn.get("status") or params.get("status") or "completed")
                if status not in FINAL_STATUSES:
                    status = "completed"
                return status, str(turn.get("error") or params.get("error") or "")

    def _capture_event(self, event: dict[str, Any]) -> None:
        self.events.append(event)
        method = str(event.get("method") or "")
        params = event.get("params", {})
        if method == "item/agentMessage/delta" and isinstance(params, dict):
            delta = params.get("delta")
            if isinstance(delta, str):
                self.final_chunks.append(delta)
        if method == "item/completed" and isinstance(params, dict):
            item = params.get("item", {})
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    self.final_chunks.append(text)


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


def git_changed_files(cwd: Path) -> list[str]:
    process = git_output(cwd, ["diff", "--name-only"])
    if process.returncode != 0:
        return []
    return [line.strip() for line in process.stdout.splitlines() if line.strip()]


def git_is_repo(cwd: Path) -> bool:
    return git_output(cwd, ["rev-parse", "--is-inside-work-tree"]).returncode == 0


def git_dirty_paths(cwd: Path) -> list[str]:
    process = git_output(cwd, ["status", "--short"])
    if process.returncode != 0:
        return ["<git status failed>"]
    return [line.strip() for line in process.stdout.splitlines() if line.strip()]


def create_branch(cwd: Path, branch_name: str) -> tuple[bool, str]:
    process = git_output(cwd, ["switch", "-c", branch_name])
    if process.returncode == 0:
        return True, ""
    return False, process.stderr.strip() or process.stdout.strip() or "git switch failed"


def blocked_result(reason: str, raw_events: list[dict[str, Any]] | None = None) -> CodexRunResult:
    return CodexRunResult(
        status="blocked",
        thread_id="",
        session_id="",
        final_response="",
        changed_files=[],
        verification_results=[],
        repair_attempts=0,
        stop_reason=reason,
        raw_events=raw_events or [],
    )


def terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


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

    if plan.get("status") != "ready":
        result = blocked_result(str(plan.get("blocker") or "plan is not ready"))
    elif execute:
        if not target_root.exists():
            result = blocked_result("target project path does not exist")
        elif not git_is_repo(target_root):
            result = blocked_result("target project is not a git repository")
        else:
            dirty = git_dirty_paths(target_root)
            if dirty:
                result = blocked_result("target project worktree is dirty: " + "; ".join(dirty))
            else:
                ok, error = create_branch(target_root, branch)
                branch_created = ok
                if not ok:
                    result = blocked_result(f"could not create target branch: {error}")
                else:
                    codex_runner = runner or AppServerCodexRunner()
                    prompt = str(plan["task_contract"]["codex_execution_prompt"])
                    result = codex_runner.run(
                        cwd=target_root,
                        prompt=prompt,
                        model=model,
                        timeout_seconds=timeout_seconds,
                    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_target_codex_run",
        "generated_at": utc_timestamp(),
        "status": result.status,
        "execute_requested": execute,
        "root": str(root),
        "project_key": project_key,
        "project": plan.get("project", {}),
        "candidate_index": candidate_index,
        "branch": branch,
        "branch_created": branch_created,
        "codex": {
            "model": model,
            "thread_id": result.thread_id,
            "session_id": result.session_id,
            "final_response": result.final_response,
            "raw_event_count": len(result.raw_events),
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
        f"- project_key: `{payload.get('project_key')}`",
        f"- project_id: `{project.get('project_id', '')}`",
        f"- project_root: `{project.get('resolved_path', '')}`",
        f"- branch: `{payload.get('branch')}`",
        f"- branch_created: `{payload.get('branch_created')}`",
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
        f"- thread_id: `{payload.get('codex', {}).get('thread_id')}`",
        f"- session_id: `{payload.get('codex', {}).get('session_id')}`",
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
    return 0 if payload["status"] in {"completed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
