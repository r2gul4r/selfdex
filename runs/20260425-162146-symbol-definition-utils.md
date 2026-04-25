# Run Record: Symbol Definition Utils

- time: `2026-04-25T16:26:52+09:00`
- task: `deduplicate extract_definitions helpers`
- profile: `autopilot-single`
- score_total: `5`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `README.md`
  - `scripts/symbol_definition_utils.py`
  - `scripts/feature_file_records.py`
  - `scripts/refactor_file_records.py`
  - `tests/test_symbol_definition_utils.py`

## Summary

Moved duplicated Python, shell, and PowerShell symbol-definition extraction into `scripts/symbol_definition_utils.py`.
`scripts/feature_file_records.py` and `scripts/refactor_file_records.py` now import and re-export `SymbolLocation` and `extract_definitions`, preserving existing caller names while removing the duplicated regex and branch logic.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_symbol_definition_utils.py`: passed, 2 tests.
- `python -m unittest discover -s tests -p test_feature_file_records.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 3 tests.
- `python -m unittest discover -s tests -p test_refactor_file_records.py`: failed in sandbox due workspace Temp fixture write permissions, then passed after approved escalation, 3 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: passed.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed.
- `python -m scripts.extract_feature_gap_candidates --root . --format json`: passed.
- `python -m scripts.extract_refactor_candidates --root . --format json`: passed.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 99 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed; selected `determine_refactor_decision + determine_small_feature_decision 중복 정리`.
- `python scripts/plan_next_task.py --root . --format markdown`: passed; selected `determine_refactor_decision + determine_small_feature_decision 중복 정리`.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue with the planner-selected decision-helper dedupe between `scripts/extract_refactor_candidates.py` and `scripts/feature_small_candidates.py`.
