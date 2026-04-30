"""Codex app-server stdio session helpers for target-project runs."""

from __future__ import annotations

from collections import deque
import json
import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Protocol, TextIO


FINAL_STATUSES = {"completed", "failed", "blocked", "stopped"}
STDERR_TAIL_LIMIT = 20


class AppServerTimeoutError(RuntimeError):
    """Raised when the app-server session exceeds its shared timeout budget."""


class AppServerProtocolError(RuntimeError):
    """Raised when app-server stdio closes or emits malformed data."""


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
    outcome_class: str = ""
    process_returncode: int | None = None
    stderr_tail: list[str] = field(default_factory=list)


class CodexRunner(Protocol):
    def run(self, *, cwd: Path, prompt: str, model: str, timeout_seconds: int) -> CodexRunResult:
        """Run Codex in cwd and return a normalized result."""


def git_changed_files(cwd: Path) -> list[str]:
    process = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if process.returncode != 0:
        return []
    return [line.strip() for line in process.stdout.splitlines() if line.strip()]


def blocked_result(
    reason: str,
    raw_events: list[dict[str, Any]] | None = None,
    *,
    outcome_class: str = "blocked_by_policy",
    process_returncode: int | None = None,
    stderr_tail: list[str] | None = None,
) -> CodexRunResult:
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
        outcome_class=outcome_class,
        process_returncode=process_returncode,
        stderr_tail=stderr_tail or [],
    )


def terminate_process(process: subprocess.Popen[str]) -> int | None:
    if process.poll() is None:
        process.terminate()
        try:
            return process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                return process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                return process.poll()
    return process.poll()


class AppServerCodexRunner:
    """Small JSON-RPC client for `codex app-server` stdio transport."""

    def __init__(self, command: list[str] | None = None) -> None:
        self.command = command or ["codex", "app-server"]

    def run(self, *, cwd: Path, prompt: str, model: str, timeout_seconds: int) -> CodexRunResult:
        client = _AppServerSession(self.command, cwd, timeout_seconds)
        return client.run(prompt=prompt, model=model)


