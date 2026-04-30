from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "slug_utils.py"
SPEC = importlib.util.spec_from_file_location("slug_utils", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
slug_utils = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = slug_utils
SPEC.loader.exec_module(slug_utils)


class SlugUtilsTests(unittest.TestCase):
    def test_normalize_slug_preserves_existing_slug_policy(self) -> None:
        self.assertEqual(slug_utils.normalize_slug("Run Recorder! v1", fallback="run"), "run-recorder-v1")
        self.assertEqual(slug_utils.normalize_slug("다보여 프로젝트!!", fallback="project"), "다보여-프로젝트")
        self.assertEqual(slug_utils.normalize_slug("!!!", fallback="run"), "run")


if __name__ == "__main__":
    unittest.main()
