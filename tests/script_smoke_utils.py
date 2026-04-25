from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys


def run_script_and_module(
    *,
    repo_root: Path,
    script_name: str,
    module_name: str,
    args: Sequence[str],
) -> tuple[subprocess.CompletedProcess[str], subprocess.CompletedProcess[str]]:
    script_command = [
        sys.executable,
        str(repo_root / "scripts" / script_name),
        *args,
    ]
    module_command = [
        sys.executable,
        "-m",
        f"scripts.{module_name}",
        *args,
    ]

    return (
        subprocess.run(
            script_command,
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ),
        subprocess.run(
            module_command,
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ),
    )
