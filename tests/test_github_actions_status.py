from __future__ import annotations

import unittest

from scripts import check_github_actions_status


class GitHubActionsStatusTests(unittest.TestCase):
    def test_parse_https_remote(self) -> None:
        repo = check_github_actions_status.parse_github_repo("https://github.com/r2gul4r/selfdex.git")

        self.assertEqual(repo, "r2gul4r/selfdex")

    def test_parse_ssh_remote(self) -> None:
        repo = check_github_actions_status.parse_github_repo("git@github.com:r2gul4r/selfdex.git")

        self.assertEqual(repo, "r2gul4r/selfdex")

    def test_classify_success_when_all_runs_succeeded(self) -> None:
        status, findings = check_github_actions_status.classify_runs(
            [
                {
                    "name": "check",
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": "https://github.com/r2gul4r/selfdex/actions/runs/1",
                }
            ]
        )

        self.assertEqual(status, "pass")
        self.assertEqual(findings, [])

    def test_classify_pending_when_no_run_exists_yet(self) -> None:
        status, findings = check_github_actions_status.classify_runs([])

        self.assertEqual(status, "pending")
        self.assertEqual(findings[0]["finding_id"], "no-workflow-run")

    def test_classify_failure_with_run_url(self) -> None:
        status, findings = check_github_actions_status.classify_runs(
            [
                {
                    "name": "check",
                    "status": "completed",
                    "conclusion": "failure",
                    "html_url": "https://github.com/r2gul4r/selfdex/actions/runs/25208966691",
                }
            ]
        )

        self.assertEqual(status, "fail")
        self.assertEqual(findings[0]["finding_id"], "workflow-failed")
        self.assertIn("25208966691", findings[0]["summary"])

    def test_workflow_runs_url_uses_head_sha_filter(self) -> None:
        url = check_github_actions_status.workflow_runs_url(
            repo="r2gul4r/selfdex",
            sha="abc123",
            branch="main",
            event="push",
            per_page=10,
        )

        self.assertIn("head_sha=abc123", url)
        self.assertIn("branch=main", url)
        self.assertIn("event=push", url)


if __name__ == "__main__":
    unittest.main()
