from __future__ import annotations

import importlib.util
import json
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

## Model Usage Policy

- gpt_direction_review_role: `high-level product, milestone, roadmap, and priority direction only`
- gpt_direction_review_approval: `user-approved-or-user-called-only`
- gpt_direction_review_auto_call: `False`
- gpt_direction_review_triggers: `project goals conflict or are unclear; candidate tasks are all strategically ambiguous`
- gpt_direction_review_non_triggers: `routine coding; tests; refactors; bug fixes; documentation drift; diff review`
- selfdex_role: `coordinate the loop, freeze contracts, manage approval, record evidence, and prevent uncontrolled autonomy`
- codex_role: `implement safely, verify, debug failures, review diffs, and stop when work becomes a product-direction question`

## First App Surface

- surface_kind: `read_only`
- write_capable_target_execution_exposed: `False`
- allowed_fields: `registered projects; next recommended task; latest run records; approval status`

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
    - `CAMPAIGN_STATE.json`
    - `STATE.md`
    - `STATE.json`
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


def campaign_json(default_budget: int = 2, max_budget: int = 4) -> dict[str, object]:
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_campaign_contract",
        "campaign": {
            "name": "test",
            "default_agent_budget": default_budget,
            "max_agent_budget": max_budget,
        },
        "hard_approval_zones": [
            "destructive Git or filesystem operations",
            "secrets, credentials, private keys, or token access",
            "paid API calls",
            "public deployment",
            "database migration or production write",
            "cross-workspace edits",
        ],
        "model_usage_policy": {
            "gpt_direction_review_role": "high-level product, milestone, roadmap, and priority direction only",
            "gpt_direction_review_approval": "user-approved-or-user-called-only",
            "gpt_direction_review_auto_call": False,
            "gpt_direction_review_triggers": [
                "project goals conflict or are unclear",
                "candidate tasks are all strategically ambiguous",
            ],
            "gpt_direction_review_non_triggers": [
                "routine coding",
                "tests",
                "refactors",
                "bug fixes",
                "documentation drift",
                "diff review",
            ],
            "selfdex_role": "coordinate the loop, freeze contracts, manage approval, record evidence, and prevent uncontrolled autonomy",
            "codex_role": "implement safely, verify, debug failures, review diffs, and stop when work becomes a product-direction question",
        },
        "first_app_surface": {
            "surface_kind": "read_only",
            "write_capable_target_execution_exposed": False,
            "allowed_fields": [
                "registered projects",
                "next recommended task",
                "latest run records",
                "approval status",
            ],
        },
    }


def state_json(agent_budget: int = 1) -> dict[str, object]:
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_state_contract",
        "current_task": {
            "task": "Add a campaign budget checker.",
            "phase": "implementation",
        },
        "orchestration_profile": {
            "agent_budget": agent_budget,
        },
        "writer_slot": {
            "write_sets": {
                "main": [
                    "scripts/check_campaign_budget.py",
                    "tests/test_campaign_budget.py",
                    "README.md",
                    "CAMPAIGN_STATE.md",
                    "CAMPAIGN_STATE.json",
                    "STATE.md",
                    "STATE.json",
                ]
            }
        },
    }


def write_json_fixture(
    root: Path,
    *,
    campaign: dict[str, object] | None = None,
    state: dict[str, object] | None = None,
) -> None:
    if not (root / "CAMPAIGN_STATE.md").exists() or not (root / "STATE.md").exists():
        write_fixture(root)
    (root / "CAMPAIGN_STATE.json").write_text(
        json.dumps(campaign if campaign is not None else campaign_json(), indent=2),
        encoding="utf-8",
    )
    (root / "STATE.json").write_text(
        json.dumps(state if state is not None else state_json(), indent=2),
        encoding="utf-8",
    )


