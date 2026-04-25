from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from script_loader_utils import load_script


external_readiness = load_script("check_external_validation_readiness.py")


def registry_text(rows: list[str]) -> str:
    return "\n".join(
        [
            "# Project Registry",
            "",
            "## Registered Projects",
            "",
            "| project_id | path | role | write_policy | verification |",
            "| :-- | :-- | :-- | :-- | :-- |",
            "| selfdex | . | harness | selfdex-local writes only | python -m unittest |",
            *rows,
            "",
        ]
    )


def write_registry(root: Path, rows: list[str]) -> None:
    (root / "PROJECT_REGISTRY.md").write_text(registry_text(rows), encoding="utf-8")


class ExternalValidationReadinessTests(unittest.TestCase):
    def test_reports_needs_external_projects_for_selfdex_only_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_registry(root, [])

            payload = external_readiness.build_payload(root)

        self.assertEqual(payload["status"], "needs_external_projects")
        self.assertFalse(payload["external_value_proven"])
        self.assertEqual(payload["external_project_count"], 0)
        self.assertEqual(payload["findings"][0]["finding_id"], "external-project-count-low")

    def test_reports_ready_for_two_existing_read_only_external_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "external-one").mkdir()
            (root / "external-two").mkdir()
            write_registry(
                root,
                [
                    "| external_one | ./external-one | app | read-only | python -m test |",
                    "| external_two | ./external-two | lib | read-only | python -m test |",
                ],
            )

            payload = external_readiness.build_payload(root)

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["finding_count"], 0)
        self.assertEqual(payload["read_only_external_project_count"], 2)

    def test_blocks_non_read_only_or_missing_external_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "external-one").mkdir()
            write_registry(
                root,
                [
                    "| external_one | ./external-one | app | write-enabled | python -m test |",
                    "| external_two | ./missing | lib | read-only | python -m test |",
                ],
            )

            payload = external_readiness.build_payload(root)

        finding_ids = {finding["finding_id"] for finding in payload["findings"]}
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("external-project-not-read-only", finding_ids)
        self.assertIn("external-project-path-missing", finding_ids)

    def test_markdown_shows_next_action(self) -> None:
        payload = {
            "status": "needs_external_projects",
            "validation_mode": "read_only",
            "external_value_proven": False,
            "minimum_external_projects": 2,
            "external_project_count": 0,
            "read_only_external_project_count": 0,
            "findings": [],
            "external_projects": [],
            "next_action": "Register external projects.",
        }

        markdown = external_readiness.render_markdown(payload)

        self.assertIn("# External Validation Readiness", markdown)
        self.assertIn("- status: `needs_external_projects`", markdown)
        self.assertIn("Register external projects.", markdown)


if __name__ == "__main__":
    unittest.main()
