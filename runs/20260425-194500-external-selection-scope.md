# Run Record: External Selection Scope

- time: `2026-04-25T19:50:00+09:00`
- task: `make external repo selection explicit`
- score_total: `4`
- topology: `autopilot-single`
- agent_budget: `0`

## Contract

- Keep the default all-read-only-external snapshot behavior.
- Support explicit user-selected subsets with repeated `--project-id`.
- Make selected, requested, and missing project ids auditable in the snapshot payload.
- Fail the CLI when a requested project id is not registered.
- Do not write external repositories.

## Changes

- Added selection metadata to `scripts/build_external_candidate_snapshot.py`.
- Added missing-project-id detection and non-zero CLI exit for invalid selections.
- Added focused tests for selected-only scans, missing ids, and markdown selection output.
- Documented single and repeated `--project-id` examples in `README.md`.

## Evidence

- `--project-id apex_analist` scanned only `apex_analist`.
- `--project-id apex_analist --project-id mqyusimeji` scanned two selected repositories and rendered the selected ids in markdown.
- `--project-id does_not_exist` emitted `missing_project_ids=[does_not_exist]` and failed instead of silently succeeding with an empty snapshot.

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_external_candidate_snapshot.py`: `passed after sandbox escalation; ran 6 tests`
- `python scripts/build_external_candidate_snapshot.py --root . --project-id apex_analist --format json`: `passed`
- `python scripts/build_external_candidate_snapshot.py --root . --project-id apex_analist --project-id mqyusimeji --format markdown`: `passed`
- `python scripts/build_external_candidate_snapshot.py --root . --project-id does_not_exist --format json`: `failed as intended with missing_project_ids`
- `python -m unittest discover -s tests`: `passed after sandbox escalation; ran 135 tests`
- `python scripts/check_external_validation_readiness.py --root . --format json`: `passed; status=ready, external_project_count=3`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- Users can now explicitly choose which registered read-only repositories to scan.
- Selection scope is visible in JSON and markdown evidence, so future validation runs are easier to audit.
