# Run Record: Plan Next Task Import Dedupe

- time: `2026-04-25T15:48:05+09:00`
- task: `deduplicate planner text import fallback`
- profile: `autopilot-single`
- score_total: `4`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `scripts/plan_next_task.py`

## Summary

Replaced the duplicated `planner_text_utils` direct/fallback import list in `scripts/plan_next_task.py` with a module alias.
Existing module-level helper names are bound once after import, preserving compatibility for tests and callers.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_plan_next_task.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 11 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python -m scripts.plan_next_task --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed; next candidate moved to `scripts/extract_feature_gap_candidates.py` responsibility split.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 86 tests.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Follow planner output: inspect `scripts/extract_feature_gap_candidates.py` and choose the smallest safe helper extraction.
