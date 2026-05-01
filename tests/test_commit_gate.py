from __future__ import annotations

import json
import shutil
import unittest
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = ROOT / "tmp" / "test-commit-gate"
check_commit_gate = load_script("check_commit_gate.py")


@contextmanager
def temporary_workspace() -> Iterator[Path]:
    TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEST_TEMP_ROOT / f"case-{uuid.uuid4().hex}"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_campaign(root: Path) -> None:
    write_json(
        root / "CAMPAIGN_STATE.json",
        {
            "campaign": {
                "subagent_runtime": "official_codex_native_subagents",
                "max_subagent_threads": 4,
            },
            "hard_approval_zones": [
                "destructive Git or filesystem operations",
                "secrets, credentials, private keys, or token access",
                "paid API calls",
                "public deployment",
                "database migration or production write",
                "cross-workspace edits",
            ],
        },
    )


def write_stale_campaign_mirror(root: Path) -> None:
    (root / "CAMPAIGN_STATE.md").write_text(
        "\n".join(
            [
                "# Campaign State",
                "",
                "## Campaign",
                "",
                "- subagent_runtime: `legacy_runtime`",
                "- max_subagent_threads: `4`",
                "",
                "## Hard Approval Zones",
                "",
                "- destructive Git or filesystem operations",
                "- secrets, credentials, private keys, or token access",
                "- paid API calls",
                "- public deployment",
                "- database migration or production write",
                "- cross-workspace edits",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_state(
    root: Path,
    *,
    phase: str = "local_verified",
    reviewer_result: str = "No P0/P1 findings.",
    verification: list[str] | None = None,
    write_paths: list[str] | None = None,
) -> None:
    write_json(
        root / "STATE.json",
        {
            "current_task": {
                "task": "fixture-task",
                "phase": phase,
            },
            "orchestration_profile": {
                "selected_agents": ["main", "reviewer"],
                "subagent_permission": "@selfdex invocation is explicit permission.",
            },
            "writer_slot": {
                "write_sets": {
                    "main": write_paths or ["README.md", "STATE.json"],
                },
            },
            "reviewer": {
                "reviewer": "not_required",
                "reviewer_result": reviewer_result,
            },
            "last_update": {
                "verification_result": verification
                if verification is not None
                else ["python -m unittest discover -s tests: pass"],
            },
        },
    )


class CommitGateTests(unittest.TestCase):
    def test_pre_commit_ready_when_contract_review_and_verification_pass(self) -> None:
        with temporary_workspace() as root:
            write_campaign(root)
            write_state(root)

            payload = check_commit_gate.build_payload(
                root,
                commit_message="docs: update readme",
                changed_paths=["README.md"],
                include_git_diff=False,
            )

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["readiness"], "pre_commit_ready")

    def test_blocks_pending_review(self) -> None:
        with temporary_workspace() as root:
            write_campaign(root)
            write_state(root, reviewer_result="pending")

            payload = check_commit_gate.build_payload(
                root,
                commit_message="docs: update readme",
                changed_paths=["README.md"],
                include_git_diff=False,
            )

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("blocking-review", finding_ids)

    def test_blocks_missing_verification(self) -> None:
        with temporary_workspace() as root:
            write_campaign(root)
            write_state(root, verification=[])

            payload = check_commit_gate.build_payload(
                root,
                commit_message="docs: update readme",
                changed_paths=["README.md"],
                include_git_diff=False,
            )

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("missing-verification", finding_ids)

    def test_blocks_non_conventional_commit_message(self) -> None:
        with temporary_workspace() as root:
            write_campaign(root)
            write_state(root)

            payload = check_commit_gate.build_payload(
                root,
                commit_message="update stuff",
                changed_paths=["README.md"],
                include_git_diff=False,
            )

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("non-conventional-commit", finding_ids)

    def test_blocks_out_of_contract_paths(self) -> None:
        with temporary_workspace() as root:
            write_campaign(root)
            write_state(root, write_paths=["README.md"])

            payload = check_commit_gate.build_payload(
                root,
                commit_message="docs: update readme",
                changed_paths=["scripts/new_tool.py"],
                include_git_diff=False,
            )

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("budget-out-of-contract-path", finding_ids)

    def test_blocks_structured_markdown_mirror_drift(self) -> None:
        with temporary_workspace() as root:
            write_campaign(root)
            write_stale_campaign_mirror(root)
            write_state(root)

            payload = check_commit_gate.build_payload(
                root,
                commit_message="docs: update readme",
                changed_paths=["README.md"],
                include_git_diff=False,
            )

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("budget-structured-markdown-mirror-drift", finding_ids)

    def test_post_push_requires_passing_github_status(self) -> None:
        with temporary_workspace() as root:
            write_campaign(root)
            write_state(root)

            payload = check_commit_gate.build_payload(
                root,
                commit_message="docs: update readme",
                stage="post-push",
                github_status="pending",
                changed_paths=[],
                include_git_diff=False,
            )

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("github-check-not-passing", finding_ids)


if __name__ == "__main__":
    unittest.main()
