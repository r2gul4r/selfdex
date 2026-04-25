# Error Log

Append-only log for execution, tool, and verification errors.

## Entries

- time: `2026-04-25T13:20:16+09:00`
  location: `tests/test_repo_metrics_utils.py::RepoMetricsUtilsTests.test_analyze_python_file_counts_code_comments_and_complexity`
  summary: `Full-suite verification failed after the Windows path baseline repair was reverted.`
  details: `python -m unittest discover -s tests raised ValueError because scripts/repo_metrics_utils.py compared a short-form ADMINI~1 temp path with a long-form Administrator temp root. Restored the minimal path.resolve().relative_to(root.resolve()) repair.`
  status: `resolved`
- time: `2026-04-25T13:20:16+09:00`
  location: `sandboxed Python test temp directories`
  summary: `Sandboxed test runs left inaccessible temporary directories under the workspace.`
  details: `The workspace-write sandbox denied Python fixture writes and cleanup for .tmp-tests and root tmp* directories. Direct cleanup was also denied, so root-scoped scratch ignore rules were added to prevent git status noise.`
  status: `resolved`
