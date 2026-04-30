from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_campaign_budget.py"
SPEC = importlib.util.spec_from_file_location("check_campaign_budget", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
check_campaign_budget = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_campaign_budget
SPEC.loader.exec_module(check_campaign_budget)


def campaign_text(default_budget: int = 2, max_budget: int = 4) -> str:
    return f"""# Campaign State

## Campaign

- name: `test`
- default_agent_budget: `{default_budget}`
- max_agent_budget: `{max_budget}`

## Hard Approval Zones

- destructive Git or filesystem operations
- secrets, credentials, private keys, or token access
- paid API calls
- public deployment
- database migration or production write
- cross-workspace edits
"""


def state_text(agent_budget: int = 1) -> str:
    return f"""# STATE

## Current Task

- task: `Add a campaign budget checker.`
- phase: `implementation`

## Orchestration Profile

- agent_budget: `{agent_budget}`

## Writer Slot

- writer_slot: `main`
- write_sets:
  - `main`:
    - `scripts/check_campaign_budget.py`
    - `tests/test_campaign_budget.py`
    - `README.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
"""


def write_fixture(root: Path, *, campaign: str | None = None, state: str | None = None) -> None:
    (root / "CAMPAIGN_STATE.md").write_text(
        campaign if campaign is not None else campaign_text(),
        encoding="utf-8",
    )
    (root / "STATE.md").write_text(
        state if state is not None else state_text(),
        encoding="utf-8",
    )


class CampaignBudgetTests(unittest.TestCase):
    def test_accepts_changed_paths_inside_state_write_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)

            payload = check_campaign_budget.build_payload(
                root,
                [
                    "scripts/check_campaign_budget.py",
                    "tests/test_campaign_budget.py",
                    "README.md",
                    "CAMPAIGN_STATE.md",
                    "STATE.md",
                ],
            )

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["violation_count"], 0)
        self.assertEqual(payload["state_contract"]["agent_budget"], 1)

    def test_rejects_state_agent_budget_above_campaign_max(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root, state=state_text(agent_budget=5))

            payload = check_campaign_budget.build_payload(root, [])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("state-agent-budget-exceeds-campaign-max", violation_ids)

    def test_rejects_out_of_contract_changed_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)

            payload = check_campaign_budget.build_payload(root, ["docs/outside.md"])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("out-of-contract-path", violation_ids)

    def test_rejects_hard_approval_path_hint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            custom_state = state_text() + "    - `secrets/token.txt`\n"
            write_fixture(root, state=custom_state)

            payload = check_campaign_budget.build_payload(root, ["secrets/token.txt"])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("hard-approval-path", violation_ids)

    def test_allows_project_scoped_runs_even_with_hard_approval_words(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            custom_state = state_text() + "    - `runs/database-migration-demo/20260430-task.md`\n"
            write_fixture(root, state=custom_state)

            payload = check_campaign_budget.build_payload(
                root,
                ["runs/database-migration-demo/20260430-task.md"],
            )

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["violation_count"], 0)

    def test_markdown_reports_pass_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)
            payload = check_campaign_budget.build_payload(root, ["README.md"])

        markdown = check_campaign_budget.render_markdown(payload)

        self.assertIn("# Campaign Budget Check", markdown)
        self.assertIn("- status: `pass`", markdown)
        self.assertIn("README.md", markdown)

    def test_include_git_diff_reports_untracked_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            write_fixture(root)
            (root / "scripts").mkdir()
            (root / "scripts" / "check_campaign_budget.py").write_text("# fixture\n", encoding="utf-8")

            payload = check_campaign_budget.build_payload(root, include_git_diff=True)

        reported = {item["normalized"] for item in payload["changed_paths"]}
        self.assertIn("scripts/check_campaign_budget.py", reported)


if __name__ == "__main__":
    unittest.main()
