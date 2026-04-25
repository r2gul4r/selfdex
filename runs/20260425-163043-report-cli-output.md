# Run Record: Report CLI Output

- time: `2026-04-25T16:34:30+09:00`
- task: `deduplicate report CLI output`
- profile: `autopilot-single`
- score_total: `5`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `README.md`
  - `scripts/cli_output_utils.py`
  - `scripts/check_doc_drift.py`
  - `scripts/list_project_registry.py`
  - `tests/test_cli_output_utils.py`

## Summary

Added `scripts/cli_output_utils.py` with `write_json_or_markdown` for shared pretty JSON and markdown stdout emission.
`scripts/check_doc_drift.py` and `scripts/list_project_registry.py` now keep their own parsing, payload building, error handling, and exit-code policy while delegating only the duplicated output block.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_cli_output_utils.py`: passed, 2 tests.
- `python -m unittest discover -s tests -p test_doc_drift.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python -m unittest discover -s tests -p test_project_registry.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 3 tests.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format markdown`: passed.
- `python scripts/list_project_registry.py --root . --format json`: passed.
- `python scripts/list_project_registry.py --root . --format markdown`: passed.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 102 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed; selected `parse_args 중복 정리`.
- `python scripts/plan_next_task.py --root . --format markdown`: passed; selected `parse_args 중복 정리`.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue with the planner-selected `parse_args` dedupe between `scripts/build_external_validation_report.py` and `scripts/prepare_candidate_quality_template.py`.
