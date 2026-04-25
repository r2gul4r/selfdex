from __future__ import annotations

import unittest
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]


feature_file_records = load_script("feature_file_records.py")
feature_gap_evidence = load_script("feature_gap_evidence.py")


def file_record(
    relative_path: str,
    content: str,
    *,
    definitions: list[object] | None = None,
    is_test_file: bool = False,
) -> object:
    lines = content.splitlines()
    return feature_file_records.FileRecord(
        path=Path(relative_path),
        relative_path=relative_path,
        lines=lines,
        content=content,
        language="python",
        is_test_file=is_test_file,
        definitions=definitions or [],
    )


class FeatureGapEvidenceTests(unittest.TestCase):
    def test_evidence_helpers_find_call_flow_and_tests(self) -> None:
        symbol = feature_file_records.SymbolLocation(name="run_task", line=1, symbol_kind="function")
        source = file_record(
            "scripts/tool.py",
            "def run_task():\n"
            "    return 1\n\n"
            "run_task()\n",
            definitions=[symbol],
        )
        test_record = file_record(
            "tests/test_tool.py",
            "def test_run_task():\n"
            "    assert run_task() == 1\n",
            is_test_file=True,
        )
        repo_index = {"records": [source, test_record], "test_records": [test_record]}

        related = feature_gap_evidence.find_related_records(
            repo_index,
            "run_task",
            "root_tooling",
            ["scripts/tool.py"],
        )
        call_flow = feature_gap_evidence.build_call_flow(repo_index, "run_task", related)
        test_evidence = feature_gap_evidence.build_test_evidence(
            repo_index,
            "run_task",
            "run_task",
            ["scripts/tool.py"],
        )

        self.assertEqual([record.relative_path for record in related], ["scripts/tool.py"])
        self.assertEqual(call_flow["status"], "linked")
        self.assertEqual(call_flow["definition"]["path"], "scripts/tool.py")
        self.assertFalse(test_evidence["missing_tests"])
        self.assertEqual(test_evidence["matched_test_files"][0]["path"], "tests/test_tool.py")

    def test_assess_gap_scores_overlapping_evidence(self) -> None:
        candidates = [
            {"signal_id": "not_implemented"},
            {"signal_id": "todo"},
            {"signal_id": "stub"},
        ]
        call_flow = {"status": "defined_only"}
        test_evidence = {"missing_tests": True}

        assessment = feature_gap_evidence.assess_gap(candidates, call_flow, test_evidence)

        self.assertEqual(assessment["decision"], "confirmed_gap")
        self.assertEqual(assessment["confidence"], "high")
        self.assertEqual(assessment["score"], 5)
        self.assertIn("관련 테스트 흔적이 없음", assessment["reasons"])

    def test_detector_self_reference_lines_are_suppressed(self) -> None:
        self.assertTrue(
            feature_gap_evidence.is_detector_self_reference(
                'weak_signals = sum(signal_counts.get(signal_id, 0) for signal_id in ("todo", "stub"))'
            )
        )
        self.assertTrue(
            feature_gap_evidence.is_detector_self_reference(
                'reasons.append("명시적인 미구현/누락 신호가 확인됨")'
            )
        )
        self.assertTrue(feature_gap_evidence.is_detector_self_reference('    "todo",'))
        self.assertTrue(feature_gap_evidence.is_detector_self_reference('    "placeholder",'))
        self.assertFalse(feature_gap_evidence.is_detector_self_reference("# TODO wire action"))

    def test_feature_scan_skips_detector_self_references_but_keeps_real_todo(self) -> None:
        feature_gap = load_script("extract_feature_gap_candidates.py")
        record = file_record(
            "scripts/tool.py",
            "STOPWORDS = {\n"
            "    \"todo\",\n"
            "    \"stub\",\n"
            "    \"placeholder\",\n"
            "}\n\n"
            "def assess_gap():\n"
            "    weak_signals = sum(signal_counts.get(signal_id, 0) for signal_id in (\"todo\", \"stub\"))\n"
            "    reasons.append(\"명시적인 미구현/누락 신호가 확인됨\")\n\n"
            "def run_action():\n"
            "    # TODO wire action\n"
            "    return None\n",
            definitions=[
                feature_file_records.SymbolLocation(name="assess_gap", line=7, symbol_kind="function"),
                feature_file_records.SymbolLocation(name="run_action", line=11, symbol_kind="function"),
            ],
        )

        candidates = feature_gap.scan_file(ROOT, record)

        self.assertEqual([candidate["feature_key"] for candidate in candidates], ["run_action"])
        self.assertEqual(candidates[0]["signal_id"], "todo")

    def test_feature_scan_skips_test_files_as_candidate_sources(self) -> None:
        feature_gap = load_script("extract_feature_gap_candidates.py")
        record = file_record(
            "tests/test_tool.py",
            "def test_run_action():\n"
            "    # TODO wire action\n"
            "    assert True\n",
            definitions=[
                feature_file_records.SymbolLocation(
                    name="test_run_action",
                    line=1,
                    symbol_kind="function",
                ),
            ],
            is_test_file=True,
        )

        self.assertEqual(feature_gap.scan_file(ROOT, record), [])

    def test_feature_extractor_reexports_moved_evidence_helpers(self) -> None:
        feature_gap = load_script("extract_feature_gap_candidates.py")

        self.assertEqual(feature_gap.extract_tokens("run_task", "todo"), ["run_task"])
        self.assertEqual(feature_gap.summarize_signals([{"signal_id": "todo"}]), {"todo": 1})
        self.assertEqual(feature_gap.find_related_records.__name__, "find_related_records")
        self.assertEqual(feature_gap.is_detector_self_reference.__name__, "is_detector_self_reference")
        self.assertEqual(feature_gap.assess_gap.__name__, "assess_gap")


if __name__ == "__main__":
    unittest.main()
