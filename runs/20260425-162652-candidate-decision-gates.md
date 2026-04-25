# Run Record: Candidate Decision Gates

- time: `2026-04-25T16:30:43+09:00`
- task: `deduplicate candidate decision gates`
- profile: `autopilot-single`
- score_total: `5`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `scripts/candidate_scoring_utils.py`
  - `scripts/extract_refactor_candidates.py`
  - `scripts/feature_small_candidates.py`
  - `tests/test_candidate_scoring_utils.py`

## Summary

Added `determine_common_axis_decision` to `scripts/candidate_scoring_utils.py` for the shared common-axis gate used by refactor and small-feature candidates.
`determine_refactor_decision` and `determine_small_feature_decision` now call that helper first, while keeping their type-specific rubric checks local.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_candidate_scoring_utils.py`: passed, 4 tests.
- `python -m unittest discover -s tests -p test_feature_small_candidates.py`: passed, 3 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: passed.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed.
- `python -m scripts.extract_feature_gap_candidates --root . --format json`: passed.
- `python -m scripts.extract_refactor_candidates --root . --format json`: passed.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 100 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed; selected `main 중복 정리`.
- `python scripts/plan_next_task.py --root . --format markdown`: passed; selected `main 중복 정리`.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue with the planner-selected `main` dedupe between `scripts/check_doc_drift.py` and `scripts/list_project_registry.py`.
