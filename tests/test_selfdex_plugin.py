from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from script_loader_utils import load_script


check_selfdex_plugin = load_script("check_selfdex_plugin.py")


def write_plugin_fixture(root: Path) -> None:
    plugin_dir = root / "plugins" / "selfdex"
    manifest = plugin_dir / ".codex-plugin"
    skill_dir = plugin_dir / "skills" / "selfdex"
    marketplace = root / ".agents" / "plugins"
    manifest.mkdir(parents=True)
    skill_dir.mkdir(parents=True)
    marketplace.mkdir(parents=True)
    (manifest / "plugin.json").write_text(
        json.dumps(
            {
                "name": "selfdex",
                "version": "0.1.0",
                "description": "Invoke Selfdex from a target project session.",
                "skills": "./skills/",
                "interface": {
                    "defaultPrompt": [
                        "@selfdex read this project and choose the next safe task"
                    ]
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (skill_dir / "SKILL.md").write_text(
        """---
name: selfdex
description: Use when the user invokes @selfdex.
---

# Selfdex

Use this skill from a target project session. Treat the current working directory as the target.

Find `SELFDEX_ROOT`, then run `scripts/plan_external_project.py`.
After explicit approval, run `scripts/run_target_codex.py`.
Install with `scripts/install_selfdex_plugin.py --yes`.

External projects are read-only by default.
Do not install this plugin without approval.
""",
        encoding="utf-8",
    )
    (marketplace / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "selfdex-local",
                "plugins": [
                    {
                        "name": "selfdex",
                        "source": {"source": "local", "path": "./plugins/selfdex"},
                        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                        "category": "Productivity",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    scripts = root / "scripts"
    scripts.mkdir()
    (scripts / "plan_external_project.py").write_text("# fixture\n", encoding="utf-8")
    (scripts / "run_target_codex.py").write_text("# fixture\n", encoding="utf-8")
    (scripts / "install_selfdex_plugin.py").write_text("# fixture\n", encoding="utf-8")


class SelfdexPluginTests(unittest.TestCase):
    def test_validates_plugin_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_plugin_fixture(root)

            payload = check_selfdex_plugin.build_payload(root)

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["finding_count"], 0)
        self.assertEqual(payload["plugin_name"], "selfdex")

    def test_rejects_missing_explicit_approval_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_plugin_fixture(root)
            skill_path = root / "plugins" / "selfdex" / "skills" / "selfdex" / "SKILL.md"
            skill_path.write_text(
                skill_path.read_text(encoding="utf-8").replace("explicit approval", "approval"),
                encoding="utf-8",
            )

            payload = check_selfdex_plugin.build_payload(root)

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("skill-missing-safety-phrase", finding_ids)

    def test_rejects_marketplace_path_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_plugin_fixture(root)
            marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
            payload = json.loads(marketplace_path.read_text(encoding="utf-8"))
            payload["plugins"][0]["source"]["path"] = "./plugins/other"
            marketplace_path.write_text(json.dumps(payload), encoding="utf-8")

            result = check_selfdex_plugin.build_payload(root)

        self.assertEqual(result["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in result["findings"]}
        self.assertIn("marketplace-path-mismatch", finding_ids)


if __name__ == "__main__":
    unittest.main()
