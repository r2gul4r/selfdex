from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> ModuleType:
    path = ROOT / "scripts" / name
    module_name = name.replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


test_gap = load_script("extract_test_gap_candidates.py")
feature_gap = load_script("extract_feature_gap_candidates.py")
refactor = load_script("extract_refactor_candidates.py")


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CandidateExtractorFixtureTests(unittest.TestCase):
    def test_test_gap_extractor_finds_missing_python_tool_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(root, "scripts/collect_repo_metrics.py", "def collect():\n    return 1\n")
            write_file(root, "scripts/extract_feature_gap_candidates.py", "def extract():\n    return []\n")
            write_file(root, "scripts/normalize_quality_signals.py", "def normalize():\n    return {}\n")

            payload = test_gap.build_payload(root)

        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertEqual(payload["schema_version"], 1)
        self.assertIn("missing-tests-python-analysis-tools", finding_ids)

    def test_feature_gap_extractor_finds_fixture_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            marker = "TO" + "DO"
            write_file(
                root,
                "scripts/sample_tool.py",
                f"def run():\n    # {marker} wire action\n    return None\n",
            )

            payload = feature_gap.extract_feature_gap_candidates(root)

        signal_ids = {
            candidate["signal_id"]
            for area in payload["areas"]
            for candidate in area["candidates"]
        }
        self.assertEqual(payload["schema_version"], 3)
        self.assertGreater(payload["candidate_count"], 0)
        self.assertIn(("to" + "do"), signal_ids)

    def test_refactor_extractor_builds_hotspot_candidate_from_metrics_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(
                root,
                "scripts/hotspot.py",
                "def parse_config():\n    return {}\n\n"
                "def render_report():\n    return ''\n",
            )
            metrics_payload = {
                "summary": {"file_count": 1},
                "files": [
                    {
                        "path": "scripts/hotspot.py",
                        "language": "python",
                        "complexity": {"cyclomatic_estimate": 120},
                        "module_size": {"code_lines": 620},
                        "duplication": {"group_count": 2},
                        "change_frequency": {"commit_count": 1},
                    }
                ],
                "duplication": {"groups": []},
            }

            candidates = refactor.build_refactor_candidates(root, metrics_payload, limit=3)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["candidate_kind"], "refactor")
        self.assertEqual(candidates[0]["source_signals"]["candidate_source"], "complexity_hotspot")
        self.assertEqual(candidates[0]["source_signals"]["path"], "scripts/hotspot.py")


if __name__ == "__main__":
    unittest.main()
