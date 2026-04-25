from __future__ import annotations

import unittest
from pathlib import Path

from script_loader_utils import load_script
from symbol_definition_test_utils import assert_standard_symbol_definitions


ROOT = Path(__file__).resolve().parents[1]


symbol_definition_utils = load_script("symbol_definition_utils.py")


class SymbolDefinitionUtilsTests(unittest.TestCase):
    def test_extract_definitions_supports_python_shell_and_powershell(self) -> None:
        assert_standard_symbol_definitions(self, symbol_definition_utils.extract_definitions)

    def test_caller_modules_reexport_shared_symbol_helpers(self) -> None:
        feature_file_records = load_script("feature_file_records.py")
        refactor_file_records = load_script("refactor_file_records.py")

        self.assertEqual(feature_file_records.SymbolLocation.__name__, "SymbolLocation")
        self.assertEqual(refactor_file_records.SymbolLocation.__name__, "SymbolLocation")
        self.assertEqual(feature_file_records.extract_definitions.__name__, "extract_definitions")
        self.assertEqual(refactor_file_records.extract_definitions.__name__, "extract_definitions")
        self.assertEqual(
            [(item.name, item.line, item.symbol_kind) for item in feature_file_records.extract_definitions("python", ["def go():"])],
            [("go", 1, "function")],
        )
        self.assertEqual(
            [(item.name, item.line, item.symbol_kind) for item in refactor_file_records.extract_definitions("python", ["class Box:"])],
            [("Box", 1, "class")],
        )


if __name__ == "__main__":
    unittest.main()
