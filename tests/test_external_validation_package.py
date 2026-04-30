from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_external_validation_package.py"
SPEC = importlib.util.spec_from_file_location("build_external_validation_package", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
build_external_validation_package = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_external_validation_package
SPEC.loader.exec_module(build_external_validation_package)


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_registry(root: Path, external_one: Path, external_two: Path) -> None:
    payload = {
        "schema_version": 1,
        "projects": [
            {
                "project_id": "selfdex",
                "path": ".",
                "role": "harness",
                "write_policy": "selfdex-local writes only",
                "verification": ["python -m unittest"],
            },
            {
                "project_id": "external_one",
                "path": str(external_one),
                "role": "fixture",
                "write_policy": "read-only",
                "verification": ["read-only candidate generation", "human rubric scoring"],
            },
            {
                "project_id": "external_two",
                "path": str(external_two),
                "role": "fixture",
                "write_policy": "read-only",
                "verification": ["read-only candidate generation", "human rubric scoring"],
            },
        ],
    }
    (root / "project_registry.json").write_text(json.dumps(payload), encoding="utf-8")
    (root / "PROJECT_REGISTRY.md").write_text("# Project Registry\n", encoding="utf-8")


def write_goal_cycle_fixture(root: Path) -> None:
    write_file(root, "README.md", "# Agent Tool\n\nA Codex automation workflow for developers.\n")
    write_file(root, "CAMPAIGN_STATE.md", "# Campaign State\n\n## Campaign\n\n- goal: `Build an agent workflow.`\n")
    write_file(root, "scripts/run.py", "print('ok')\n")
    write_file(root, "tests/test_run.py", "def test_run():\n    assert True\n")


class ExternalValidationPackageTests(unittest.TestCase):
    def test_build_package_writes_summary_and_project_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external_one = root / "external-one"
            external_two = root / "external-two"
            external_one.mkdir()
            external_two.mkdir()
            write_goal_cycle_fixture(external_one)
            write_goal_cycle_fixture(external_two)
            write_registry(root, external_one, external_two)

            payload = build_external_validation_package.build_package(root, limit=2, timestamp="20260430-130000")
            artifact_exists = [
                (root / artifact).exists()
                for project in payload["projects"]
                for artifact in project["artifacts"].values()
            ]

        self.assertEqual(payload["analysis_kind"], "selfdex_external_validation_package")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["external_value_proven"])
        self.assertEqual(payload["project_count"], 2)
        self.assertIn("runs/external-validation/summary.md", payload["summary_path"])
        self.assertTrue(all(artifact_exists))
        for project in payload["projects"]:
            self.assertEqual(project["status"], "pass")


if __name__ == "__main__":
    unittest.main()
