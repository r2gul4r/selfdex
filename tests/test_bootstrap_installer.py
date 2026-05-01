from __future__ import annotations

import subprocess
import shutil
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.ps1"


def powershell_executable() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def powershell_command_args(executable: str, *args: str) -> list[str]:
    command = [executable, "-NoProfile"]
    if Path(executable).name.lower().startswith("powershell"):
        command.extend(["-ExecutionPolicy", "Bypass"])
    command.extend(args)
    return command


class BootstrapInstallerTests(unittest.TestCase):
    def test_bootstrap_script_contains_clone_update_and_plugin_install(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")

        self.assertIn("git", text)
        self.assertIn("clone", text)
        self.assertIn("pull", text)
        self.assertIn("--ff-only", text)
        self.assertIn("scripts\\install_selfdex_plugin.py", text)
        self.assertIn("--yes", text)
        self.assertIn("--force", text)
        self.assertIn("check_selfdex_setup.py", text)
        self.assertIn("DryRun", text)
        self.assertNotIn("run_target_codex.py", text)
        self.assertNotIn("Remove-Item", text)

    def test_bootstrap_script_parses_as_powershell(self) -> None:
        executable = powershell_executable()
        if executable is None:
            self.skipTest("PowerShell runtime is not available")

        command = (
            "$errors = $null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            f"'{INSTALLER}', [ref]$null, [ref]$errors) > $null; "
            "if ($errors.Count -gt 0) { $errors | ForEach-Object { $_.Message }; exit 1 }"
        )

        result = subprocess.run(
            powershell_command_args(executable, "-Command", command),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bootstrap_dry_run_does_not_clone_or_install(self) -> None:
        executable = powershell_executable()
        if executable is None:
            self.skipTest("PowerShell runtime is not available")

        install_root = "C:/tmp/selfdex-bootstrap-dry-run"
        result = subprocess.run(
            powershell_command_args(
                executable,
                "-File",
                str(INSTALLER),
                "-DryRun",
                "-InstallRoot",
                install_root,
            ),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("dry run", output.lower())
        self.assertIn("would clone Selfdex", output)
        self.assertIn("install_selfdex_plugin.py", output)
        self.assertIn("check_selfdex_setup.py", output)


if __name__ == "__main__":
    unittest.main()
