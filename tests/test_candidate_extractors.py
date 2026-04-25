from __future__ import annotations

import importlib.util
import json
import subprocess
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

    def test_refactor_extractor_builds_duplicate_candidate_from_metrics_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            duplicate_body = "\n".join(
                [
                    "def shared_flow():",
                    "    value = 1",
                    "    value += 1",
                    "    value += 2",
                    "    value += 3",
                    "    value += 4",
                    "    value += 5",
                    "    value += 6",
                    "    value += 7",
                    "    value += 8",
                    "    value += 9",
                    "    return value",
                    "",
                ]
            )
            write_file(root, "scripts/alpha.py", duplicate_body)
            write_file(root, "scripts/beta.py", duplicate_body)
            base_metrics = {
                "language": "python",
                "complexity": {"cyclomatic_estimate": 20},
                "module_size": {"code_lines": 12},
                "duplication": {"group_count": 1},
                "change_frequency": {"commit_count": 2},
            }
            metrics_payload = {
                "summary": {"file_count": 2},
                "files": [
                    {"path": "scripts/alpha.py", **base_metrics},
                    {"path": "scripts/beta.py", **base_metrics},
                ],
                "duplication": {
                    "groups": [
                        {
                            "fingerprint": "fixture-shared-flow",
                            "normalized_line_count": 12,
                            "occurrence_count": 2,
                            "excerpt": ["value += 1", "return value"],
                            "modules": [
                                {"path": "scripts/alpha.py", "start_line": 1, "end_line": 12},
                                {"path": "scripts/beta.py", "start_line": 1, "end_line": 12},
                            ],
                        }
                    ]
                },
            }

            candidates = refactor.build_refactor_candidates(root, metrics_payload, limit=3)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["candidate_kind"], "refactor")
        self.assertEqual(candidates[0]["source_signals"]["candidate_source"], "duplicate_block")
        self.assertEqual(candidates[0]["source_signals"]["paths"], ["scripts/alpha.py", "scripts/beta.py"])
        self.assertEqual(candidates[0]["common_score"], refactor.compute_common_score(candidates[0]["common_axes"]))

    def test_refactor_extractor_runs_as_script_and_module_with_metrics_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(
                root,
                "scripts/hotspot.py",
                "def parse_config():\n    return {}\n\n"
                "def render_report():\n    return ''\n",
            )
            metrics_path = root / "metrics.json"
            metrics_path.write_text(
                json.dumps(
                    {
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
                ),
                encoding="utf-8",
            )
            script_command = [
                sys.executable,
                str(ROOT / "scripts" / "extract_refactor_candidates.py"),
                "--root",
                str(root),
                "--metrics-input",
                str(metrics_path),
                "--format",
                "json",
            ]
            module_command = [
                sys.executable,
                "-m",
                "scripts.extract_refactor_candidates",
                "--root",
                str(root),
                "--metrics-input",
                str(metrics_path),
                "--format",
                "json",
            ]

            script_output = subprocess.run(
                script_command,
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            module_output = subprocess.run(
                module_command,
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        script_payload = json.loads(script_output.stdout)
        module_payload = json.loads(module_output.stdout)

        self.assertEqual(script_payload["schema_version"], 1)
        self.assertEqual(module_payload["schema_version"], 1)
        self.assertEqual(
            script_payload["refactor_candidates"][0]["source_signals"]["path"],
            "scripts/hotspot.py",
        )
        self.assertEqual(
            module_payload["refactor_candidates"][0]["source_signals"]["path"],
            "scripts/hotspot.py",
        )


if __name__ == "__main__":
    unittest.main()
