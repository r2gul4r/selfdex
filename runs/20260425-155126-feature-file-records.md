# Run Record: Feature File Records

- time: `2026-04-25T15:54:03+09:00`
- task: `extract feature gap file-record helpers`
- profile: `autopilot-mixed`
- score_total: `8`
- agent_budget: `1`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `README.md`
  - `scripts/extract_feature_gap_candidates.py`
  - `scripts/feature_file_records.py`
  - `tests/test_feature_file_records.py`

## Summary

Moved feature-gap repository file scanning, text loading, test-file detection, definition extraction, repo-index building, and enclosing-symbol lookup into `scripts/feature_file_records.py`.
`scripts/extract_feature_gap_candidates.py` now imports those helpers, re-exports the moved helper names for compatibility, and still excludes itself from repository scans through an explicit `exclude_filename`.

Explorer sidecar recommended a small-feature scoring extraction instead.
Main kept the file-record extraction because it mirrors the existing refactor helper boundary and avoids changing candidate scoring, sorting, or decision semantics in this step.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_feature_file_records.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 3 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: passed.
- `python scripts/extract_feature_gap_candidates.py --root . --format markdown`: passed.
- `python -m scripts.extract_feature_gap_candidates --root . --format json`: passed.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 89 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue reducing `scripts/extract_feature_gap_candidates.py` by extracting the small-feature scoring/selection helpers recommended by the explorer.
