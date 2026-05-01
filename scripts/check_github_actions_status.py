#!/usr/bin/env python3
"""Check GitHub Actions status for a pushed commit."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from cli_output_utils import write_json_or_markdown
except ModuleNotFoundError:
    from scripts.cli_output_utils import write_json_or_markdown


API_ROOT = "https://api.github.com"
GITHUB_REMOTE_PATTERNS = (
    re.compile(r"^https://github\.com/(?P<repo>[^/]+/[^/.]+)(?:\.git)?/?$"),
    re.compile(r"^git@github\.com:(?P<repo>[^/]+/[^/.]+)(?:\.git)?$"),
)
FAILURE_CONCLUSIONS = {
    "action_required",
    "cancelled",
    "failure",
    "neutral",
    "skipped",
    "stale",
    "startup_failure",
    "timed_out",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check GitHub Actions status for a commit.")
    parser.add_argument("--root", default=".", help="Repository root used to infer repo and sha.")
    parser.add_argument("--repo", help="GitHub repository in owner/name form. Defaults to origin remote.")
    parser.add_argument("--sha", help="Commit SHA. Defaults to HEAD.")
    parser.add_argument("--branch", help="Optional branch filter.")
    parser.add_argument("--event", default="push", help="Optional event filter. Defaults to push.")
    parser.add_argument("--per-page", type=int, default=20, help="Maximum workflow runs to inspect.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format.")
    return parser.parse_args(argv)


def git_output(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


def parse_github_repo(remote_url: str) -> str | None:
    for pattern in GITHUB_REMOTE_PATTERNS:
        match = pattern.match(remote_url.strip())
        if match:
            return match.group("repo")
    return None


def infer_repo(root: Path) -> str:
    remote = git_output(root, ["config", "--get", "remote.origin.url"])
    repo = parse_github_repo(remote)
    if repo is None:
        raise RuntimeError(f"remote.origin.url is not a supported GitHub remote: {remote}")
    return repo


def infer_sha(root: Path) -> str:
    return git_output(root, ["rev-parse", "HEAD"])


def request_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "selfdex-github-actions-status",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_json(url: str, token: str | None = None) -> dict[str, Any]:
    request = Request(url, headers=request_headers(token))
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach GitHub API: {exc.reason}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub API returned a non-object payload")
    return payload


def workflow_runs_url(
    *,
    repo: str,
    sha: str,
    branch: str | None,
    event: str | None,
    per_page: int,
) -> str:
    query: dict[str, str] = {
        "head_sha": sha,
        "per_page": str(max(1, min(per_page, 100))),
    }
    if branch:
        query["branch"] = branch
    if event:
        query["event"] = event
    return f"{API_ROOT}/repos/{repo}/actions/runs?{urlencode(query)}"


def normalize_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": run.get("id"),
        "name": run.get("name") or run.get("workflow_name") or "",
        "event": run.get("event") or "",
        "status": run.get("status") or "",
        "conclusion": run.get("conclusion") or "",
        "head_branch": run.get("head_branch") or "",
        "head_sha": run.get("head_sha") or "",
        "html_url": run.get("html_url") or "",
        "created_at": run.get("created_at") or "",
        "updated_at": run.get("updated_at") or "",
    }


def classify_runs(runs: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    if not runs:
        findings.append(
            {
                "finding_id": "no-workflow-run",
                "severity": "medium",
                "summary": "No GitHub Actions workflow run was found for the commit yet.",
            }
        )
        return "pending", findings

    pending = [run for run in runs if run["status"] != "completed"]
    if pending:
        findings.append(
            {
                "finding_id": "workflow-pending",
                "severity": "medium",
                "summary": f"{len(pending)} workflow run(s) are not completed yet.",
            }
        )
        return "pending", findings

    failed = [
        run
        for run in runs
        if run["conclusion"] in FAILURE_CONCLUSIONS or run["conclusion"] != "success"
    ]
    if failed:
        for run in failed:
            findings.append(
                {
                    "finding_id": "workflow-failed",
                    "severity": "high",
                    "summary": f"{run['name']} concluded {run['conclusion'] or 'unknown'}: {run['html_url']}",
                }
            )
        return "fail", findings

    return "pass", findings


def build_payload(
    *,
    root: Path,
    repo: str | None,
    sha: str | None,
    branch: str | None,
    event: str | None,
    per_page: int,
    token: str | None,
) -> dict[str, Any]:
    root = root.resolve()
    resolved_repo = repo or infer_repo(root)
    resolved_sha = sha or infer_sha(root)
    url = workflow_runs_url(
        repo=resolved_repo,
        sha=resolved_sha,
        branch=branch,
        event=event,
        per_page=per_page,
    )
    payload = fetch_json(url, token=token)
    raw_runs = payload.get("workflow_runs")
    runs = [normalize_run(run) for run in raw_runs if isinstance(run, dict)] if isinstance(raw_runs, list) else []
    status, findings = classify_runs(runs)
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_github_actions_status",
        "status": status,
        "repo": resolved_repo,
        "sha": resolved_sha,
        "branch": branch or "",
        "event": event or "",
        "run_count": len(runs),
        "finding_count": len(findings),
        "findings": findings,
        "runs": runs,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GitHub Actions Status",
        "",
        f"- status: `{payload['status']}`",
        f"- repo: `{payload['repo']}`",
        f"- sha: `{payload['sha']}`",
        f"- run_count: `{payload['run_count']}`",
        "",
        "## Runs",
        "",
    ]
    for run in payload["runs"]:
        lines.append(
            f"- `{run['name']}` status=`{run['status']}` conclusion=`{run['conclusion']}` url={run['html_url']}"
        )
    if not payload["runs"]:
        lines.append("- none")
    lines.extend(["", "## Findings", ""])
    for finding in payload["findings"]:
        lines.append(f"- `{finding['finding_id']}` {finding['summary']}")
    if not payload["findings"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or None
    try:
        payload = build_payload(
            root=Path(args.root),
            repo=args.repo,
            sha=args.sha,
            branch=args.branch,
            event=args.event,
            per_page=args.per_page,
            token=token,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    write_json_or_markdown(payload, args.format, render_markdown)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
