#!/usr/bin/env python3
"""Check whether a Selfdex task is ready for the commit gate."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from argparse_utils import add_format_argument, add_root_argument
    from check_campaign_budget import build_payload as build_campaign_budget_payload
    from cli_output_utils import write_json_or_markdown
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.check_campaign_budget import build_payload as build_campaign_budget_payload
    from scripts.cli_output_utils import write_json_or_markdown


CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([a-z0-9._-]+\))?(!)?: .+"
)
READY_PHASES = {"local_verified", "reviewed", "commit_ready", "completed"}
BLOCKING_REVIEW_WORDS = ("pending", "not_started", "blocked", "failed", "p0", "p1")
BLOCKING_VERIFICATION_WORDS = ("fail", "failed", "error", "blocked")


@dataclass(frozen=True)
class GateFinding:
    finding_id: str
    severity: str
    summary: str
    evidence: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "summary": self.summary,
            "evidence": self.evidence,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Selfdex commit-gate readiness.")
    add_root_argument(parser, help_text="Selfdex repository root.")
    parser.add_argument("--commit-message", required=True, help="Proposed Conventional Commit message.")
    parser.add_argument(
        "--stage",
        choices=("pre-commit", "post-push"),
        default="pre-commit",
        help="Gate stage to evaluate. Defaults to pre-commit.",
    )
    parser.add_argument(
        "--github-status",
        choices=("unknown", "pending", "pass", "fail"),
        default="unknown",
        help="GitHub Actions status for post-push evaluation.",
    )
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="Changed path to validate instead of relying only on git diff. May be repeated.",
    )
    parser.add_argument(
        "--include-git-diff",
        action="store_true",
        default=True,
        help="Include git diff, cached diff, and untracked paths. Enabled by default.",
    )
    parser.add_argument(
        "--no-git-diff",
        action="store_false",
        dest="include_git_diff",
        help="Use only --changed-path values.",
    )
    parser.add_argument(
        "--allow-hard-approval",
        action="store_true",
        help="Allow hard-approval path hints after explicit approval.",
    )
    add_format_argument(parser, default="markdown", help_text="Output format. Defaults to markdown.")
    return parser.parse_args(argv)


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def state_review_text(state: dict[str, Any]) -> str:
    reviewer = state.get("reviewer")
    if not isinstance(reviewer, dict):
        return ""
    return " ".join(
        str(reviewer.get(field) or "")
        for field in ("reviewer", "reviewer_mode", "reviewer_result")
    ).strip()


def verification_entries(state: dict[str, Any]) -> list[str]:
    last_update = state.get("last_update")
    if not isinstance(last_update, dict):
        return []
    values = last_update.get("verification_result")
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def has_blocking_review(review_text: str) -> bool:
    lower = review_text.lower()
    lower = re.sub(r"\bno\s+p0\s*/\s*p1\b", "", lower)
    lower = re.sub(r"\bno\s+p[01]\b", "", lower)
    lower = lower.replace("no p0 or p1", "")
    return any(word in lower for word in BLOCKING_REVIEW_WORDS)


def has_blocking_verification(entries: list[str]) -> bool:
    for entry in entries:
        lower = entry.lower()
        if "expected fail" in lower or "expected failure" in lower:
            continue
        if any(word in lower for word in BLOCKING_VERIFICATION_WORDS):
            return True
    return False


def changed_path_count(budget_payload: dict[str, Any]) -> int:
    return len(budget_payload.get("changed_paths", []))


def budget_findings(budget_payload: dict[str, Any]) -> list[GateFinding]:
    findings: list[GateFinding] = []
    for violation in budget_payload.get("violations", []):
        findings.append(
            GateFinding(
                finding_id=f"budget-{violation.get('violation_id', 'violation')}",
                severity=str(violation.get("severity") or "high"),
                summary=str(violation.get("message") or "Campaign budget violation."),
                evidence=str(violation.get("evidence") or ""),
            )
        )
    for warning in budget_payload.get("mirror_warnings", []):
        findings.append(
            GateFinding(
                finding_id=f"budget-{warning.get('warning_id', 'mirror-warning')}",
                severity="high",
                summary="Structured JSON and markdown mirrors differ; fix state drift before committing.",
                evidence=f"{warning.get('source', '')}:{warning.get('field', '')}",
            )
        )
    return findings


def build_payload(
    root: Path,
    *,
    commit_message: str,
    stage: str = "pre-commit",
    github_status: str = "unknown",
    changed_paths: list[str] | None = None,
    include_git_diff: bool = True,
    allow_hard_approval: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    state_path = root / "STATE.json"
    state = read_json_object(state_path)
    current_task = state.get("current_task") if isinstance(state.get("current_task"), dict) else {}
    phase = str(current_task.get("phase") or "")
    reviewer_text = state_review_text(state)
    verification = verification_entries(state)
    budget_payload = build_campaign_budget_payload(
        root,
        changed_paths or [],
        include_git_diff=include_git_diff,
        allow_hard_approval=allow_hard_approval,
    )

    findings = budget_findings(budget_payload)
    if phase not in READY_PHASES:
        findings.append(
            GateFinding(
                "state-not-ready",
                "high",
                "STATE.json phase is not ready for commit.",
                phase,
            )
        )
    if not reviewer_text:
        findings.append(
            GateFinding("missing-review", "high", "Reviewer status is missing from STATE.json.")
        )
    elif has_blocking_review(reviewer_text):
        findings.append(
            GateFinding("blocking-review", "high", "Reviewer status still contains a blocking state.", reviewer_text)
        )
    if not verification:
        findings.append(
            GateFinding("missing-verification", "high", "Verification evidence is required before commit.")
        )
    elif has_blocking_verification(verification):
        findings.append(
            GateFinding(
                "blocking-verification",
                "high",
                "Verification evidence contains a blocking failure word.",
                "; ".join(verification),
            )
        )
    if not CONVENTIONAL_COMMIT_RE.match(commit_message.strip()):
        findings.append(
            GateFinding(
                "non-conventional-commit",
                "high",
                "Commit message must use Conventional Commits format.",
                commit_message,
            )
        )
    if stage == "pre-commit" and changed_path_count(budget_payload) == 0:
        findings.append(
            GateFinding("nothing-to-commit", "medium", "No changed paths were found for the pre-commit gate.")
        )
    if stage == "post-push" and github_status != "pass":
        findings.append(
            GateFinding(
                "github-check-not-passing",
                "high",
                "Post-push gate requires passing GitHub Actions status.",
                github_status,
            )
        )

    high_findings = [finding for finding in findings if finding.severity == "high"]
    status = "pass" if not high_findings else "fail"
    readiness = "blocked"
    if status == "pass":
        readiness = "post_push_ready" if stage == "post-push" else "pre_commit_ready"

    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_commit_gate_check",
        "root": str(root),
        "status": status,
        "readiness": readiness,
        "stage": stage,
        "github_status": github_status,
        "commit_message": commit_message,
        "conventional_commit": bool(CONVENTIONAL_COMMIT_RE.match(commit_message.strip())),
        "task": current_task.get("task", ""),
        "phase": phase,
        "reviewer_text": reviewer_text,
        "verification_count": len(verification),
        "changed_path_count": changed_path_count(budget_payload),
        "budget_status": budget_payload.get("status"),
        "finding_count": len(findings),
        "findings": [finding.to_dict() for finding in findings],
        "budget_check": budget_payload,
        "next_step": next_step(status, stage),
    }


def next_step(status: str, stage: str) -> str:
    if status != "pass":
        return "Stop the loop. Fix the blocking findings before committing or selecting the next task."
    if stage == "post-push":
        return "Record the passing GitHub check, close the run, then select the next candidate."
    return "Commit with the approved message, push if policy allows, then run the post-push GitHub check."


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Commit Gate Check",
        "",
        f"- status: `{payload['status']}`",
        f"- readiness: `{payload['readiness']}`",
        f"- stage: `{payload['stage']}`",
        f"- task: `{payload['task']}`",
        f"- phase: `{payload['phase']}`",
        f"- commit_message: `{payload['commit_message']}`",
        f"- changed_path_count: `{payload['changed_path_count']}`",
        f"- verification_count: `{payload['verification_count']}`",
        f"- budget_status: `{payload['budget_status']}`",
        "",
        "## Findings",
        "",
    ]
    for finding in payload["findings"]:
        lines.append(
            f"- `{finding['finding_id']}` {finding['severity']}: "
            f"{finding['summary']} ({finding['evidence']})"
        )
    if not payload["findings"]:
        lines.append("- none")
    lines.extend(["", "## Next Step", "", payload["next_step"], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_payload(
            Path(args.root),
            commit_message=args.commit_message,
            stage=args.stage,
            github_status=args.github_status,
            changed_paths=list(args.changed_path),
            include_git_diff=args.include_git_diff,
            allow_hard_approval=args.allow_hard_approval,
        )
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json_or_markdown(payload, args.format, render_markdown)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
