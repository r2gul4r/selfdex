# Slug Helper Dedup

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: current workspace branch
- final_status: `completed`
- outcome_class: `success`

## Selected Candidate

- source: `refactor`
- title: `slugify + sanitize_slug duplicate cleanup`
- work_type: `improvement`
- priority_score: `48.3`
- topology: `autopilot-single`
- agent_budget: `0`

## Frozen Task Contract

- Move duplicated slug normalization from `scripts/plan_external_project.py` and `scripts/record_run.py` into one shared helper.
- Preserve `plan_external_project.slugify(value)` fallback behavior as `external-project`.
- Preserve `record_run.sanitize_slug(value)` fallback behavior as `run`.
- Preserve `record_run.sanitize_project_key(value)` fallback behavior as `project`.
- Do not change timestamp validation, artifact layout, or target-project execution behavior.

## Changes

- Added `scripts/slug_utils.py` with shared `normalize_slug(value, fallback=...)`.
- Updated `scripts/plan_external_project.py` to keep `slugify()` as a compatibility wrapper.
- Updated `scripts/record_run.py` to keep `sanitize_slug()` and `sanitize_project_key()` as compatibility wrappers.
- Added `tests/test_slug_utils.py` for the shared slug policy.

## Changed Files

- `scripts/slug_utils.py`
- `scripts/plan_external_project.py`
- `scripts/record_run.py`
- `tests/test_slug_utils.py`
- `STATE.md`
- `CAMPAIGN_STATE.md`
- `runs/selfdex/20260430-135412-slug-helper-dedup.md`

## Verification

- `python -m unittest tests.test_slug_utils tests.test_record_run tests.test_plan_external_project tests.test_run_target_codex`: passed, 23 tests
- `python scripts/collect_repo_metrics.py --root . --paths scripts\plan_external_project.py scripts\record_run.py --pretty --min-duplicate-lines 10`: passed, duplicate `group_count=0`
- `python -m compileall -q scripts tests`: passed
- `python scripts/plan_next_task.py --root . --format json`: passed, next selected candidate moved to `test_main_returns_zero_for_dry_run_blocked + test_main_returns_two_for_execute_blocked`
- `python scripts/check_doc_drift.py --root . --format json`: passed, `finding_count=0`
- `python -m unittest discover -s tests`: passed, 170 tests
- `git diff --check`: passed, with expected LF-to-CRLF working-copy warnings
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed, `violation_count=0`

## Repair Attempts

- none

## Failure Or Stop Reason

- none
