# Run Record: Planner Text Utils

- time: `2026-04-25T15:44:44+09:00`
- task: `extract planner text helpers`
- profile: `autopilot-single`
- score_total: `6`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `README.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `scripts/planner_text_utils.py`
  - `scripts/plan_next_task.py`
  - `tests/test_planner_text_utils.py`

## Summary

Moved campaign markdown parsing, token matching, and work-type classification from `scripts/plan_next_task.py` into `scripts/planner_text_utils.py`.
`plan_next_task.py` keeps module-level helper compatibility through imports, so existing tests and callers can still use the same names.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_planner_text_utils.py`: passed, 3 tests.
- `python -m unittest discover -s tests -p test_plan_next_task.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 11 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed; next candidate moved to a smaller `scripts/plan_next_task.py` duplicate-block cleanup.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 86 tests.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Follow planner output: inspect the remaining `scripts/plan_next_task.py` duplicate block and remove only the smallest safe duplication.
