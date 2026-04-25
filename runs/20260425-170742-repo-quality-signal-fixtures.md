# Run: repo-quality-signal-fixtures

- time: `2026-04-25T17:10:21+09:00`
- task: `deduplicate repo quality signal metric fixtures`
- profile: `autopilot-single`
- score_total: `5`
- agent_budget: `0`
- actual_topology: `single local writer`

## Contract

- Add a shared test helper for repo metric hotspot and low-signal fixture payloads.
- Replace only duplicated fixture literals in the two selected tests.
- Preserve quality signal expectations and called normalization functions.

## Changes

- Added `tests/repo_quality_signal_test_utils.py` with hotspot, low-signal, and payload fixture builders.
- Updated `tests/test_normalize_quality_signals.py` to reuse the full repo metrics payload helper.
- Updated `tests/test_repo_quality_signal_utils.py` to reuse the hotspot metric item helper.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_normalize_quality_signals.py`: passed.
- `python -m unittest discover -s tests -p test_repo_quality_signal_utils.py`: passed.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed; this duplicate is no longer selected.
- `python scripts/plan_next_task.py --root . --format json`: passed; next selected candidate is broad `load_script` helper duplication.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python -m unittest discover -s tests`: sandbox Temp/root fixture write denial, then passed after approved escalation; 110 tests OK.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF warnings only.

## Result

- Repo quality signal fixture values now live in one test helper.
- Normalization/scoring behavior was not changed.
- Planner advanced to the next broader refactor candidate.

## Next

- Deduplicate repeated test script-loading boilerplate across multiple tests, with careful write-set ownership because the candidate spans many files.
