# Run Record: Feature Gap Evidence

- time: `2026-04-25T16:05:05+09:00`
- task: `extract feature gap evidence helpers`
- profile: `autopilot-single`
- score_total: `7`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `README.md`
  - `scripts/extract_feature_gap_candidates.py`
  - `scripts/feature_gap_evidence.py`
  - `tests/test_feature_gap_evidence.py`

## Summary

Moved token extraction, signal summaries, related path summaries, related-record matching, call-flow inference, test evidence detection, and gap assessment into `scripts/feature_gap_evidence.py`.
`scripts/extract_feature_gap_candidates.py` imports and re-exports the moved helper names, keeping the extractor focused on signal scanning, documentation rendering, grouping, and payload assembly.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_feature_gap_evidence.py`: passed, 3 tests.
- `python -m unittest discover -s tests -p test_feature_file_records.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 3 tests.
- `python -m unittest discover -s tests -p test_feature_small_candidates.py`: passed, 3 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: passed.
- `python scripts/extract_feature_gap_candidates.py --root . --format markdown`: passed.
- `python -m scripts.extract_feature_gap_candidates --root . --format json`: passed.
- `python -m unittest discover -s tests`: first exposed brittle import-identity assertions, then passed after adjusting re-export tests; sandboxed full-suite also failed due Temp/root fixture write permissions and passed after approved escalation, 95 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue planner-guided cleanup. The likely next safe task is deduplicating shared symbol-definition helpers between `feature_file_records.py` and `refactor_file_records.py`.
