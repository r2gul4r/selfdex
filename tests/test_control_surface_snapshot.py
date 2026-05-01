from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_control_surface_snapshot.py"
SPEC = importlib.util.spec_from_file_location("build_control_surface_snapshot", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
control_surface = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = control_surface
SPEC.loader.exec_module(control_surface)


def write_registry(root: Path) -> None:
    (root / "project_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "projects": [
                    {
                        "project_id": "selfdex",
                        "path": ".",
                        "role": "control harness",
                        "write_policy": "selfdex-local writes only",
                        "verification": ["python -m unittest discover -s tests"],
                    },
                    {
                        "project_id": "demo",
                        "path": "../demo",
                        "role": "read-only target",
                        "write_policy": "read-only",
                        "verification": ["read-only planning"],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def write_campaign(root: Path) -> None:
    (root / "CAMPAIGN_STATE.md").write_text(
        """# Campaign State

## Campaign

- name: `test`
- goal: `Make Selfdex a command center for selected projects.`

## Candidate Queue

- Add read-only dashboard snapshot.
""",
        encoding="utf-8",
    )
    (root / "CAMPAIGN_STATE.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "analysis_kind": "selfdex_campaign_contract",
                "campaign": {
                    "direction_review_default": "recommend_and_wait_for_user_approval",
                },
                "model_usage_policy": {
                    "gpt_direction_review_auto_call": False,
                    "gpt_direction_review_approval": "user-approved-or-user-called-only",
                },
                "first_app_surface": {
                    "write_capable_target_execution_exposed": False,
                },
                "latest_run": {
                    "status": "blocked",
                    "artifact_path": "runs/selfdex/20260501-000002-second.md",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "STATE.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "analysis_kind": "selfdex_state_contract",
                "current_task": {
                    "task": "Add read-only dashboard snapshot.",
                    "phase": "planning",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def write_runs(root: Path) -> None:
    runs = root / "runs" / "selfdex"
    runs.mkdir(parents=True)
    (runs / "20260501-000001-first.md").write_text(
        """# First Run

- status: `completed`
- project_key: `selfdex`
- summary: `first`
""",
        encoding="utf-8",
    )
    (runs / "20260501-000002-second.md").write_text(
        """# Second Run

- status: `blocked`
- project_key: `selfdex`
- summary: `second`
""",
        encoding="utf-8",
    )
    external = root / "runs" / "external-validation"
    external.mkdir(parents=True)
    (external / "summary.md").write_text("# External Summary\n\n- status: `pass`\n", encoding="utf-8")
    (external / "fs-snapshot.md").write_text("# Snapshot\n\n- status: `scanned`\n", encoding="utf-8")


class ControlSurfaceSnapshotTests(unittest.TestCase):
    def test_builds_read_only_control_surface_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_registry(root)
            write_campaign(root)
            write_runs(root)

            payload = control_surface.build_payload(root, run_limit=1)

        self.assertEqual(payload["surface_kind"], "read_only")
        self.assertFalse(payload["mutating_tools_exposed"])
        self.assertEqual(payload["project_count"], 2)
        self.assertEqual(payload["projects"][1]["write_policy"], "read-only")
        self.assertEqual(payload["next_task"]["title"], "Add read-only dashboard snapshot.")
        self.assertEqual(len(payload["recent_runs"]), 1)
        self.assertEqual(payload["recent_runs"][0]["status"], "blocked")
        self.assertEqual(payload["recent_runs"][0]["path"], "runs/selfdex/20260501-000002-second.md")
        self.assertEqual(payload["approval_status"]["gpt_direction_review_approval"], "user-approved-or-user-called-only")
        self.assertFalse(payload["approval_status"]["gpt_direction_review_auto_call"])
        self.assertFalse(payload["approval_status"]["write_capable_apps_mcp_tools_exposed"])
        self.assertEqual(payload["approval_status"]["current_phase"], "planning")

    def test_latest_runs_excludes_non_timestamped_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runs(root)

            runs = control_surface.latest_runs(root, 5)

        paths = [run["path"] for run in runs]
        self.assertEqual(
            paths,
            [
                "runs/selfdex/20260501-000002-second.md",
                "runs/selfdex/20260501-000001-first.md",
            ],
        )

    def test_markdown_declares_no_mutating_surface(self) -> None:
        payload = {
            "surface_kind": "read_only",
            "mutating_tools_exposed": False,
            "project_count": 0,
            "recent_runs": [],
            "execution_policy": "No writes.",
            "projects": [],
            "next_task": None,
            "approval_status": {
                "target_project_writes_allowed": False,
                "target_project_write_approval_required": True,
                "target_execution_approval_required": True,
                "write_capable_apps_mcp_tools_exposed": False,
                "gpt_direction_review_auto_call": False,
                "gpt_direction_review_approval": "user-approved-or-user-called-only",
                "current_task": "demo",
                "current_phase": "verified",
                "latest_run_status": "completed",
            },
            "errors": [],
        }

        markdown = control_surface.render_markdown(payload)

        self.assertIn("# Selfdex Control Surface Snapshot", markdown)
        self.assertIn("mutating_tools_exposed: `False`", markdown)
        self.assertIn("## Approval Status", markdown)
        self.assertIn("gpt_direction_review_auto_call: `False`", markdown)
        self.assertIn("No writes.", markdown)


if __name__ == "__main__":
    unittest.main()
