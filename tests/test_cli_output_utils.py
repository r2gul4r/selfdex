from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]


cli_output_utils = load_script("cli_output_utils.py")


class CliOutputUtilsTests(unittest.TestCase):
    def test_write_json_or_markdown_emits_pretty_json(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            cli_output_utils.write_json_or_markdown(
                {"message": "안녕"},
                "json",
                lambda payload: "# ignored\n",
            )

        output = stdout.getvalue()
        self.assertEqual(json.loads(output), {"message": "안녕"})
        self.assertIn('\n  "message": "안녕"\n', output)
        self.assertTrue(output.endswith("\n"))

    def test_write_json_or_markdown_uses_markdown_renderer(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            cli_output_utils.write_json_or_markdown(
                {"title": "Report"},
                "markdown",
                lambda payload: f"# {payload['title']}\n",
            )

        self.assertEqual(stdout.getvalue(), "# Report\n")


if __name__ == "__main__":
    unittest.main()
