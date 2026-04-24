from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_doc_drift.py"
SPEC = importlib.util.spec_from_file_location("check_doc_drift", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
check_doc_drift = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_doc_drift
SPEC.loader.exec_module(check_doc_drift)


README_TEMPLATE = """# Selfdex

## Core Files

| Path | Role |
| :-- | :-- |
| `AGENTS.md` | Rules |
| `AUTOPILOT.md` | Policy |
| `CAMPAIGN_STATE.md` | Campaign |
| `STATE.md` | Task state |
| `PROJECT_REGISTRY.md` | Registry |
| `docs/SELFDEX_FINAL_GOAL.md` | Goal |
| `runs/` | Run records |
| `scripts/plan_next_task.py` | Planner |
| `scripts/check_campaign_budget.py` | Budget check |
| `scripts/check_doc_drift.py` | Drift check |
| `scripts/collect_repo_metrics.py` | Metrics |
| `scripts/extract_*_candidates.py` | Candidate extractors |
| `scripts/record_run.py` | Run recorder |

## Quick Start

```bash
python scripts/plan_next_task.py --root . --format markdown
python scripts/check_campaign_budget.py --root . --format markdown
python scripts/check_doc_drift.py --root . --format markdown
python scripts/collect_repo_metrics.py --root . --pretty
python scripts/extract_test_gap_candidates.py --root . --format markdown
```
"""


def write_repo(root: Path, readme: str = README_TEMPLATE) -> None:
    (root / "README.md").write_text(readme, encoding="utf-8")
    (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (root / "AUTOPILOT.md").write_text("# Autopilot\n", encoding="utf-8")
    (root / "CAMPAIGN_STATE.md").write_text("# Campaign\n", encoding="utf-8")
    (root / "STATE.md").write_text("# State\n", encoding="utf-8")
    (root / "PROJECT_REGISTRY.md").write_text("# Registry\n", encoding="utf-8")
    (root / "runs").mkdir()
    (root / "docs").mkdir()
    (root / "docs" / "SELFDEX_FINAL_GOAL.md").write_text("# Goal\n", encoding="utf-8")
    scripts = root / "scripts"
    scripts.mkdir()
    for name in (
        "plan_next_task.py",
        "check_campaign_budget.py",
        "check_doc_drift.py",
        "collect_repo_metrics.py",
        "extract_test_gap_candidates.py",
        "extract_refactor_candidates.py",
        "record_run.py",
    ):
        (scripts / name).write_text("# script\n", encoding="utf-8")


class DocDriftTests(unittest.TestCase):
    def test_passes_when_readme_documents_core_paths_and_report_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_repo(root)

            payload = check_doc_drift.build_payload(root)

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["finding_count"], 0)

    def test_wildcard_documents_matching_extractor_scripts(self) -> None:
        text = "```text\nignore `scripts/not_real.py`\n```\n" + README_TEMPLATE
        paths = check_doc_drift.documented_code_paths(text)

        self.assertTrue(check_doc_drift.is_documented("scripts/extract_test_gap_candidates.py", paths))
        self.assertTrue(check_doc_drift.is_documented("scripts/extract_refactor_candidates.py", paths))
        self.assertFalse(check_doc_drift.is_documented("scripts/not_real.py", paths))

    def test_fails_when_report_script_is_missing_from_readme(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            readme = README_TEMPLATE.replace("| `scripts/record_run.py` | Run recorder |\n", "")
            write_repo(root, readme=readme)

            payload = check_doc_drift.build_payload(root)

        self.assertEqual(payload["status"], "fail")
        finding_paths = {finding["path"] for finding in payload["findings"]}
        self.assertIn("scripts/record_run.py", finding_paths)

    def test_fails_when_quick_start_report_command_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            readme = README_TEMPLATE.replace(
                "python scripts/check_doc_drift.py --root . --format markdown\n",
                "",
            )
            write_repo(root, readme=readme)

            payload = check_doc_drift.build_payload(root)

        self.assertEqual(payload["status"], "fail")
        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertIn("missing-quick-start-report-command", finding_ids)

    def test_markdown_lists_generated_report_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_repo(root)
            payload = check_doc_drift.build_payload(root)

        markdown = check_doc_drift.render_markdown(payload)

        self.assertIn("# Doc Drift Check", markdown)
        self.assertIn("- status: `pass`", markdown)
        self.assertIn("scripts/check_doc_drift.py", markdown)


if __name__ == "__main__":
    unittest.main()
