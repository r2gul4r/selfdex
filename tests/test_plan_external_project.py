from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from external_validation_test_utils import write_external_registry, write_goal_cycle_fixture
except ModuleNotFoundError:
    from tests.external_validation_test_utils import write_external_registry, write_goal_cycle_fixture


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_external_project.py"
SPEC = importlib.util.spec_from_file_location("plan_external_project", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
plan_external_project = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = plan_external_project
SPEC.loader.exec_module(plan_external_project)


REGISTRY_VERIFICATION = "python -m unittest discover -s tests"


class PlanExternalProjectTests(unittest.TestCase):
    def test_registered_project_plan_contains_contract_and_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_external_registry(root, external, verification=REGISTRY_VERIFICATION)
            write_goal_cycle_fixture(external)

            payload = plan_external_project.build_plan(root, project_id="external_one", limit=3)

        contract = payload["task_contract"]

        self.assertEqual(payload["analysis_kind"], "selfdex_external_project_plan")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["validation_mode"], "read_only")
        self.assertFalse(payload["external_project_writes_performed"])
        self.assertEqual(contract["selected_candidate"]["source"], "project_direction")
        self.assertEqual(contract["selected_candidate"]["title"], "Close one autonomous feedback loop with evidence")
        self.assertIn("project_direction", contract)
        self.assertIn("purpose", contract["project_direction"])
        self.assertFalse(contract["write_boundaries"]["target_project_writes_allowed_now"])
        self.assertEqual(
            contract["write_boundaries"]["evidence_only_files"],
            contract["files_likely_to_inspect"],
        )
        self.assertEqual(contract["files_likely_safe_to_modify_after_approval"], [])
        self.assertTrue(contract["human_approval_required"])
        self.assertIn("real_problem", contract["candidate_quality"]["scores"])
        self.assertIn(REGISTRY_VERIFICATION, contract["registry_verification_notes"])
        self.assertNotIn("human rubric scoring", contract["verification_commands"])
        self.assertIn("Human approval is required", contract["codex_execution_prompt"])
        self.assertIn("Expected outcome:", contract["codex_execution_prompt"])
        self.assertIn("Project direction context:", contract["codex_execution_prompt"])
        self.assertIn("Move the project in a better direction", contract["codex_execution_prompt"])
        self.assertIn("Success criteria:", contract["codex_execution_prompt"])
        self.assertIn("Context budget:", contract["codex_execution_prompt"])
        self.assertIn("Tool and skill routing:", contract["codex_execution_prompt"])
        self.assertIn("do not install skills, plugins, MCP servers", contract["codex_execution_prompt"])
        self.assertIn("Stop conditions:", contract["codex_execution_prompt"])

    def test_project_root_plan_does_not_need_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            external = Path(temp_dir) / "external-one"
            root.mkdir()
            external.mkdir()
            write_goal_cycle_fixture(external)

            payload = plan_external_project.build_plan(
                root,
                project_root=str(external),
                project_name="ad_hoc",
                limit=3,
            )

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["project"]["project_id"], "ad_hoc")
        self.assertEqual(payload["project"]["write_policy"], "read-only")
        self.assertFalse(payload["external_project_writes_performed"])

    def test_missing_registered_project_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_external_registry(root, external, verification=REGISTRY_VERIFICATION)

            payload = plan_external_project.build_plan(root, project_id="missing", limit=3)

        self.assertEqual(payload["status"], "fail")
        self.assertIn("not registered", payload["blocker"])
        self.assertIsNone(payload["task_contract"])

    def test_record_run_writes_under_project_scoped_selfdex_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_external_registry(root, external, verification=REGISTRY_VERIFICATION)
            write_goal_cycle_fixture(external)
            payload = plan_external_project.build_plan(root, project_id="external_one", limit=3)

            path = plan_external_project.write_plan_artifact(root, payload, "20260425-201500")

            self.assertTrue(path.exists())
            self.assertEqual(path.parent, root / "runs" / "external_one")
            self.assertIn("external-one", payload["project"]["resolved_path"])
            self.assertIn("Codex Execution Prompt", path.read_text(encoding="utf-8"))
            self.assertFalse((external / "runs").exists())

    def test_project_root_record_run_uses_project_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "selfdex"
            external = Path(temp_dir) / "external-one"
            root.mkdir()
            external.mkdir()
            write_goal_cycle_fixture(external)
            payload = plan_external_project.build_plan(
                root,
                project_root=str(external),
                project_name="Target Project!",
                limit=3,
            )

            path = plan_external_project.write_plan_artifact(root, payload, "20260425-201501")

        self.assertEqual(path.parent.name, "target-project")


if __name__ == "__main__":
    unittest.main()
