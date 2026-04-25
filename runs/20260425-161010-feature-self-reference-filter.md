# Run Record: Feature Self-Reference Filter

- time: `2026-04-25T16:21:46+09:00`
- task: `suppress detector self-reference feature gaps`
- profile: `autopilot-single`
- score_total: `5`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `scripts/extract_feature_gap_candidates.py`
  - `scripts/feature_gap_evidence.py`
  - `tests/test_feature_gap_evidence.py`

## Summary

Added a narrow detector self-reference suppression helper so feature-gap scanning skips its own `signal_counts.get(...)`, `reasons.append(...)`, and `signal_id` vocabulary lines.
The scan still detects normal TODO/stub/not-implemented lines, and planner output now advances past the false-positive `assess_gap` capability candidate.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_feature_gap_evidence.py`: passed, 5 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 5 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: passed.
- `python scripts/extract_feature_gap_candidates.py --root . --format markdown`: passed.
- `python -m scripts.extract_feature_gap_candidates --root . --format json`: passed.
- `feature extractor assess_gap candidate count`: `0`.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 97 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed; selected `extract_definitions 중복 정리`.
- `python scripts/plan_next_task.py --root . --format markdown`: passed; selected `extract_definitions 중복 정리`.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue with the planner-selected `extract_definitions` dedupe between `scripts/feature_file_records.py` and `scripts/refactor_file_records.py`.
