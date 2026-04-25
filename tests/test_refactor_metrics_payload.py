from __future__ import annotations

import unittest
from pathlib import Path

from script_loader_utils import load_script


ROOT = Path(__file__).resolve().parents[1]


refactor_metrics_payload = load_script("refactor_metrics_payload.py")


class RefactorMetricsPayloadTests(unittest.TestCase):
    def test_should_skip_repo_path_filters_state_logs_and_internal_dirs(self) -> None:
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("STATE.md"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("nested\\ERROR_LOG.md"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path(".git/config"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("runs/20260425-demo.md"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("tools/__pycache__/cache.pyc"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("node_modules/pkg/index.js"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("dist/generated.js"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path(".venv/lib/site.py"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("package-lock.json"))
        self.assertTrue(refactor_metrics_payload.should_skip_repo_path("nested/pnpm-lock.yaml"))
        self.assertFalse(refactor_metrics_payload.should_skip_repo_path("scripts/tool.py"))
        self.assertFalse(refactor_metrics_payload.should_skip_repo_path("package.json"))
        self.assertFalse(refactor_metrics_payload.should_skip_repo_path("build.xml"))

    def test_filter_metrics_payload_prunes_files_and_duplicate_groups(self) -> None:
        payload = {
            "summary": {"file_count": 5},
            "files": [
                {"path": "scripts/a.py"},
                {"path": "scripts/b.py"},
                {"path": "STATE.md"},
                {"path": ".git/config"},
                {"path": "runs/20260425-demo.md"},
                {"path": "node_modules/pkg/index.js"},
                {"path": "package-lock.json"},
            ],
            "duplication": {
                "group_count": 2,
                "groups": [
                    {
                        "fingerprint": "kept",
                        "occurrence_count": 3,
                        "modules": [
                            {"path": "scripts/a.py"},
                            {"path": "scripts/b.py"},
                            {"path": "STATE.md"},
                            {"path": "runs/20260425-demo.md"},
                        ],
                    },
                    {
                        "fingerprint": "dropped",
                        "occurrence_count": 2,
                        "modules": [
                            {"path": "scripts/a.py"},
                            {"path": "ERROR_LOG.md"},
                        ],
                    },
                ],
            },
        }

        filtered = refactor_metrics_payload.filter_metrics_payload(payload)

        self.assertEqual([item["path"] for item in filtered["files"]], ["scripts/a.py", "scripts/b.py"])
        self.assertEqual(filtered["summary"]["file_count"], 2)
        self.assertEqual(filtered["duplication"]["group_count"], 1)
        self.assertEqual(filtered["duplication"]["groups"][0]["fingerprint"], "kept")
        self.assertEqual(filtered["duplication"]["groups"][0]["occurrence_count"], 2)
        self.assertEqual(
            [module["path"] for module in filtered["duplication"]["groups"][0]["modules"]],
            ["scripts/a.py", "scripts/b.py"],
        )

    def test_load_metrics_reads_explicit_json_file_without_collecting(self) -> None:
        payload = refactor_metrics_payload.load_metrics(
            ROOT,
            str(ROOT / "examples" / "quality_signal_samples.json"),
        )

        self.assertIn("results", payload)


if __name__ == "__main__":
    unittest.main()
