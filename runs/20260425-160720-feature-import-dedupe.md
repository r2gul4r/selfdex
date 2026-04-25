# Run Record: Feature Import Dedupe

- time: `2026-04-25T16:09:05+09:00`
- task: `deduplicate feature extractor fallback imports`
- profile: `autopilot-single`
- score_total: `4`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `scripts/extract_feature_gap_candidates.py`

## Summary

Replaced repeated direct/fallback helper import lists in `scripts/extract_feature_gap_candidates.py` with module aliases for `feature_file_records`, `feature_gap_evidence`, and `feature_small_candidates`.
Existing module-level helper names are still bound once after import, preserving compatibility while reducing duplicate import blocks.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_feature_gap_evidence.py`: passed, 3 tests.
- `python -m unittest discover -s tests -p test_feature_small_candidates.py`: passed, 3 tests.
- `python -m unittest discover -s tests -p test_feature_file_records.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 3 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: passed after approved escalation, 5 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: passed.
- `python -m scripts.extract_feature_gap_candidates --root . --format json`: passed.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 95 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue with the next planner candidate, likely deduplicating symbol-definition helpers shared between feature and refactor file-record modules.
