from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from script_loader_utils import load_script


check_selfdex_setup = load_script("check_selfdex_setup.py")


def write_root(root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    for name in (
        "plan_external_project.py",
        "run_target_codex.py",
        "check_github_actions_status.py",
    ):
        (scripts / name).write_text("# fixture\n", encoding="utf-8")


def write_installed_plugin(home: Path, root: Path) -> None:
    plugin = home / "plugins" / "selfdex"
    skill = plugin / "skills" / "selfdex"
    manifest = plugin / ".codex-plugin"
    skill.mkdir(parents=True)
    manifest.mkdir(parents=True)
    (manifest / "plugin.json").write_text('{"name": "selfdex"}\n', encoding="utf-8")
    (skill / "SKILL.md").write_text("# Selfdex\n", encoding="utf-8")
    (plugin / "selfdex-root.json").write_text(
        json.dumps({"schema_version": 1, "selfdex_root": str(root.resolve())}),
        encoding="utf-8",
    )
    marketplace = home / ".agents" / "plugins" / "marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        json.dumps(
            {
                "plugins": [
                    {
                        "name": "selfdex",
                        "source": {"source": "local", "path": "./plugins/selfdex"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


class SelfdexSetupTests(unittest.TestCase):
    def test_ready_with_manual_actions_when_core_is_installed(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as home_dir:
            root = Path(root_dir)
            home = Path(home_dir)
            codex_home = home / ".codex"
            write_root(root)
            write_installed_plugin(home, root)

            payload = check_selfdex_setup.build_payload(root, home, codex_home=codex_home)

            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["readiness"], "ready_with_recommended_actions")
            check_ids = {check["check_id"]: check for check in payload["checks"]}
            self.assertEqual(check_ids["selfdex-plugin-directory"]["status"], "pass")
            self.assertEqual(check_ids["github-actions-fallback"]["status"], "pass")
            self.assertEqual(check_ids["gmail-not-required"]["status"], "pass")
            self.assertEqual(check_ids["github-plugin"]["status"], "manual_action")

    def test_detects_codex_github_plugin_cache_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as home_dir:
            root = Path(root_dir)
            home = Path(home_dir)
            codex_home = home / ".codex"
            (codex_home / "plugins" / "cache" / "openai-curated" / "github").mkdir(parents=True)
            write_root(root)
            write_installed_plugin(home, root)

            payload = check_selfdex_setup.build_payload(root, home, codex_home=codex_home)
            check_ids = {check["check_id"]: check for check in payload["checks"]}

            self.assertEqual(check_ids["github-plugin"]["status"], "pass")

    def test_blocks_when_selfdex_plugin_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as home_dir:
            root = Path(root_dir)
            home = Path(home_dir)
            write_root(root)

            payload = check_selfdex_setup.build_payload(root, home, codex_home=home / ".codex")

            self.assertEqual(payload["status"], "fail")
            self.assertEqual(payload["readiness"], "blocked")
            self.assertGreater(payload["high_failure_count"], 0)


if __name__ == "__main__":
    unittest.main()