class CampaignBudgetTests(unittest.TestCase):
    def test_accepts_changed_paths_inside_state_write_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)
            write_json_fixture(root)

            payload = check_campaign_budget.build_payload(
                root,
                [
                    "scripts/check_campaign_budget.py",
                    "tests/test_campaign_budget.py",
                    "README.md",
                    "CAMPAIGN_STATE.md",
                    "CAMPAIGN_STATE.json",
                    "STATE.md",
                    "STATE.json",
                ],
            )

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["violation_count"], 0)
        self.assertEqual(payload["state_contract"]["agent_budget"], 1)

    def test_rejects_missing_structured_json_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)

            payload = check_campaign_budget.build_payload(root, ["README.md"])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("missing-structured-campaign-contract", violation_ids)
        self.assertIn("missing-structured-state-contract", violation_ids)

    def test_prefers_structured_json_contracts_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(
                root,
                campaign=campaign_text(max_budget=1).replace(
                    "user-approved-or-user-called-only",
                    "automatic",
                ),
                state=state_text(agent_budget=9),
            )
            write_json_fixture(root)

            payload = check_campaign_budget.build_payload(root, ["README.md"])

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["contract_sources"]["campaign"], "CAMPAIGN_STATE.json")
        self.assertEqual(payload["contract_sources"]["state"], "STATE.json")
        self.assertEqual(payload["state_contract"]["agent_budget"], 1)

    def test_reports_markdown_mirror_warning_when_json_differs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(
                root,
                campaign=campaign_text(max_budget=1).replace(
                    "user-approved-or-user-called-only",
                    "automatic",
                ),
                state=state_text(agent_budget=9),
            )
            write_json_fixture(root)

            payload = check_campaign_budget.build_payload(root, ["README.md"])

        self.assertEqual(payload["status"], "pass")
        warning_fields = {
            (item["source"], item["field"]) for item in payload["mirror_warnings"]
        }
        self.assertIn(("CAMPAIGN_STATE.md", "max_agent_budget"), warning_fields)
        self.assertIn(("CAMPAIGN_STATE.md", "model_usage_policy"), warning_fields)
        self.assertIn(("STATE.md", "agent_budget"), warning_fields)

    def test_reports_model_usage_mirror_warning_when_json_differs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)
            campaign = campaign_json()
            model_policy = dict(campaign["model_usage_policy"])  # type: ignore[arg-type]
            model_policy["gpt_direction_review_auto_call"] = True
            campaign["model_usage_policy"] = model_policy
            write_json_fixture(root, campaign=campaign)

            payload = check_campaign_budget.build_payload(root, ["README.md"])

        warning_fields = {
            (item["source"], item["field"]) for item in payload["mirror_warnings"]
        }
        self.assertIn(("CAMPAIGN_STATE.md", "model_usage_policy"), warning_fields)

    def test_reports_first_app_surface_mirror_warning_when_json_differs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)
            campaign = campaign_json()
            first_surface = dict(campaign["first_app_surface"])  # type: ignore[arg-type]
            first_surface["write_capable_target_execution_exposed"] = True
            campaign["first_app_surface"] = first_surface
            write_json_fixture(root, campaign=campaign)

            payload = check_campaign_budget.build_payload(root, ["README.md"])

        warning_fields = {
            (item["source"], item["field"]) for item in payload["mirror_warnings"]
        }
        self.assertIn(("CAMPAIGN_STATE.md", "first_app_surface"), warning_fields)

    def test_structured_json_rejects_budget_above_campaign_max(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_json_fixture(root, state=state_json(agent_budget=5))

            payload = check_campaign_budget.build_payload(root, [])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("state-agent-budget-exceeds-campaign-max", violation_ids)

    def test_rejects_state_agent_budget_above_campaign_max(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_json_fixture(root, state=state_json(agent_budget=5))

            payload = check_campaign_budget.build_payload(root, [])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("state-agent-budget-exceeds-campaign-max", violation_ids)

    def test_rejects_out_of_contract_changed_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_json_fixture(root)

            payload = check_campaign_budget.build_payload(root, ["docs/outside.md"])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("out-of-contract-path", violation_ids)

    def test_rejects_hard_approval_path_hint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            custom_state = state_json()
            custom_state["writer_slot"]["write_sets"]["main"].append("secrets/token.txt")  # type: ignore[index]
            write_json_fixture(root, state=custom_state)

            payload = check_campaign_budget.build_payload(root, ["secrets/token.txt"])

        self.assertEqual(payload["status"], "fail")
        violation_ids = {item["violation_id"] for item in payload["violations"]}
        self.assertIn("hard-approval-path", violation_ids)

    def test_allows_project_scoped_runs_even_with_hard_approval_words(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            custom_state = state_json()
            custom_state["writer_slot"]["write_sets"]["main"].append(  # type: ignore[index]
                "runs/database-migration-demo/20260430-task.md"
            )
            write_json_fixture(root, state=custom_state)

            payload = check_campaign_budget.build_payload(
                root,
                ["runs/database-migration-demo/20260430-task.md"],
            )

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["violation_count"], 0)

    def test_markdown_reports_pass_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_json_fixture(root)
            payload = check_campaign_budget.build_payload(root, ["README.md"])

        markdown = check_campaign_budget.render_markdown(payload)

        self.assertIn("# Campaign Budget Check", markdown)
        self.assertIn("- status: `pass`", markdown)
        self.assertIn("README.md", markdown)

    def test_include_git_diff_reports_untracked_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            write_json_fixture(root)
            (root / "scripts").mkdir()
            (root / "scripts" / "check_campaign_budget.py").write_text("# fixture\n", encoding="utf-8")

            payload = check_campaign_budget.build_payload(root, include_git_diff=True)

        reported = {item["normalized"] for item in payload["changed_paths"]}
        self.assertIn("scripts/check_campaign_budget.py", reported)

    def test_include_git_diff_preserves_unicode_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            custom_state = state_json()
            custom_state["writer_slot"]["write_sets"]["main"].append("runs/")  # type: ignore[index]
            write_json_fixture(root, state=custom_state)
            run_dir = root / "runs" / "daboyeo"
            run_dir.mkdir(parents=True)
            (run_dir / "중복-정리.md").write_text("# fixture\n", encoding="utf-8")

            payload = check_campaign_budget.build_payload(root, include_git_diff=True)

        reported = {item["normalized"] for item in payload["changed_paths"]}
        self.assertIn("runs/daboyeo/중복-정리.md", reported)
        self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
