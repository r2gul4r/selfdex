from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_external_project.py"
SPEC = importlib.util.spec_from_file_location("plan_external_project", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
plan_external_project = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = plan_external_project
SPEC.loader.exec_module(plan_external_project)


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_registry(root: Path, external: Path, *, write_policy: str = "read-only") -> None:
    (root / "PROJECT_REGISTRY.md").write_text(
        "# Project Registry\n\n"
        "## Registered Projects\n\n"
        "| project_id | path | role | write_policy | verification |\n"
        "| :-- | :-- | :-- | :-- | :-- |\n"
        "| selfdex | . | harness | selfdex-local writes only | python -m unittest |\n"
        f"| external_one | {external} | fixture | {write_policy} | python -m unittest discover -s tests |\n",
        encoding="utf-8",
    )


def write_goal_cycle_fixture(root: Path) -> None:
    write_file(
        root,
        "CAMPAIGN_STATE.md",
        "# Campaign State\n\n## Campaign\n\n- goal: `Build a harness that can detect, plan, verify, and record work.`\n",
    )
    write_file(
        root,
        "docs/GOAL_COMPARISON_AREAS.md",
        "- 저장소가 자기 부족한 코드 품질과 기능 공백을 스스로 찾고, 개선안을 제안·구현·검증한다\n",
    )
    write_file(root, "Makefile", "test: test-installers\n\tpython -m unittest discover -s tests\n")


class PlanExternalProjectTests(unittest.TestCase):
    def test_registered_project_plan_contains_contract_and_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_registry(root, external)
            write_goal_cycle_fixture(external)

            payload = plan_external_project.build_plan(root, project_id="external_one", limit=3)

        contract = payload["task_contract"]

        self.assertEqual(payload["analysis_kind"], "selfdex_external_project_plan")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["validation_mode"], "read_only")
        self.assertFalse(payload["external_project_writes_performed"])
        self.assertEqual(contract["selected_candidate"]["title"], "자가개선 루프 통합 검증 부재")
        self.assertFalse(contract["write_boundaries"]["target_project_writes_allowed_now"])
        self.assertTrue(contract["human_approval_required"])
        self.assertIn("real_problem", contract["candidate_quality"]["scores"])
        self.assertIn("python -m unittest discover -s tests", contract["registry_verification_notes"])
        self.assertNotIn("human rubric scoring", contract["verification_commands"])
        self.assertIn("Human approval is required", contract["codex_execution_prompt"])

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
            write_registry(root, external)

            payload = plan_external_project.build_plan(root, project_id="missing", limit=3)

        self.assertEqual(payload["status"], "fail")
        self.assertIn("not registered", payload["blocker"])
        self.assertIsNone(payload["task_contract"])

    def test_record_run_writes_only_under_selfdex_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-one"
            external.mkdir()
            write_registry(root, external)
            write_goal_cycle_fixture(external)
            payload = plan_external_project.build_plan(root, project_id="external_one", limit=3)

            path = plan_external_project.write_plan_artifact(root, payload, "20260425-201500")

            self.assertTrue(path.exists())
            self.assertEqual(path.parent, root / "runs")
            self.assertIn("external-one", payload["project"]["resolved_path"])
            self.assertIn("Codex Execution Prompt", path.read_text(encoding="utf-8"))
            self.assertFalse((external / "runs").exists())


if __name__ == "__main__":
    unittest.main()
