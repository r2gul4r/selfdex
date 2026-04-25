# Run Record: Plan Next Task Argparse Helper Reuse

- time: `2026-04-25T15:40:28+09:00`
- task: `reuse argparse helpers in plan_next_task`
- profile: `autopilot-single`
- score_total: `5`
- agent_budget: `0`
- write_set:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `ERROR_LOG.md`
  - `scripts/plan_next_task.py`
  - `tests/test_argparse_utils.py`

## Summary

Rewired `scripts/plan_next_task.py` to use the shared `add_root_argument` and `add_format_argument` helpers.
The planner still defaults to markdown output, preserving existing CLI behavior.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_argparse_utils.py`: passed, 5 tests.
- `python -m unittest discover -s tests -p test_plan_next_task.py`: failed in sandbox due Windows Temp fixture write permissions, then passed after approved escalation, 11 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python -m unittest discover -s tests`: failed in sandbox due Windows Temp/root fixture write permissions, then passed after approved escalation, 83 tests.
- `python scripts/plan_next_task.py --root . --format markdown`: initially failed when the verification pipe truncated stdout; passed when rerun without truncation.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.

## Next

- Continue `scripts/plan_next_task.py` responsibility split.
- The next likely slice is extracting campaign queue parsing/scoring into a helper module.
