from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = ROOT / "package.json"
CLI = ROOT / "bin" / "selfdex.js"
INSTALLER = ROOT / "install.ps1"
TMP_BASE = ROOT / ".tmp-tests"


def resolve_command(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found

    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / name
    )
    if bundled.exists():
        return str(bundled)

    if name == "npm":
        npm_cmd = bundled.with_suffix(".cmd")
        if npm_cmd.exists():
            return str(npm_cmd)

    return None


NODE = resolve_command("node")
NPM = resolve_command("npm")


def write_node_doctor_fixture(root: Path, home: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    for name in ("plan_external_project.py", "run_target_codex.py", "check_github_actions_status.py"):
        (scripts / name).write_text("# fixture\n", encoding="utf-8")

    codex_agents = root / ".codex" / "agents"
    codex_agents.mkdir(parents=True, exist_ok=True)
    (root / ".codex" / "config.toml").write_text(
        "\n".join(
            [
                "[features]",
                "multi_agent = true",
                "",
                "[agents]",
                "max_threads = 6",
                "max_depth = 1",
                "",
                "[agents.explorer]",
                'config_file = "agents/explorer.toml"',
                "[agents.worker]",
                'config_file = "agents/worker.toml"',
                "[agents.reviewer]",
                'config_file = "agents/reviewer.toml"',
                "[agents.docs_researcher]",
                'config_file = "agents/docs-researcher.toml"',
            ]
        ),
        encoding="utf-8",
    )
    (codex_agents / "explorer.toml").write_text(
        'name = "explorer"\nmodel = "gpt-5.5"\nmodel_reasoning_effort = "low"\nsandbox_mode = "read-only"\n',
        encoding="utf-8",
    )
    (codex_agents / "worker.toml").write_text(
        'name = "worker"\nmodel = "gpt-5.5"\nmodel_reasoning_effort = "high"\n# frozen task slice\n# declared write boundary\n',
        encoding="utf-8",
    )
    (codex_agents / "reviewer.toml").write_text(
        'name = "reviewer"\nmodel = "gpt-5.5"\nmodel_reasoning_effort = "xhigh"\nsandbox_mode = "read-only"\n',
        encoding="utf-8",
    )
    (codex_agents / "docs-researcher.toml").write_text(
        'name = "docs_researcher"\nmodel = "gpt-5.5"\nmodel_reasoning_effort = "medium"\nsandbox_mode = "read-only"\n',
        encoding="utf-8",
    )

    plugin = home / "plugins" / "selfdex"
    skill = home / "skills" / "selfdex"
    marketplace = home / ".agents" / "plugins"
    plugin.mkdir(parents=True, exist_ok=True)
    skill.mkdir(parents=True, exist_ok=True)
    marketplace.mkdir(parents=True, exist_ok=True)
    (plugin / "selfdex-root.json").write_text(
        json.dumps({"schema_version": 1, "selfdex_root": str(root.resolve())}),
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text("---\nname: selfdex\n---\n", encoding="utf-8")
    (marketplace / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": "selfdex", "source": {"path": "./plugins/selfdex"}}]}),
        encoding="utf-8",
    )


class NpmCliTests(unittest.TestCase):
    def test_package_declares_selfdex_bin(self) -> None:
        payload = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))

        self.assertEqual(payload["name"], "selfdex")
        self.assertEqual(payload["bin"]["selfdex"], "bin/selfdex.js")
        self.assertIn("bin/", payload["files"])
        self.assertIn("install.ps1", payload["files"])
        self.assertNotIn("preinstall", payload.get("scripts", {}))
        self.assertNotIn("postinstall", payload.get("scripts", {}))

    @unittest.skipIf(NODE is None, "node is not available")
    def test_help_and_version_commands(self) -> None:
        help_result = subprocess.run(
            [NODE, str(CLI), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)
        self.assertIn("selfdex install", help_result.stdout)
        self.assertIn("selfdex doctor", help_result.stdout)
        self.assertIn("--dry-run", help_result.stdout)

        version_result = subprocess.run(
            [NODE, str(CLI), "--version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(version_result.returncode, 0, version_result.stdout + version_result.stderr)
        self.assertIn(json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["version"], version_result.stdout)

    @unittest.skipIf(NODE is None, "node is not available")
    def test_install_dry_run_delegates_to_bootstrap_without_writes(self) -> None:
        TMP_BASE.mkdir(exist_ok=True)
        install_root = TMP_BASE / f"selfdex-install-root-{uuid.uuid4().hex}"
        result = subprocess.run(
            [
                NODE,
                str(CLI),
                "install",
                "--dry-run",
                "--install-root",
                str(install_root),
                "--repo-url",
                "https://example.invalid/selfdex.git",
                "--branch",
                "test-branch",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("dry run", output.lower())
        self.assertIn("test-branch", output)
        self.assertIn(install_root.name, output)
        self.assertIn("check_selfdex_setup.py", output)
        self.assertFalse(install_root.exists())

    @unittest.skipIf(NODE is None, "node is not available")
    def test_doctor_help_command(self) -> None:
        result = subprocess.run(
            [NODE, str(CLI), "doctor", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("selfdex doctor", result.stdout)
        self.assertIn("--codex-home", result.stdout)
        self.assertIn("legacy Python", result.stdout)

    @unittest.skipIf(NODE is None, "node is not available")
    def test_doctor_runs_node_native_by_default(self) -> None:
        TMP_BASE.mkdir(exist_ok=True)
        install_root = TMP_BASE / f"selfdex-doctor-root-{uuid.uuid4().hex}"
        home = TMP_BASE / f"selfdex-doctor-home-{uuid.uuid4().hex}"
        write_node_doctor_fixture(install_root, home)

        result = subprocess.run(
            [
                NODE,
                str(CLI),
                "doctor",
                "--install-root",
                str(install_root),
                "--home",
                str(home),
                "--codex-home",
                str(home),
                "--format",
                "json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        check_ids = {check["check_id"]: check for check in payload["checks"]}
        self.assertEqual(payload["runtime"], "node-native")
        self.assertEqual(check_ids["node-doctor"]["status"], "pass")
        self.assertEqual(check_ids["selfdex-global-skill"]["status"], "pass")
        self.assertNotIn("python-command", check_ids)

    @unittest.skipIf(NODE is None, "node is not available")
    def test_doctor_python_option_uses_legacy_python_doctor(self) -> None:
        TMP_BASE.mkdir(exist_ok=True)
        install_root = TMP_BASE / f"selfdex-python-doctor-root-{uuid.uuid4().hex}"
        scripts = install_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        (scripts / "check_selfdex_setup.py").write_text(
            "print('legacy python doctor marker')\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                NODE,
                str(CLI),
                "doctor",
                "--install-root",
                str(install_root),
                "--python",
                sys.executable,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("legacy python doctor marker", result.stdout)

    @unittest.skipIf(NPM is None, "npm is not available")
    def test_npm_pack_dry_run_includes_bootstrap_files(self) -> None:
        TMP_BASE.mkdir(exist_ok=True)
        cache_dir = TMP_BASE / "npm-cache"
        cache_dir.mkdir(exist_ok=True)
        env = os.environ.copy()
        env["npm_config_cache"] = str(cache_dir)
        result = subprocess.run(
            [NPM, "pack", "--dry-run", "--json"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)[0]
        files = {entry["path"] for entry in payload["files"]}
        self.assertIn("package.json", files)
        self.assertIn("bin/selfdex.js", files)
        self.assertIn("install.ps1", files)

    def test_cli_does_not_define_publish_side_effects(self) -> None:
        text = CLI.read_text(encoding="utf-8")
        installer_text = INSTALLER.read_text(encoding="utf-8")

        self.assertIn("install.ps1", text)
        self.assertNotIn("npm publish", text)
        self.assertNotIn("npm publish", installer_text)
        self.assertNotIn("run_target_codex.py --execute", text)


if __name__ == "__main__":
    unittest.main()
