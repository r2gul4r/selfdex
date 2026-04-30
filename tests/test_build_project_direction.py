from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_project_direction.py"
SPEC = importlib.util.spec_from_file_location("build_project_direction", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
build_project_direction = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_project_direction
SPEC.loader.exec_module(build_project_direction)


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_product_fixture(root: Path) -> None:
    write_file(
        root,
        "README.md",
        "# Movie Finder\n\n"
        "A web app for users who compare movie showtimes, recommendations, and booking paths.\n"
        "The backend API collects schedule data and serves the frontend experience.\n",
    )
    write_file(root, "frontend/src/pages/home.tsx", "export function Home() { return null }\n")
    write_file(root, "backend/src/main/java/app/MovieController.java", "class MovieController {}\n")
    write_file(root, "scripts/ingest_showtimes.py", "print('ingest')\n")
    write_file(root, "tests/test_home.py", "def test_home():\n    assert True\n")


class BuildProjectDirectionTests(unittest.TestCase):
    def test_infers_project_direction_from_docs_and_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_product_fixture(root)

            payload = build_project_direction.build_payload(root, limit=5)

        labels = {item["label"] for item in payload["product_signals"]}
        opportunity_ids = {item["opportunity_id"] for item in payload["opportunities"]}

        self.assertEqual(payload["analysis_kind"], "selfdex_project_direction")
        self.assertIn("Movie Finder", payload["purpose"]["summary"])
        self.assertIn("end users", payload["audience"])
        self.assertIn("interactive_experience", labels)
        self.assertIn("service_layer", labels)
        self.assertIn("data_pipeline", labels)
        self.assertIn("direction:core-user-journey", opportunity_ids)
        self.assertIn("direction:data-quality-loop", opportunity_ids)
        self.assertIn("evidence", payload["purpose"])
        self.assertIn("quote", payload["purpose"]["evidence"][0])

    def test_opportunities_are_scored_for_strategy_not_only_hygiene(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_product_fixture(root)

            payload = build_project_direction.build_payload(root, limit=1)

        opportunity = payload["opportunities"][0]

        self.assertEqual(opportunity["source"], "project_direction")
        self.assertEqual(opportunity["work_type"], "direction")
        self.assertGreaterEqual(opportunity["priority_score"], 38)
        self.assertIn("strategic_fit", opportunity["strategic_dimensions"])
        self.assertIn("suggested_first_step", opportunity)
        self.assertIn("evidence", opportunity)
        self.assertIn("path", opportunity["evidence"][0])
        self.assertIn("signal", opportunity["evidence"][0])
        self.assertIn("quote", opportunity["evidence"][0])
        self.assertIn("confidence", opportunity["evidence"][0])
        self.assertIn("python -m unittest discover -s tests", opportunity["suggested_checks"])

    def test_run_artifacts_are_not_used_as_direction_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(root, "README.md", "# Direction\n\nA developer automation project.\n")
            write_file(root, "runs/20260430-old.md", "test secret api deployment note\n")
            write_file(root, "scripts/run.py", "print('ok')\n")

            payload = build_project_direction.build_payload(root, limit=3)

        all_paths = [
            path
            for opportunity in payload["opportunities"]
            for path in opportunity["evidence_paths"]
        ]
        self.assertFalse(any(path.startswith("runs/") for path in all_paths))

    def test_doc_only_product_signal_rules_still_infer_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(root, "README.md", "# Docs Only\n\nThis backend API service has no source files yet.\n")

            payload = build_project_direction.build_payload(root, limit=3)

        service_signal = next(
            item for item in payload["product_signals"] if item["label"] == "service_layer"
        )
        self.assertEqual(service_signal["evidence_paths"], [])


if __name__ == "__main__":
    unittest.main()
