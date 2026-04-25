# Run Record: Shared External Scan Excludes

- time: `2026-04-25T18:31:00+09:00`
- task: `add shared external scan excludes`
- score_total: `5`
- topology: `autopilot-single`
- agent_budget: `0`

## Contract

- Add shared generated/dependency/cache directory exclusions before external read-only snapshots.
- Reuse the shared exclusions in metrics, test-gap, feature-gap, and refactor filtering helpers.
- Do not scan or write external repositories in this step.
- Do not claim external value is proven.

## Changes

- Added `scripts/repo_scan_excludes.py` with common scan exclusions for `.git`, `.codex`, Python caches, virtualenvs, JS dependency folders, coverage, and build outputs.
- Wired `scripts/collect_repo_metrics.py`, `scripts/extract_test_gap_candidates.py`, `scripts/feature_file_records.py`, and `scripts/refactor_metrics_payload.py` to use the shared exclusion set.
- Kept `runs/` as an extra refactor-candidate filter so audit records stay out of internal refactor candidates.
- Added focused tests covering shared exclusions, metrics scan filtering, test-gap filtering, feature file-record filtering, and refactor metric filtering.
- Documented the helper in `README.md`.

## Repairs

- `python -m unittest discover -s tests` initially exposed a spec-loader import regression in `tests/test_selfdex_loop_integration.py`.
- Added script-directory import path setup to touched scanner helpers so file-path loaded wrappers can resolve `repo_scan_excludes.py`.

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_repo_scan_excludes.py`: `passed after sandbox escalation; ran 4 tests`
- `python -m unittest discover -s tests -p test_feature_file_records.py`: `passed after sandbox escalation; ran 3 tests`
- `python -m unittest discover -s tests -p test_refactor_metrics_payload.py`: `passed; ran 3 tests`
- `python -m unittest discover -s tests -p test_selfdex_loop_integration.py`: `passed after import-path repair and sandbox escalation; ran 2 tests`
- `python -m unittest discover -s tests`: `passed after sandbox escalation; ran 126 tests`
- `python scripts/plan_next_task.py --root . --format json`: `passed; candidate_count=0, errors=[]`
- `python scripts/plan_next_task.py --root . --format markdown`: `passed; selected none`
- `python scripts/check_external_validation_readiness.py --root . --format json`: `passed; status=ready, external_project_count=3`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- External read-only snapshots can now skip common dependency and generated-output directories by default.
- The next safe task is generating read-only candidate snapshots for the registered external projects, then scoring the top candidates with the candidate quality rubric.
