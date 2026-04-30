# Target Codex App Server Split

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: current workspace branch
- final_status: `completed`
- outcome_class: `success`

## Selected Candidate

- source: `refactor`
- title: `scripts/run_target_codex.py responsibility split`
- work_type: `improvement`
- priority_score: `50.6`
- topology: `autopilot-single`
- agent_budget: `0`

## Frozen Task Contract

- Extract Codex app-server stdio, deadline, stderr, and process cleanup helpers out of `scripts/run_target_codex.py`.
- Keep `scripts/run_target_codex.py` responsible for CLI args, target planning, branch policy, payload assembly, run artifact writing, and rendering.
- Preserve existing payload fields and target execution policies.
- Do not execute a real target-project Codex session.
- Do not weaken timeout, stderr drain, branch restore, or execute-mode exit-code behavior.

## Changes

- Added `scripts/target_codex_app_server.py` for app-server session mechanics:
  - `CodexRunResult`
  - `CodexRunner`
  - `AppServerCodexRunner`
  - deadline and stream readers
  - stderr tail capture
  - process terminate/kill cleanup
  - app-server JSON event parsing
- Updated `scripts/run_target_codex.py` to import the helper module and keep compatibility re-exports for existing tests and downstream imports.
- Removed the app-server session implementation from `scripts/run_target_codex.py`.
- Removed the new import fallback duplicate by using a module alias plus one re-export block.

## Changed Files

- `scripts/run_target_codex.py`
- `scripts/target_codex_app_server.py`
- `STATE.md`
- `CAMPAIGN_STATE.md`
- `runs/selfdex/20260430-133640-target-codex-app-server-split.md`

## Verification

- `python -m unittest tests.test_run_target_codex`: passed, 12 tests
- `python -m compileall -q scripts tests`: passed
- `python scripts/collect_repo_metrics.py --root . --paths scripts\run_target_codex.py --pretty --min-duplicate-lines 10`: passed
  - before: `total_lines=741`, `code_lines=644`, `cyclomatic_estimate=123`
  - after: `total_lines=397`, `code_lines=344`, `cyclomatic_estimate=63`, `duplicate group_count=0`
- `python scripts/collect_repo_metrics.py --root . --paths scripts\target_codex_app_server.py --pretty --min-duplicate-lines 10`: passed, `duplicate group_count=0`
- `python scripts/plan_next_task.py --root . --format json`: passed, next selected candidate moved to `slugify + sanitize_slug duplicate cleanup`
- `python scripts/check_doc_drift.py --root . --format json`: passed, `finding_count=0`
- `python -m unittest discover -s tests`: passed, 169 tests
- `git diff --check`: passed, with expected LF-to-CRLF working-copy warnings
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed, `violation_count=0`

## Repair Attempts

- One in-scope repair removed the duplicate import fallback introduced by the first extraction patch.

## Failure Or Stop Reason

- none
