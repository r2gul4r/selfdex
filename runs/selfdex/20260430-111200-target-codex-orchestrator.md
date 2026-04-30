# Target Codex Orchestrator

- goal: implement Selfdex target-project Codex automation with project-scoped run records
- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: `main`
- selected candidate: user-approved implementation plan
- topology: `autopilot-single`
- agent budget used: `0`
- project_key: `selfdex`
- write sets:
  - `STATE.md`
  - `CAMPAIGN_STATE.md`
  - `README.md`
  - `AUTOPILOT.md`
  - `docs/SELFDEX_FINAL_GOAL.md`
  - `scripts/plan_external_project.py`
  - `scripts/record_run.py`
  - `scripts/run_target_codex.py`
  - `scripts/check_campaign_budget.py`
  - `tests/test_plan_external_project.py`
  - `tests/test_record_run.py`
  - `tests/test_run_target_codex.py`
  - `tests/test_campaign_budget.py`

## Selected Candidate

- User-approved plan: add Selfdex target-project orchestration that scans a target repository, selects one candidate, creates a contract, creates a target branch, starts target Codex in that target `cwd`, and records results under `runs/<project_key>/`.

## Frozen Task Contract

- Implement one-candidate target Codex orchestration.
- Default to non-mutating dry-run behavior unless `--execute` is passed.
- Require branch isolation before target-project writes.
- Record target run artifacts in Selfdex under `runs/<project_key>/<YYYYMMDD-HHMMSS>-<task-slug>.md`.
- Resolve project key from `project_id`, then ad-hoc `project_name`, then target folder name.
- Keep hard approval zones separate from folder-wide target execution approval.

## Codex Session

- thread_id: `not launched for verification`
- session_id: `not launched for verification`
- note: implementation tests use a fake runner; no real target-project Codex session was started.

## Changed Files

- `CAMPAIGN_STATE.md`
- `README.md`
- `AUTOPILOT.md`
- `docs/SELFDEX_FINAL_GOAL.md`
- `scripts/plan_external_project.py`
- `scripts/record_run.py`
- `scripts/run_target_codex.py`
- `scripts/check_campaign_budget.py`
- `tests/test_plan_external_project.py`
- `tests/test_record_run.py`
- `tests/test_run_target_codex.py`
- `tests/test_campaign_budget.py`
- `runs/selfdex/20260430-111200-target-codex-orchestrator.md`

## Result

- Added `scripts/run_target_codex.py` to plan one target candidate, optionally create a target branch, run a Codex app-server adapter, and write a Selfdex artifact.
- Changed run records and external plan artifacts to use `runs/<project_key>/`.
- Added campaign-budget handling so run artifacts do not falsely trip hard approval hints.
- Documented the target execution shape in Selfdex docs.
- final status: `completed`

## Verification

- `python -m unittest discover -s tests -p test_run_target_codex.py`: passed, ran 4 tests.
- `python -m unittest discover -s tests -p test_plan_external_project.py`: passed, ran 5 tests.
- `python -m unittest discover -s tests -p test_record_run.py`: passed, ran 5 tests.
- `python -m unittest discover -s tests -p test_campaign_budget.py`: passed, ran 7 tests.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests`: passed, ran 147 tests.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed, `violation_count=0`.
- `git diff --check`: passed; PowerShell reported LF-to-CRLF working-copy warnings only.

## Repair Attempts

- `0`

## Failure Or Stop Reason

- none

## Notes

- Tests use a fake Codex runner and temporary target repositories; no real target-project Codex execution was launched.
- Real execution still depends on a working local Codex app-server path.
