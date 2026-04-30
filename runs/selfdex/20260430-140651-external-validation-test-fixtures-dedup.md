# Run: external validation test fixtures dedup

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: current working tree
- selected candidate: `tests/test_candidate_quality_template.py plus tests/test_external_validation_report.py duplicate cleanup`
- final status: `completed`
- outcome_class: `success`

## Frozen Task Contract

Move duplicated planner candidate and external snapshot payload shapes shared by candidate-quality template and external-validation report tests into a focused test utility.

Acceptance:

- Common planner candidate and external snapshot payload construction is centralized in a small test utility.
- Candidate-quality template tests keep the same candidate counts, source projects, scoring placeholders, and markdown assertions.
- External-validation report tests keep the same quality matching, missing-score, unregistered-project, snapshot, and markdown assertions.
- Duplicate metrics for the selected test paths no longer report the selected duplicate group.
- Planner moves on to a different next candidate.

Non-goals:

- Do not change production external validation scripts.
- Do not generalize unrelated test fixtures.
- Do not touch external target repositories.

## Codex Thread

- thread/session id: local Codex desktop session; no target-project Codex session executed
- target project writes: none

## Changed Files

- `STATE.md`
- `CAMPAIGN_STATE.md`
- `ERROR_LOG.md`
- `tests/external_validation_test_utils.py`
- `tests/test_candidate_quality_template.py`
- `tests/test_external_validation_report.py`
- `runs/selfdex/20260430-140651-external-validation-test-fixtures-dedup.md`

## Verification

- `python -m unittest tests.test_candidate_quality_template tests.test_external_validation_report`
  - result: passed after one import repair and sandbox escalation
  - detail: first run exposed helper import entrypoint mismatch; second sandboxed run hit Windows Temp fixture writes; approved rerun passed 9 tests
- `python scripts/collect_repo_metrics.py --root . --paths tests\test_candidate_quality_template.py tests\test_external_validation_report.py --pretty --min-duplicate-lines 10`
  - result: passed
  - detail: `group_count=0`, `duplicated_line_instances=0`
- `python -m compileall -q scripts tests`
  - result: passed
- `python scripts/plan_next_task.py --root . --format json`
  - result: passed
  - detail: next selected candidate changed to `write_multi_registry + write_registry` duplicate cleanup
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

- `1`: added import fallback for the shared test utility so both module-name and discover-style unittest entrypoints work.

## Failure Or Stop Reason

- none
