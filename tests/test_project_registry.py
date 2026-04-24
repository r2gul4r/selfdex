from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "list_project_registry.py"
SPEC = importlib.util.spec_from_file_location("list_project_registry", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
list_project_registry = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = list_project_registry
SPEC.loader.exec_module(list_project_registry)


REGISTRY_TEXT = """# Project Registry

## Registered Projects

| project_id | path | role | write_policy | verification |
| :-- | :-- | :-- | :-- | :-- |
| selfdex | . | harness | selfdex-local writes only | python -m compileall -q scripts tests; python -m unittest discover -s tests |
| missing | ./missing-project | fixture | read-only | python -m test |
"""


class ProjectRegistryTests(unittest.TestCase):
    def test_parse_registry_table(self) -> None:
        entries = list_project_registry.parse_registry(REGISTRY_TEXT)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].project_id, "selfdex")
        self.assertEqual(entries[0].verification[0], "python -m compileall -q scripts tests")
        self.assertEqual(entries[1].path, "./missing-project")

    def test_build_payload_reports_path_existence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")

            payload = list_project_registry.build_payload(root)

        projects = {project["project_id"]: project for project in payload["projects"]}
        self.assertEqual(payload["registered_project_count"], 2)
        self.assertTrue(projects["selfdex"]["path_exists"])
        self.assertFalse(projects["missing"]["path_exists"])

    def test_markdown_output_includes_write_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")
            payload = list_project_registry.build_payload(root)

        markdown = list_project_registry.render_markdown(payload)

        self.assertIn("# Project Registry", markdown)
        self.assertIn("- write_policy: selfdex-local writes only", markdown)
        self.assertIn("- path_exists: `False`", markdown)


if __name__ == "__main__":
    unittest.main()
