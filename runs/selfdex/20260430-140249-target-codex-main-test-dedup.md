# Run: target Codex main test dedup

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: current working tree
- selected candidate: `test_main_returns_zero_for_dry_run_blocked + test_main_returns_two_for_execute_blocked duplicate cleanup`
- final status: `completed`
- outcome_class: `success`

## Frozen Task Contract

Extract the duplicated stdout/stderr capture and `run_target_codex.main` CLI argument setup shared by the dry-run blocked and execute blocked tests in `tests/test_run_target_codex.py`.

Acceptance:

- Add a narrow local test helper for captured CLI invocation.
- Keep dry-run blocked returning exit code `0` with `outcome_class=dry_run`.
- Keep execute-requested blocked returning exit code `2` with `status=blocked`.
- Confirm duplicate metrics for the target test file no longer report the selected duplicate.
- Confirm planner moves on to a different candidate.

Non-goals:

- Do not change production `run_target_codex.py` behavior.
- Do not change app-server, branch, timeout, or artifact semantics.
- Do not refactor unrelated test fixtures.

## Codex Thread

- thread/session id: local Codex desktop session; no target-project Codex session executed
- target project writes: none

## Changed Files

- `STATE.md`
- `ERROR_LOG.md`
- `tests/test_run_target_codex.py`
- `runs/selfdex/20260430-140249-target-codex-main-test-dedup.md`

## Verification

- `python -m unittest tests.test_run_target_codex`
  - result: passed
  - detail: ran 12 tests
- `python scripts/collect_repo_metrics.py --root . --paths tests\test_run_target_codex.py --pretty --min-duplicate-lines 10`
  - result: passed
  - detail: `group_count=0`, `duplicated_line_instances=0`
- `python -m compileall -q scripts tests`
  - result: passed
- `python scripts/plan_next_task.py --root . --format json`
  - result: passed
  - detail: next selected candidate changed to `tests/test_candidate_quality_template.py` plus `tests/test_external_validation_report.py` duplicate cleanup
- `python scripts/check_doc_drift.py --root . --format json`
  - result: passed
  - detail: `finding_count=0`
- `git diff --check`
  - result: passed
  - detail: exit 0 with LF-to-CRLF working-copy warnings
- `python -m unittest discover -s tests`
  - result: passed after sandbox escalation
  - detail: sandboxed run failed on Windows Temp fixture writes; approved rerun passed 170 tests

## Repair Attempts

- `0`

## Failure Or Stop Reason

- none

## Notes

- The initial sandboxed full-suite failure was logged as resolved in `ERROR_LOG.md`.
