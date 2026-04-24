from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "markdown_utils.py"
SPEC = importlib.util.spec_from_file_location("markdown_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
markdown_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = markdown_utils
SPEC.loader.exec_module(markdown_utils)


class MarkdownUtilsTests(unittest.TestCase):
    def test_clean_markdown_value_strips_wrapping_backticks(self) -> None:
        self.assertEqual(markdown_utils.clean_markdown_value(" `STATE.md` "), "STATE.md")
        self.assertEqual(markdown_utils.clean_markdown_value("`a` and `b`"), "a and b")

    def test_extract_markdown_section_stops_at_peer_heading(self) -> None:
        text = """# Title

## Campaign

- goal: `Build`

### Nested

- still here

## Candidate Queue

- next
"""

        section = markdown_utils.extract_markdown_section(text, "Campaign")

        self.assertIn("- goal: `Build`", section)
        self.assertIn("- still here", section)
        self.assertNotIn("- next", section)


if __name__ == "__main__":
    unittest.main()
