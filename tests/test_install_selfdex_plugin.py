from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from script_loader_utils import load_script


install_selfdex_plugin = load_script("install_selfdex_plugin.py")


def write_checkout(root: Path) -> None:
    plugin_dir = root / "plugins" / "selfdex"
    manifest = plugin_dir / ".codex-plugin"
    skill_dir = plugin_dir / "skills" / "selfdex"
    manifest.mkdir(parents=True)
    skill_dir.mkdir(parents=True)
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

Use `SELFDEX_ROOT`, `selfdex-root.json`, or the Installed Checkout section.
Run `scripts/plan_external_project.py` first.
After explicit approval, run `scripts/run_target_codex.py`.
Install with `scripts/install_selfdex_plugin.py --yes`.
External projects are read-only by default.
Do not install this plugin without approval.
""",
        encoding="utf-8",
    )
    scripts = root / "scripts"
    scripts.mkdir()
    for name in (
        "plan_external_project.py",
        "run_target_codex.py",
        "install_selfdex_plugin.py",
    ):
        (scripts / name).write_text("# fixture\n", encoding="utf-8")
    (root / "CAMPAIGN_STATE.json").write_text("{}", encoding="utf-8")


class InstallSelfdexPluginTests(unittest.TestCase):
    def test_default_plugin_home_uses_codex_home_env(self) -> None:
        with tempfile.TemporaryDirectory() as codex_home:
            old_value = os.environ.get("CODEX_HOME")
            os.environ["CODEX_HOME"] = codex_home
            try:
                self.assertEqual(
                    install_selfdex_plugin.plugin_home_from().resolve(),
                    Path(codex_home).resolve(),
                )
            finally:
                if old_value is None:
                    os.environ.pop("CODEX_HOME", None)
                else:
                    os.environ["CODEX_HOME"] = old_value

    def test_dry_run_does_not_write_home_files(self) -> None:
        with tempfile.TemporaryDirectory() as checkout_dir, tempfile.TemporaryDirectory() as home_dir:
            checkout = Path(checkout_dir)
            home = Path(home_dir)
            write_checkout(checkout)

            payload = install_selfdex_plugin.build_payload(checkout, home)

            self.assertEqual(payload["status"], "pass")
            self.assertTrue(payload["dry_run"])
            self.assertFalse((home / "plugins" / "selfdex").exists())
            self.assertFalse((home / ".agents" / "plugins" / "marketplace.json").exists())

    def test_installs_plugin_and_records_checkout_root(self) -> None:
        with tempfile.TemporaryDirectory() as checkout_dir, tempfile.TemporaryDirectory() as home_dir:
            checkout = Path(checkout_dir)
            home = Path(home_dir)
            write_checkout(checkout)

            payload = install_selfdex_plugin.build_payload(checkout, home, yes=True)

            target_plugin = home / "plugins" / "selfdex"
            marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
            root_config = json.loads((target_plugin / "selfdex-root.json").read_text(encoding="utf-8"))
            skill_text = (target_plugin / "skills" / "selfdex" / "SKILL.md").read_text(encoding="utf-8")
            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "pass")
            self.assertFalse(payload["dry_run"])
            self.assertEqual(root_config["selfdex_root"], str(checkout.resolve()))
            self.assertIn("## Installed Checkout", skill_text)
            self.assertIn(str(checkout.resolve()), skill_text)
            self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/selfdex")
            self.assertEqual(marketplace["plugins"][0]["policy"]["authentication"], "ON_INSTALL")

    def test_refuses_existing_plugin_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as checkout_dir, tempfile.TemporaryDirectory() as home_dir:
            checkout = Path(checkout_dir)
            home = Path(home_dir)
            write_checkout(checkout)
            existing = home / "plugins" / "selfdex"
            existing.mkdir(parents=True)
            (existing / "marker.txt").write_text("keep\n", encoding="utf-8")

            payload = install_selfdex_plugin.build_payload(checkout, home, yes=True)

            self.assertEqual(payload["status"], "fail")
            finding_ids = {finding["finding_id"] for finding in payload["findings"]}
            self.assertIn("existing-plugin-directory", finding_ids)
            self.assertEqual((existing / "marker.txt").read_text(encoding="utf-8"), "keep\n")

    def test_force_preserves_other_marketplace_entries(self) -> None:
        with tempfile.TemporaryDirectory() as checkout_dir, tempfile.TemporaryDirectory() as home_dir:
            checkout = Path(checkout_dir)
            home = Path(home_dir)
            write_checkout(checkout)
            marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
            marketplace_path.parent.mkdir(parents=True)
            marketplace_path.write_text(
                json.dumps(
                    {
                        "name": "local",
                        "plugins": [
                            {
                                "name": "other",
                                "source": {"source": "local", "path": "./plugins/other"},
                                "policy": {
                                    "installation": "AVAILABLE",
                                    "authentication": "ON_INSTALL",
                                },
                                "category": "Productivity",
                            },
                            {
                                "name": "selfdex",
                                "source": {"source": "local", "path": "./old/selfdex"},
                                "policy": {
                                    "installation": "AVAILABLE",
                                    "authentication": "ON_USE",
                                },
                                "category": "Productivity",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = install_selfdex_plugin.build_payload(checkout, home, yes=True, force=True)

            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
            entries = {entry["name"]: entry for entry in marketplace["plugins"]}
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(entries["other"]["source"]["path"], "./plugins/other")
            self.assertEqual(entries["selfdex"]["source"]["path"], "./plugins/selfdex")
            self.assertEqual(entries["selfdex"]["policy"]["authentication"], "ON_INSTALL")


if __name__ == "__main__":
    unittest.main()
