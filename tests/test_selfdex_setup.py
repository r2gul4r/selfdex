from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from script_loader_utils import load_script


check_selfdex_setup = load_script("check_selfdex_setup.py")
TEST_TEMP_ROOT = Path(__file__).resolve().parents[1] / "tmp" / "test-selfdex-setup"


@contextmanager
def temporary_pair() -> Iterator[tuple[Path, Path]]:
    TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    root = TEST_TEMP_ROOT / f"root-{uuid.uuid4().hex}"
    home = TEST_TEMP_ROOT / f"home-{uuid.uuid4().hex}"
    root.mkdir()
    home.mkdir()
    try:
        yield root, home
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)


def write_root(root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    for name in (
        "plan_external_project.py",
        "run_target_codex.py",
        "check_github_actions_status.py",
    ):
        (scripts / name).write_text("# fixture\n", encoding="utf-8")


def write_codex_policy(root: Path) -> None:
    agents = root / ".codex" / "agents"
    agents.mkdir(parents=True)
    (root / ".codex" / "config.toml").write_text(
        "\n".join(
            [
                "[features]",
                "multi_agent = true",
                "[agents.explorer]",
                "[agents.worker]",
                "[agents.reviewer]",
                "[agents.docs_researcher]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (agents / "explorer.toml").write_text(
        "\n".join(
            [
                'name = "explorer"',
                'model = "gpt-5.5"',
                'model_reasoning_effort = "low"',
                'sandbox_mode = "read-only"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (agents / "worker.toml").write_text(
        "\n".join(
            [
                'name = "worker"',
                'model = "gpt-5.5"',
                'model_reasoning_effort = "high"',
                'developer_instructions = """',
                "Implement only the frozen task slice assigned by the main agent.",
                "Stay inside the declared write boundary.",
                '"""',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (agents / "reviewer.toml").write_text(
        "\n".join(
            [
                'name = "reviewer"',
                'model = "gpt-5.5"',
                'model_reasoning_effort = "xhigh"',
                'sandbox_mode = "read-only"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (agents / "docs-researcher.toml").write_text(
        "\n".join(
            [
                'name = "docs_researcher"',
                'model = "gpt-5.5"',
                'model_reasoning_effort = "medium"',
                'sandbox_mode = "read-only"',
                "",
            ]
        ),
        encoding="utf-8",
    )


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
        with temporary_pair() as (root, home):
            codex_home = home / ".codex"
            write_root(root)
            write_codex_policy(root)
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
        with temporary_pair() as (root, home):
            codex_home = home / ".codex"
            (codex_home / "plugins" / "cache" / "openai-curated" / "github").mkdir(parents=True)
            write_root(root)
            write_codex_policy(root)
            write_installed_plugin(home, root)

            payload = check_selfdex_setup.build_payload(root, home, codex_home=codex_home)
            check_ids = {check["check_id"]: check for check in payload["checks"]}

            self.assertEqual(check_ids["github-plugin"]["status"], "pass")

    def test_blocks_when_selfdex_plugin_is_missing(self) -> None:
        with temporary_pair() as (root, home):
            write_root(root)
            write_codex_policy(root)

            payload = check_selfdex_setup.build_payload(root, home, codex_home=home / ".codex")

            self.assertEqual(payload["status"], "fail")
            self.assertEqual(payload["readiness"], "blocked")
            self.assertGreater(payload["high_failure_count"], 0)

    def test_blocks_when_codex_policy_surface_is_missing(self) -> None:
        with temporary_pair() as (root, home):
            write_root(root)
            write_installed_plugin(home, root)

            payload = check_selfdex_setup.build_payload(root, home, codex_home=home / ".codex")

            self.assertEqual(payload["status"], "fail")
            check_ids = {check["check_id"]: check for check in payload["checks"]}
            self.assertEqual(check_ids["codex-config"]["status"], "fail")
            self.assertEqual(check_ids["codex-config"]["severity"], "high")

    def test_blocks_when_worker_policy_is_stale(self) -> None:
        with temporary_pair() as (root, home):
            write_root(root)
            write_codex_policy(root)
            write_installed_plugin(home, root)
            (root / ".codex" / "agents" / "worker.toml").write_text('name = "worker"\n', encoding="utf-8")

            payload = check_selfdex_setup.build_payload(root, home, codex_home=home / ".codex")

            self.assertEqual(payload["status"], "fail")
            check_ids = {check["check_id"]: check for check in payload["checks"]}
            self.assertEqual(check_ids["codex-agent-worker"]["status"], "fail")
            self.assertIn("stale", check_ids["codex-agent-worker"]["summary"])

    def test_blocks_when_readonly_agent_model_or_effort_is_stale(self) -> None:
        with temporary_pair() as (root, home):
            write_root(root)
            write_codex_policy(root)
            write_installed_plugin(home, root)
            (root / ".codex" / "agents" / "explorer.toml").write_text(
                "\n".join(
                    [
                        'name = "explorer"',
                        'model = "gpt-5.4-mini"',
                        'model_reasoning_effort = "low"',
                        'sandbox_mode = "read-only"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            payload = check_selfdex_setup.build_payload(root, home, codex_home=home / ".codex")

            self.assertEqual(payload["status"], "fail")
            check_ids = {check["check_id"]: check for check in payload["checks"]}
            self.assertEqual(check_ids["codex-agent-explorer"]["status"], "fail")
            self.assertIn('model = "gpt-5.5"', check_ids["codex-agent-explorer"]["summary"])

    def test_blocks_when_readonly_agent_reasoning_effort_is_missing(self) -> None:
        with temporary_pair() as (root, home):
            write_root(root)
            write_codex_policy(root)
            write_installed_plugin(home, root)
            (root / ".codex" / "agents" / "reviewer.toml").write_text(
                "\n".join(
                    [
                        'name = "reviewer"',
                        'model = "gpt-5.5"',
                        'sandbox_mode = "read-only"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            payload = check_selfdex_setup.build_payload(root, home, codex_home=home / ".codex")

            self.assertEqual(payload["status"], "fail")
            check_ids = {check["check_id"]: check for check in payload["checks"]}
            self.assertEqual(check_ids["codex-agent-reviewer"]["status"], "fail")
            self.assertIn("model_reasoning_effort", check_ids["codex-agent-reviewer"]["summary"])


if __name__ == "__main__":
    unittest.main()
