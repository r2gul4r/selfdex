# Run: symbol-definition-test-utils

- time: `2026-04-25T17:06:37+09:00`
- task: `deduplicate symbol definition extraction test helper`
- profile: `autopilot-single`
- score_total: `6`
- agent_budget: `0`
- actual_topology: `single local writer`

## Contract

- Add a shared test helper for common python/shell/powershell symbol definition expectations.
- Replace only duplicated expectation setup and assertions in the two selected tests.
- Preserve expected tuples and each test's called `extract_definitions` function.

## Changes

- Added `tests/symbol_definition_test_utils.py` with `assert_standard_symbol_definitions(...)`.
- Updated `tests/test_refactor_file_records.py` to reuse the helper while still exercising `refactor_file_records.extract_definitions`.
- Updated `tests/test_symbol_definition_utils.py` to reuse the helper while still exercising `symbol_definition_utils.extract_definitions`.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_refactor_file_records.py`: sandbox Temp/root fixture write denial, then passed after approved escalation.
- `python -m unittest discover -s tests -p test_symbol_definition_utils.py`: passed.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed; this duplicate is no longer selected.
- `python scripts/plan_next_task.py --root . --format json`: passed; next selected candidate is `test_repo_metrics_normalization_keeps_quality_signal_shape + test_normalize_repo_metric_file_builds_quality_signal_shape`.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python -m unittest discover -s tests`: sandbox Temp/root fixture write denial, then passed after approved escalation; 110 tests OK.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF warnings only.

## Result

- The shared symbol extraction expectation now has one test helper.
- Parser behavior and exported helper behavior were not changed.
- Planner advanced to the next bounded refactor candidate.

## Next

- Deduplicate quality signal shape fixtures across normalize and repo quality signal tests.
