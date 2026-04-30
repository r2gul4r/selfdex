from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "project_direction_evidence.py"
SPEC = importlib.util.spec_from_file_location("project_direction_evidence", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
project_direction_evidence = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = project_direction_evidence
SPEC.loader.exec_module(project_direction_evidence)


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ProjectDirectionEvidenceTests(unittest.TestCase):
    def test_repo_files_excludes_runs_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(root, "README.md", "# Project\n\nA useful project.\n")
            write_file(root, "runs/old.md", "old run\n")

            files = project_direction_evidence.repo_files(root)

        paths = {project_direction_evidence.rel_path(root, path) for path in files}
        self.assertIn("README.md", paths)
        self.assertNotIn("runs/old.md", paths)

    def test_quote_map_and_evidence_objects_preserve_traceable_quote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            readme = root / "README.md"
            write_file(root, "README.md", "# Project\n\nThis line explains the useful direction clearly.\n")
            docs = [(readme, readme.read_text(encoding="utf-8"))]

            quote_map = project_direction_evidence.quote_map_from_docs(root, docs)
            evidence = project_direction_evidence.evidence_objects(
                ["README.md"],
                signal_text="direction evidence",
                quote_map=quote_map,
            )

        self.assertEqual(quote_map["README.md"], "This line explains the useful direction clearly.")
        self.assertEqual(evidence[0]["quote"], "This line explains the useful direction clearly.")
        self.assertEqual(evidence[0]["signal"], "direction evidence")


if __name__ == "__main__":
    unittest.main()
