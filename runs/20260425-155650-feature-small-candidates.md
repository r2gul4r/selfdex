# Run Record: Feature Small Candidates

- time: `2026-04-25T15:59:16+09:00`
- task: `extract feature small-candidate scoring helpers`
- profile: `autopilot-single`
- score_total: `6`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `README.md`
  - `scripts/extract_feature_gap_candidates.py`
  - `scripts/feature_small_candidates.py`
  - `tests/test_feature_small_candidates.py`

## Summary

Moved small-feature scoring, decision thresholds, implementation-scope text, rationale construction, and sorted candidate-list construction into `scripts/feature_small_candidates.py`.
`scripts/extract_feature_gap_candidates.py` imports and re-exports the moved helper names, keeping downstream helper imports compatible while shrinking the extractor body.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_feature_small_candidates.py`: first failed due an incorrect fixture expectation, then passed after fixing the fixture, 3 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: passed.
- `python scripts/extract_feature_gap_candidates.py --root . --format markdown`: passed.
- `python -m scripts.extract_feature_gap_candidates --root . --format json`: passed.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 92 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue with the planner-selected feature-gap extractor cleanup, likely reducing duplicated symbol-definition helpers shared with refactor extraction.
