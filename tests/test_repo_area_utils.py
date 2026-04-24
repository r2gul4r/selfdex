from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "repo_area_utils.py"
SPEC = importlib.util.spec_from_file_location("repo_area_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
repo_area_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = repo_area_utils
SPEC.loader.exec_module(repo_area_utils)


class RepoAreaUtilsTests(unittest.TestCase):
    def test_classify_known_repository_areas(self) -> None:
        cases = {
            Path("installer/install.ps1"): "installer",
            Path("docs/SELFDEX_FINAL_GOAL.md"): "documentation",
            Path("codex_agents/reviewer.md"): "agent_profiles",
            Path("profiles/default.md"): "agent_profiles",
            Path("codex_rules/base.md"): "rules_and_skills",
            Path("codex_skills/scan.md"): "rules_and_skills",
            Path("examples/sample.md"): "examples_and_snapshots",
            Path("scripts/plan_next_task.py"): "root_tooling",
            Path("README.md"): "root_tooling",
            Path("src/module.py"): "other",
        }

        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(repo_area_utils.classify_area(path), expected)

    def test_area_labels_cover_classifier_outputs(self) -> None:
        expected_keys = {
            "installer",
            "root_tooling",
            "documentation",
            "agent_profiles",
            "rules_and_skills",
            "examples_and_snapshots",
            "other",
        }

        self.assertEqual(set(repo_area_utils.AREA_LABELS), expected_keys)
        self.assertEqual(repo_area_utils.AREA_LABELS["root_tooling"], "루트 도구/자동화")


if __name__ == "__main__":
    unittest.main()
