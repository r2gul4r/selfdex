from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_history_penalty.py"
SPEC = importlib.util.spec_from_file_location("run_history_penalty", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
run_history_penalty = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_history_penalty
SPEC.loader.exec_module(run_history_penalty)


@dataclass(frozen=True)
class CandidateFixture:
    title: str
    priority_score: float
    source_signals: dict[str, Any] = field(default_factory=dict)


def write_run(root: Path, project_id: str, name: str, status: str, title: str) -> None:
    path = root / "runs" / project_id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Target Codex Run\n\n- status: `{status}`\n\n## Selected Candidate\n\n- title: {title}\n",
        encoding="utf-8",
    )


class RunHistoryPenaltyTests(unittest.TestCase):
    def test_failed_run_titles_are_project_scoped_and_status_filtered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_run(root, "external_one", "failed.md", "failed", "Repeat me")
            write_run(root, "external_one", "completed.md", "completed", "Ignore me")
            write_run(root, "external_two", "blocked.md", "blocked", "Other project")

            titles = run_history_penalty.failed_run_titles(root, "external_one")

        self.assertEqual(titles, {"Repeat me"})

    def test_apply_run_history_penalty_marks_and_demotes_repeated_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_run(root, "selfdex", "stopped.md", "stopped", "Repeat me")
            candidates = [
                CandidateFixture("Repeat me", 20, {"existing": True}),
                CandidateFixture("New item", 10),
            ]

            adjusted = run_history_penalty.apply_run_history_penalty(candidates, root)

        self.assertEqual(adjusted[0].priority_score, 12)
        self.assertTrue(adjusted[0].source_signals["existing"])
        self.assertTrue(adjusted[0].source_signals["run_history"]["previous_failed_or_blocked"])
        self.assertEqual(adjusted[0].source_signals["run_history"]["score_adjustment"], -8.0)
        self.assertEqual(adjusted[1], candidates[1])

    def test_none_root_keeps_candidates_unchanged(self) -> None:
        candidates = [CandidateFixture("Repeat me", 20)]

        adjusted = run_history_penalty.apply_run_history_penalty(candidates, None)

        self.assertIs(adjusted, candidates)


if __name__ == "__main__":
    unittest.main()
