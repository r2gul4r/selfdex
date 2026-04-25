from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]
SELFDEX_LOOP_INTEGRATION_MARKER = "selfdex_loop_integration"

extract_test_gap_candidates = load_script("extract_test_gap_candidates.py")
plan_next_task = load_script("plan_next_task.py")


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_goal_cycle_fixture(root: Path) -> None:
    write_file(
        root,
        "CAMPAIGN_STATE.md",
        """# Campaign State

## Campaign

- name: `test`
- goal: `Build a harness that can detect, plan, verify, and record work.`

## Candidate Queue

none
""",
    )
    write_file(
        root,
        "docs/GOAL_COMPARISON_AREAS.md",
        "- 저장소가 자기 부족한 코드 품질과 기능 공백을 스스로 찾고, 개선안을 제안·구현·검증한다\n",
    )
    write_file(
        root,
        "Makefile",
        "test: test-installers\n\tpython -m unittest discover -s tests\n",
    )


def write_empty_extractor(root: Path, script_name: str, payload: dict[str, object]) -> None:
    write_file(
        root,
        f"scripts/{script_name}",
        "import json\n"
        f"print(json.dumps({payload!r}, ensure_ascii=False))\n",
    )


def write_test_gap_wrapper(root: Path) -> None:
    source_path = ROOT / "scripts" / "extract_test_gap_candidates.py"
    write_file(
        root,
        "scripts/extract_test_gap_candidates.py",
        "import importlib.util\n"
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        f"source_path = Path({json.dumps(str(source_path))})\n"
        "spec = importlib.util.spec_from_file_location('real_test_gap', source_path)\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name] = module\n"
        "spec.loader.exec_module(module)\n"
        "root_arg = sys.argv[sys.argv.index('--root') + 1] if '--root' in sys.argv else '.'\n"
        "payload = module.build_payload(Path(root_arg).resolve())\n"
        "print(json.dumps(payload, ensure_ascii=False, indent=2 if '--pretty' in sys.argv else None))\n",
    )


def write_planner_fixture_scripts(root: Path) -> None:
    write_test_gap_wrapper(root)
    write_empty_extractor(root, "extract_refactor_candidates.py", {"refactor_candidates": []})
    write_empty_extractor(root, "extract_feature_gap_candidates.py", {"small_feature_candidates": []})
    write_file(
        root,
        "tests/test_extract_feature_gap_candidates.py",
        "def test_extract_feature_gap_candidates_smoke():\n"
        "    assert 'extract_feature_gap_candidates'\n",
    )


class SelfdexLoopIntegrationTests(unittest.TestCase):
    def test_test_gap_payload_flows_into_planner_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_goal_cycle_fixture(root)
            write_planner_fixture_scripts(root)

            payload = plan_next_task.choose_candidate(root)

        self.assertEqual(payload["selected"]["source"], "test_gap")
        self.assertEqual(payload["selected"]["title"], "자가개선 루프 통합 검증 부재")
        self.assertEqual(payload["selected"]["source_signals"]["category"], "verification_gap")
        self.assertIn("plan_next_task.py --root . --format json", payload["selected"]["suggested_checks"][1])

    def test_goal_cycle_gap_is_suppressed_by_integration_evidence_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_goal_cycle_fixture(root)
            write_file(
                root,
                "tests/test_selfdex_loop_integration.py",
                f"{SELFDEX_LOOP_INTEGRATION_MARKER}\n"
                "extract_test_gap_candidates\n"
                "plan_next_task\n"
                "choose_candidate\n",
            )

            payload = extract_test_gap_candidates.build_payload(root)

        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertNotIn("verification-gap-goal-cycle", finding_ids)


if __name__ == "__main__":
    unittest.main()
