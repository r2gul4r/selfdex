# Run Record: Candidate Scoring Utils

- time: `2026-04-25T15:32:45+09:00`
- task: `extract shared candidate scoring helpers`
- profile: `autopilot-single`
- score_total: `6`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `README.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `scripts/candidate_scoring_utils.py`
  - `scripts/extract_refactor_candidates.py`
  - `scripts/extract_feature_gap_candidates.py`
  - `tests/test_candidate_scoring_utils.py`

## Summary

Moved duplicated common candidate scoring primitives into `scripts/candidate_scoring_utils.py`.
Both feature and refactor candidate extractors now import the shared point map, common score function, and priority grade helper while keeping their decision-specific logic local.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_candidate_scoring_utils.py`: passed, 3 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed, `schema_version=1`, `refactor_candidate_count=5`.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 79 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed; next candidate remains the broader refactor extractor responsibility split.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: initially flagged `scripts/candidate_scoring_utils.py` as undocumented; passed after README repair.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue the broader `scripts/extract_refactor_candidates.py` responsibility split.
- The next smallest slice is likely separating refactor-specific decision/rubric logic from payload rendering.
