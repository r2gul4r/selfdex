from __future__ import annotations

import json
import os
import shutil
import subprocess
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
