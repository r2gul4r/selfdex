# Product Signal Block Dedup

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: current workspace branch
- final_status: `completed`
- outcome_class: `success`

## Selected Candidate

- source: `refactor`
- title: `scripts/build_project_direction.py duplicate block cleanup`
- work_type: `improvement`
- priority_score: `50.6`
- topology: `autopilot-single`
- agent_budget: `0`

## Frozen Task Contract

- Replace repeated product signal detection blocks in `scripts/build_project_direction.py` with a data-driven rule helper.
- Preserve existing product signal labels, summaries, path patterns, and doc keyword behavior.
- Keep doc-only product signal creation working when no matching source paths exist.
- Do not modify external target repositories.
- Do not execute target-project Codex sessions.

## Changes

- Added `PRODUCT_SIGNAL_RULES` and `product_signal_from_rule()` in `scripts/build_project_direction.py`.
- Replaced four repeated path/keyword/append blocks with a loop over the rule table.
- Collapsed duplicated `project_direction_evidence` fallback import blocks into a module alias import.
- Added focused doc-only product signal coverage in `tests/test_build_project_direction.py`.
- Logged the Windows Temp sandbox verification failure and alias shadowing repair in `ERROR_LOG.md`.

## Changed Files

- `scripts/build_project_direction.py`
- `tests/test_build_project_direction.py`
- `ERROR_LOG.md`
- `STATE.md`
- `CAMPAIGN_STATE.md`
- `runs/selfdex/20260430-132542-product-signal-block-dedup.md`

## Verification

- `python -m unittest tests.test_build_project_direction`: passed, 4 tests
- `python scripts/collect_repo_metrics.py --root . --paths scripts\build_project_direction.py --pretty --min-duplicate-lines 10`: passed, duplicate `group_count=0`
- `python -m compileall -q scripts tests`: passed
- `python scripts/build_project_direction.py --root . --format json`: passed, `opportunity_count=4`
- `python scripts/build_external_candidate_snapshot.py --root . --project-id fs --limit 2 --format json`: passed, `candidate_count=2`, `scanner_error_count=0`
- `python scripts/plan_next_task.py --root . --format json`: passed, next selected candidate moved to `scripts/run_target_codex.py responsibility split`
- `python -m unittest discover -s tests`: passed, 169 tests
- `python scripts/check_doc_drift.py --root . --format json`: passed, `finding_count=0`
- `git diff --check`: passed, with expected LF-to-CRLF working-copy warnings
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed, `violation_count=0`

## Repair Attempts

- Reran focused tests with approved sandbox escalation after Windows Temp fixture writes were denied in the normal sandbox.
- Renamed the module alias from `evidence` to `direction_evidence` after focused tests exposed local variable shadowing in `infer_purpose()`.

## Failure Or Stop Reason

- none
