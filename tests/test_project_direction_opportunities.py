from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "scripts" / "project_direction_evidence.py"
EVIDENCE_SPEC = importlib.util.spec_from_file_location("project_direction_evidence", EVIDENCE_PATH)
if EVIDENCE_SPEC is None or EVIDENCE_SPEC.loader is None:
    raise RuntimeError(f"Could not load {EVIDENCE_PATH}")
project_direction_evidence = importlib.util.module_from_spec(EVIDENCE_SPEC)
sys.modules[EVIDENCE_SPEC.name] = project_direction_evidence
EVIDENCE_SPEC.loader.exec_module(project_direction_evidence)

SCRIPT_PATH = ROOT / "scripts" / "project_direction_opportunities.py"
SPEC = importlib.util.spec_from_file_location("project_direction_opportunities", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT_PATH}")
project_direction_opportunities = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = project_direction_opportunities
SPEC.loader.exec_module(project_direction_opportunities)


class ProjectDirectionOpportunityTests(unittest.TestCase):
    def test_build_opportunities_keeps_direction_payload_contract(self) -> None:
        root = Path("fixture-root")
        files = [
            root / "frontend" / "home.tsx",
            root / "backend" / "api.py",
            root / "tests" / "test_home.py",
        ]
        purpose = {
            "summary": "Fixture project is the clearest documented project anchor.",
            "evidence_paths": ["README.md"],
        }
        product_signals = [
            {
                "label": "interactive_experience",
                "summary": "The project exposes a user-facing surface.",
                "evidence_paths": ["frontend/home.tsx"],
            }
        ]
        constraints = [
            {
                "label": "local_verification_available",
                "summary": "There is a local test surface.",
                "evidence_paths": ["tests/test_home.py"],
            }
        ]

        opportunities = project_direction_opportunities.build_opportunities(
            root=root,
            files=files,
            purpose=purpose,
            product_signals=product_signals,
            technical_signals=[],
            constraints=constraints,
            quote_map={"README.md": "Fixture project direction."},
            limit=3,
        )

        self.assertEqual(opportunities[0]["source"], "project_direction")
        self.assertEqual(opportunities[0]["work_type"], "direction")
        self.assertIn("priority_grade", opportunities[0])
        self.assertIn("strategic_dimensions", opportunities[0])
        self.assertIn("suggested_first_step", opportunities[0])
        self.assertIn("python -m unittest discover -s tests", opportunities[0]["suggested_checks"])


if __name__ == "__main__":
    unittest.main()
