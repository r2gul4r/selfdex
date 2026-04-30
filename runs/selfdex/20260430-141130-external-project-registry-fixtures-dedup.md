# Run: external project registry fixtures dedup

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: current working tree
- selected candidate: `write_multi_registry + write_registry duplicate cleanup`
- final status: `completed`
- outcome_class: `success`

## Frozen Task Contract

Move duplicated external project registry and goal-cycle project fixture writers shared by external candidate snapshot and external project planning tests into the shared external validation test utility.

Acceptance:

- Shared fixture helpers write files, goal-cycle project contents, and registry rows used by both selected tests.
- External candidate snapshot tests keep read-only scan, non-read-only skip, explicit selection, missing id, scanner error, run-history, and markdown assertions.
- External project planning tests keep registered, ad-hoc, missing, and project-scoped artifact assertions.
- Duplicate metrics for the selected test paths report `group_count=0`.
- Planner no longer selects this duplicate and reports no remaining candidates.

Non-goals:

- Do not change production external snapshot or external project planning scripts.
- Do not modify external target repositories.
- Do not broaden fixture text beyond current test needs.

## Codex Thread

- thread/session id: local Codex desktop session; no target-project Codex session executed
- target project writes: none

## Changed Files

- `STATE.md`
- `CAMPAIGN_STATE.md`
- `ERROR_LOG.md`
- `tests/external_validation_test_utils.py`
- `tests/test_external_candidate_snapshot.py`
- `tests/test_plan_external_project.py`
- `runs/selfdex/20260430-141130-external-project-registry-fixtures-dedup.md`

## Verification

- `python -m unittest tests.test_external_candidate_snapshot tests.test_plan_external_project`
  - result: passed after one fixture literal repair
  - detail: ran 12 tests after sandbox escalation
- `python scripts/collect_repo_metrics.py --root . --paths tests\test_external_candidate_snapshot.py tests\test_plan_external_project.py --pretty --min-duplicate-lines 10`
  - result: passed
  - detail: `group_count=0`, `duplicated_line_instances=0`
- `python -m compileall -q scripts tests`
  - result: passed
- `python scripts/plan_next_task.py --root . --format json`
  - result: passed
  - detail: `candidate_count=0`, `selected=null`
- `python scripts/check_doc_drift.py --root . --format json`
  - result: passed
  - detail: `finding_count=0`
- `git diff --check`
  - result: passed
  - detail: exit 0 with LF-to-CRLF working-copy warnings
- `python -m unittest discover -s tests`
  - result: passed after sandbox escalation
  - detail: ran 170 tests

## Repair Attempts

- `1`: replaced one unstable non-ASCII project-name fixture in `tests/test_plan_external_project.py` with an ASCII slug fixture; dedicated slug behavior remains covered elsewhere.

## Failure Or Stop Reason

- none
