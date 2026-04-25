# Run: script-loader-utils

- time: `2026-04-25T17:17:13+09:00`
- task: `deduplicate test script loader boilerplate`
- profile: `autopilot-mixed`
- score_total: `8`
- agent_budget: `1`
- actual_topology: `main implementation plus one read-only reviewer`

## Contract

- Add a shared test helper for importlib-based script loading.
- Replace only duplicated local `load_script` helper blocks in the planner-selected tests.
- Preserve loaded script names, module registration behavior, and assertions.

## Changes

- Added `tests/script_loader_utils.py` with `load_script(...)`.
- Updated planner-selected tests to import and use the shared loader:
  - `tests/test_candidate_extractors.py`
  - `tests/test_candidate_scoring_utils.py`
  - `tests/test_cli_output_utils.py`
  - `tests/test_feature_file_records.py`
  - `tests/test_feature_gap_evidence.py`
  - `tests/test_feature_small_candidates.py`
  - `tests/test_planner_text_utils.py`
  - `tests/test_refactor_file_records.py`
  - `tests/test_refactor_metrics_payload.py`
  - `tests/test_symbol_definition_utils.py`

## Review

- Reviewer result: clean.
- Reviewer confirmed the helper preserves `module_name = name.replace(".py", "")`, `spec_from_file_location`, `sys.modules[spec.name] = module` before `exec_module`, and unchanged script names in touched tests.
- Reviewer residual risk was only inability to run Python in its shell; main covered that with bundled-Python focused and full-suite verification.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- Focused touched tests passed:
  - `test_candidate_scoring_utils.py`
  - `test_cli_output_utils.py`
  - `test_feature_gap_evidence.py`
  - `test_feature_small_candidates.py`
  - `test_planner_text_utils.py`
  - `test_refactor_metrics_payload.py`
  - `test_symbol_definition_utils.py`
- Focused touched tests that write fixtures hit sandbox Temp/root write denial, then passed after approved escalation:
  - `test_candidate_extractors.py`
  - `test_feature_file_records.py`
  - `test_refactor_file_records.py`
- `rg` found no remaining local `load_script` boilerplate/importlib/sys/ModuleType block in touched tests.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed; this duplicate is no longer selected.
- `python scripts/plan_next_task.py --root . --format json`: passed; next selected candidate is historical run-record duplicate text.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python -m unittest discover -s tests`: sandbox Temp/root fixture write denial, then passed after approved escalation; 110 tests OK.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF warnings only.

## Result

- Repeated script-loading boilerplate now has one shared test helper.
- Test loading semantics and assertions were preserved.
- Planner advanced to the next bounded candidate.

## Next

- Evaluate whether historical run-record duplicate text should be edited, deferred, or handled by changing future run templates instead of rewriting old audit records.
