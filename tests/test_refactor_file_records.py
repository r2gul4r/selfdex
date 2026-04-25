from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from script_loader_utils import load_script
from symbol_definition_test_utils import assert_standard_symbol_definitions


ROOT = Path(__file__).resolve().parents[1]


refactor_file_records = load_script("refactor_file_records.py")


class RefactorFileRecordsTests(unittest.TestCase):
    def test_read_text_lines_replaces_decode_errors(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            path = Path(temp_dir) / "broken.txt"
            path.write_bytes(b"alpha\n\xff\nomega\n")

            lines = refactor_file_records.read_text_lines(path)

        self.assertEqual(lines[0], "alpha")
        self.assertEqual(lines[2], "omega")
        self.assertIn("\ufffd", lines[1])

    def test_extract_definitions_supports_python_shell_and_powershell(self) -> None:
        assert_standard_symbol_definitions(self, refactor_file_records.extract_definitions)

    def test_build_file_records_and_symbol_helpers_preserve_locations(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            script = root / "scripts" / "sample.py"
            script.parent.mkdir()
            script.write_text(
                "def first():\n"
                "    return 1\n"
                "\n"
                "def second():\n"
                "    if True:\n"
                "        return 2\n",
                encoding="utf-8",
            )
            metrics = {
                "files": [
                    {"path": "scripts/sample.py", "language": "python"},
                    {"path": "README.md", "language": "markdown"},
                ]
            }

            records = refactor_file_records.build_file_records(root, metrics)

        self.assertEqual(list(records), ["scripts/sample.py"])
        record = records["scripts/sample.py"]
        self.assertEqual([item.name for item in record.definitions], ["first", "second"])
        self.assertEqual(
            refactor_file_records.find_enclosing_symbol(record, 5).name,
            "second",
        )
        self.assertEqual(
            [(symbol.name, span) for symbol, span in refactor_file_records.symbol_spans(record)],
            [("first", 3), ("second", 3)],
        )


if __name__ == "__main__":
    unittest.main()
