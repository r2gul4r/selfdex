from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]


feature_file_records = load_script("feature_file_records.py")


def write_file(root: Path, relative_path: str, content: bytes | str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


class FeatureFileRecordTests(unittest.TestCase):
    def test_iter_repo_files_filters_feature_scan_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(root, "scripts/target.py", "def run():\n    return 1\n")
            write_file(root, "scripts/extract_feature_gap_candidates.py", "def skip():\n    return 0\n")
            write_file(root, "STATE.md", "# ignored\n")
            write_file(root, "assets/image.png", b"\x89PNG\r\n")
            write_file(root, ".git/config", "[core]\n")
            write_file(root, "node_modules/pkg/generated.py", "def ignored():\n    return 2\n")
            write_file(root, "dist/generated.py", "def ignored():\n    return 3\n")

            files = feature_file_records.iter_repo_files(
                root,
                exclude_filename="extract_feature_gap_candidates.py",
            )

        self.assertEqual([path.relative_to(root).as_posix() for path in files], ["scripts/target.py"])

    def test_build_repo_index_records_symbols_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(
                root,
                "scripts/tool.py",
                "class Runner:\n"
                "    pass\n\n"
                "def run_task():\n"
                "    return 1\n",
            )
            write_file(root, "tests/test_tool.py", "def test_run_task():\n    assert True\n")
            files = feature_file_records.iter_repo_files(root)

            index = feature_file_records.build_repo_index(root, files)

        record = index["by_relative_path"]["scripts/tool.py"]
        test_record = index["by_relative_path"]["tests/test_tool.py"]

        self.assertFalse(record.is_test_file)
        self.assertTrue(test_record.is_test_file)
        self.assertEqual([symbol.name for symbol in record.definitions], ["Runner", "run_task"])
        self.assertEqual(
            feature_file_records.find_enclosing_symbol(record, 5).name,
            "run_task",
        )

    def test_feature_extractor_reexports_moved_helpers(self) -> None:
        feature_gap = load_script("extract_feature_gap_candidates.py")

        self.assertEqual(feature_gap.FileRecord.__name__, feature_file_records.FileRecord.__name__)
        self.assertEqual(feature_gap.iter_repo_files.__name__, "iter_repo_files")
        self.assertEqual(feature_gap.build_repo_index.__name__, "build_repo_index")
        self.assertEqual(feature_gap.normalize_excerpt("  alpha   beta  "), "alpha beta")


if __name__ == "__main__":
    unittest.main()