class _Deadline:
    def __init__(self, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds
        self.expires_at = time.monotonic() + max(timeout_seconds, 0)

    def remaining(self) -> float:
        return max(0.0, self.expires_at - time.monotonic())

    def require_time(self) -> float:
        remaining = self.remaining()
        if remaining <= 0:
            raise AppServerTimeoutError(
                f"codex app-server timed out after {self.timeout_seconds} seconds"
            )
        return remaining


class _LineQueueReader:
    def __init__(self, stream: TextIO | None) -> None:
        self.stream = stream
        self.lines: queue.Queue[str | BaseException | None] = queue.Queue()
        self.thread = threading.Thread(target=self._run, name="selfdex-app-server-stdout", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def read_line(self, deadline: _Deadline) -> str | None:
        try:
            item = self.lines.get(timeout=deadline.require_time())
        except queue.Empty as exc:
            raise AppServerTimeoutError(
                f"codex app-server timed out after {deadline.timeout_seconds} seconds"
            ) from exc
        if isinstance(item, BaseException):
            raise AppServerProtocolError(f"codex app-server stdout read failed: {item}") from item
        return item

    def _run(self) -> None:
        if self.stream is None:
            self.lines.put(None)
            return
        try:
            while True:
                line = self.stream.readline()
                if line == "":
                    break
                self.lines.put(line)
        except BaseException as exc:  # pragma: no cover - defensive reader guard
            self.lines.put(exc)
        finally:
            self.lines.put(None)


class _StderrTailReader:
    def __init__(self, stream: TextIO | None, limit: int = STDERR_TAIL_LIMIT) -> None:
        self.stream = stream
        self.tail: deque[str] = deque(maxlen=limit)
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._run, name="selfdex-app-server-stderr", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def lines(self) -> list[str]:
        with self.lock:
            return list(self.tail)

    def join(self, timeout: float = 0.1) -> None:
        self.thread.join(timeout=timeout)

    def _run(self) -> None:
        if self.stream is None:
            return
        try:
            while True:
                line = self.stream.readline()
                if line == "":
                    break
                with self.lock:
                    self.tail.append(line.rstrip("\r\n"))
        except OSError as exc:
            with self.lock:
                self.tail.append(f"<stderr read failed: {exc}>")


class _AppServerSession:
    def __init__(self, command: list[str], cwd: Path, timeout_seconds: int) -> None:
        self.command = command
        self.cwd = cwd
        self.timeout_seconds = timeout_seconds
        self.next_id = 1
        self.events: list[dict[str, Any]] = []
        self.final_chunks: list[str] = []

    def run(self, *, prompt: str, model: str) -> CodexRunResult:
        deadline = _Deadline(self.timeout_seconds)
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
            return blocked_result(
                f"codex app-server failed to start: {exc}",
                outcome_class="runtime_failure",
            )

        stdout_reader = _LineQueueReader(process.stdout)
        stderr_reader = _StderrTailReader(process.stderr)
        stdout_reader.start()
        stderr_reader.start()
        result: CodexRunResult
        try:
            self._send(
                process,
                stdout_reader,
                deadline,
                "initialize",
                {"clientInfo": {"name": "selfdex", "title": "Selfdex", "version": "0.1.0"}},
            )
            self._send_notification(process, "initialized", {})
            thread_response = self._send(process, stdout_reader, deadline, "thread/start", {"model": model})
            if thread_response.get("error"):
                result = blocked_result(
                    f"codex app-server thread/start failed: {json.dumps(thread_response['error'], ensure_ascii=False)}",
                    self.events,
                    outcome_class="runtime_failure",
                )
            else:
                thread_id = str(thread_response.get("result", {}).get("thread", {}).get("id") or "")
                if not thread_id:
                    result = blocked_result(
                        "codex app-server did not return a thread id",
                        self.events,
                        outcome_class="runtime_failure",
                    )
                else:
                    turn_response = self._send(
                        process,
                        stdout_reader,
                        deadline,
                        "turn/start",
                        {
                            "threadId": thread_id,
                            "cwd": str(self.cwd),
                            "input": [{"type": "text", "text": prompt}],
                        },
                    )
                    if turn_response.get("error"):
                        result = blocked_result(
                            f"codex app-server turn/start failed: {json.dumps(turn_response['error'], ensure_ascii=False)}",
                            self.events,
                            outcome_class="runtime_failure",
                        )
                    else:
                        status, stop_reason = self._read_until_turn_done(stdout_reader, deadline)
                        result = CodexRunResult(
                            status=status,
                            thread_id=thread_id,
                            session_id=thread_id,
                            final_response="".join(self.final_chunks).strip(),
                            changed_files=git_changed_files(self.cwd),
                            verification_results=[],
                            repair_attempts=0,
                            stop_reason=stop_reason,
                            raw_events=self.events,
                            outcome_class="success" if status == "completed" else "runtime_failure",
                            process_returncode=process.poll(),
                        )
        except AppServerTimeoutError as exc:
            result = blocked_result(str(exc), self.events, outcome_class="runtime_failure")
        except (AppServerProtocolError, BrokenPipeError, OSError, RuntimeError) as exc:
            result = blocked_result(
                f"codex app-server runtime failure: {exc}",
                self.events,
                outcome_class="runtime_failure",
            )
        finally:
            returncode = terminate_process(process)
            stderr_reader.join()
        return replace(
            result,
            process_returncode=returncode if result.process_returncode is None else result.process_returncode,
            stderr_tail=stderr_reader.lines(),
        )

    def _send(
        self,
        process: subprocess.Popen[str],
        stdout_reader: _LineQueueReader,
        deadline: _Deadline,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        message_id = self.next_id
        self.next_id += 1
        self._write(process, {"method": method, "id": message_id, "params": params})
        return self._read_response(stdout_reader, deadline, message_id)

    def _send_notification(self, process: subprocess.Popen[str], method: str, params: dict[str, Any]) -> None:
        self._write(process, {"method": method, "params": params})

    def _write(self, process: subprocess.Popen[str], message: dict[str, Any]) -> None:
        if process.stdin is None:
            raise RuntimeError("codex app-server stdin is unavailable")
        process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def _read_response(
        self,
        stdout_reader: _LineQueueReader,
        deadline: _Deadline,
        message_id: int,
    ) -> dict[str, Any]:
        while True:
            event = self._read_event(stdout_reader, deadline, "waiting for response")
            if event.get("id") == message_id:
                return event

    def _read_until_turn_done(self, stdout_reader: _LineQueueReader, deadline: _Deadline) -> tuple[str, str]:
        while True:
            event = self._read_event(stdout_reader, deadline, "waiting for turn completion")
            if event.get("method") == "turn/completed":
                params = event.get("params", {})
                turn = params.get("turn", {}) if isinstance(params, dict) else {}
                status = str(turn.get("status") or params.get("status") or "completed")
                if status not in FINAL_STATUSES:
                    status = "completed"
                return status, str(turn.get("error") or params.get("error") or "")

    def _read_event(
        self,
        stdout_reader: _LineQueueReader,
        deadline: _Deadline,
        context: str,
    ) -> dict[str, Any]:
        line = stdout_reader.read_line(deadline)
        if line is None:
            raise AppServerProtocolError(f"codex app-server closed stdout while {context}")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AppServerProtocolError(f"codex app-server emitted invalid JSON while {context}: {exc.msg}") from exc
        if not isinstance(event, dict):
            raise AppServerProtocolError(f"codex app-server emitted non-object JSON while {context}")
        self._capture_event(event)
        return event

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
