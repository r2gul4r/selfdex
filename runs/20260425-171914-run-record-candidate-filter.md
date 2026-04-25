# Run: run-record-candidate-filter

- time: `2026-04-25T17:24:41+09:00`
- task: `exclude run records from refactor candidate metrics`
- profile: `autopilot-single`
- score_total: `6`
- agent_budget: `0`
- actual_topology: `single local writer`

## Contract

- Do not rewrite historical run records.
- Filter `runs/` audit records out of refactor metrics payloads.
- Preserve normal source/script eligibility and scoring formulas.

## Changes

- Added `runs` to `SKIP_DIRS` in `scripts/refactor_metrics_payload.py`.
- Updated `tests/test_refactor_metrics_payload.py` so run records are skipped as files and pruned from duplicate groups.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_refactor_metrics_payload.py`: passed.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: sandbox Temp/root fixture write denial, then passed after approved escalation.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed; `refactor_candidate_count` is 0 and run-record duplicate is no longer selected.
- `python scripts/plan_next_task.py --root . --format json`: passed; next selected candidate is coverage signal production hardening.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python -m unittest discover -s tests`: sandbox Temp/root fixture write denial, then passed after approved escalation; 110 tests OK.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF warnings only.

## Result

- Historical run records stay canonical audit evidence instead of becoming refactor edit targets.
- Refactor candidate selection is cleaner and now moves to a real hardening gap.

## Next

- Add a bounded coverage signal production path or a local coverage report fixture so candidate planning can see branch/line coverage evidence.
