from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from script_loader_utils import load_script
from script_smoke_utils import run_script_and_module


ROOT = Path(__file__).resolve().parents[1]


repo_scan_excludes = load_script("repo_scan_excludes.py")
test_gap = load_script("extract_test_gap_candidates.py")


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_bytes(root: Path, relative_path: str, content: bytes) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


class RepoScanExcludesTests(unittest.TestCase):
    def test_default_scan_excludes_cover_common_generated_directories(self) -> None:
        excluded = repo_scan_excludes.DEFAULT_SCAN_EXCLUDED_DIRS

        for directory in ("node_modules", "dist", "build", "coverage", ".venv", "venv", ".next", ".codex-backups"):
            self.assertIn(directory, excluded)

    def test_path_has_excluded_dir_uses_relative_root_parts(self) -> None:
        root = Path("workspace")

        self.assertTrue(
            repo_scan_excludes.path_has_excluded_dir(
                root / "node_modules" / "package" / "index.js",
                root=root,
            )
        )
        self.assertFalse(repo_scan_excludes.path_has_excluded_dir(root / "src" / "index.js", root=root))

    def test_collect_repo_metrics_skips_dependency_and_build_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(root, "src/app.py", "def run():\n    return 1\n")
            write_file(root, "node_modules/pkg/index.py", "def generated():\n    return 2\n")
            write_file(root, "dist/bundle.py", "def bundled():\n    return 3\n")
            write_file(root, ".venv/lib/site.py", "def env_file():\n    return 4\n")
            write_bytes(root, "assets/logo.png", b"\x89PNG\r\n\x1a\n")

            script_output, module_output = run_script_and_module(
                repo_root=ROOT,
                script_name="collect_repo_metrics.py",
                module_name="collect_repo_metrics",
                args=["--root", str(root)],
            )

        for output in (script_output, module_output):
            payload = json.loads(output.stdout)
            self.assertEqual([item["path"] for item in payload["files"]], ["src/app.py"])

    def test_test_gap_scan_filter_skips_dependency_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated = root / "node_modules" / "pkg" / "tool.py"
            source = root / "scripts" / "tool.py"
            write_file(root, "node_modules/pkg/tool.py", "def generated():\n    return 1\n")
            write_file(root, "scripts/tool.py", "def source():\n    return 1\n")

            self.assertFalse(test_gap.should_scan(generated, root=root))
            self.assertTrue(test_gap.should_scan(source, root=root))


if __name__ == "__main__":
    unittest.main()
