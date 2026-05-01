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
    commit_gate_dir = plugin_dir / "skills" / "selfdex-commit-gate"
    marketplace = root / ".agents" / "plugins"
    codex_agents = root / ".codex" / "agents"
    manifest.mkdir(parents=True)
    skill_dir.mkdir(parents=True)
    commit_gate_dir.mkdir(parents=True)
    marketplace.mkdir(parents=True)
    codex_agents.mkdir(parents=True)
    (manifest / "plugin.json").write_text(
        json.dumps(
            {
                "name": "selfdex",
                "version": "0.1.0",
                "description": "Invoke Selfdex from a target project session.",
                "skills": "./skills/",
                "interface": {
                    "defaultPrompt": [
                        "@selfdex read this project and choose the next safe task",
                        "@selfdex close the verified task with the commit gate",
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

Calling @selfdex is explicit permission to use Codex native Subagents/MultiAgentV2.
Keep the main agent focused on approvals and records.
Use explorer, docs_researcher, worker, and reviewer roles when useful.
Find `SELFDEX_ROOT`, then run `scripts/plan_external_project.py`.
After explicit approval, run `scripts/run_target_codex.py`.
Install with `scripts/install_selfdex_plugin.py --yes`.
After review, run `scripts/check_commit_gate.py`.

External projects are read-only by default.
Do not install this plugin without approval.
""",
        encoding="utf-8",
    )
    (commit_gate_dir / "SKILL.md").write_text(
        """---
name: selfdex-commit-gate
description: Use when a verified Selfdex task should be closed with commit gate.
---

# Selfdex Commit Gate

Use `scripts/check_commit_gate.py` before commit.
Use `scripts/check_github_actions_status.py` after push.
Require Conventional Commits.
Check GitHub Actions.
Do not select the next candidate until GitHub status is closed.
Run only when the user explicitly asks for it.
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
    (scripts / "check_commit_gate.py").write_text("# fixture\n", encoding="utf-8")
    (scripts / "check_github_actions_status.py").write_text("# fixture\n", encoding="utf-8")
    (root / ".codex" / "config.toml").write_text("[features]\nmulti_agent = true\n", encoding="utf-8")
    agent_models = {
        "explorer": ("explorer", "low"),
        "worker": ("worker", "high"),
        "reviewer": ("reviewer", "xhigh"),
        "docs-researcher": ("docs_researcher", "medium"),
    }
    for file_name, (agent_name, effort) in agent_models.items():
        (codex_agents / f"{file_name}.toml").write_text(
            "\n".join(
                [
                    f'name = "{agent_name}"',
                    'model = "gpt-5.5"',
                    f'model_reasoning_effort = "{effort}"',
                    'sandbox_mode = "read-only"',
                    'description = "fixture"',
                    'developer_instructions = "Implement only the frozen task slice assigned by the main agent. Stay inside the declared write boundary."',
                    "",
                ]
            ),
            encoding="utf-8",
        )


class SelfdexPluginTests(unittest.TestCase):
    def test_validates_plugin_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_plugin_fixture(root)

            payload = check_selfdex_plugin.build_payload(root)

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["finding_count"], 0)
        self.assertEqual(payload["plugin_name"], "selfdex")
        self.assertEqual(payload["commit_gate_phrase_count"], 7)
        self.assertEqual(payload["codex_agent_file_count"], 5)

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

    def test_rejects_stale_codex_agent_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_plugin_fixture(root)
            explorer_path = root / ".codex" / "agents" / "explorer.toml"
            explorer_path.write_text(
                explorer_path.read_text(encoding="utf-8").replace('model = "gpt-5.5"', 'model = "gpt-5.4-mini"'),
                encoding="utf-8",
            )

            result = check_selfdex_plugin.build_payload(root)

        self.assertEqual(result["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in result["findings"]}
        self.assertIn("codex-agent-policy-drift", finding_ids)

    def test_rejects_missing_codex_agent_reasoning_effort(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_plugin_fixture(root)
            reviewer_path = root / ".codex" / "agents" / "reviewer.toml"
            reviewer_path.write_text(
                reviewer_path.read_text(encoding="utf-8").replace('model_reasoning_effort = "xhigh"\n', ""),
                encoding="utf-8",
            )

            result = check_selfdex_plugin.build_payload(root)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(
            any(
                finding["finding_id"] == "codex-agent-policy-drift"
                and "model_reasoning_effort" in finding["summary"]
                for finding in result["findings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
