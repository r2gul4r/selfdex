# Run Record: Generated Artifact Refactor Filter

- time: `2026-04-25T19:35:00+09:00`
- task: `exclude generated artifacts from refactor candidates`
- score_total: `4`
- topology: `autopilot-single`
- agent_budget: `0`

## Contract

- Filter low-value generated artifacts from refactor candidate snapshots.
- Keep external repositories read-only.
- Preserve normal source/config candidates such as `package.json` and `build.xml`.
- Do not claim external value is proven.

## Changes

- Added common lockfiles such as `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `Cargo.lock`, and `poetry.lock` to refactor metric filtering.
- Added `.codex-backups` to shared scanner directory exclusions.
- Added focused coverage in `tests/test_refactor_metrics_payload.py` and `tests/test_repo_scan_excludes.py`.

## Evidence

- Before the filter, `apex_analist` snapshot ranked `package-lock.json` and backup artifacts as refactor candidates.
- After the filter, `apex_analist` snapshot no longer ranked `package-lock.json` or `.codex-backups` candidates.
- Remaining `apex_analist` candidates are still not proof of usefulness; they need human rubric scoring.

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_repo_scan_excludes.py`: `passed after sandbox escalation; ran 4 tests`
- `python -m unittest discover -s tests -p test_refactor_metrics_payload.py`: `passed; ran 3 tests`
- `python scripts/build_external_candidate_snapshot.py --root . --project-id apex_analist --format json`: `passed; candidate_count=5, scanner_error_count=0`
- `python -m unittest discover -s tests`: `passed after sandbox escalation; ran 133 tests`
- `python scripts/check_external_validation_readiness.py --root . --format json`: `passed; status=ready, external_project_count=3`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- External candidate snapshots are less polluted by generated dependency and backup artifacts.
- The next useful improvement is making user-selected external repo scans explicit and hard to misuse.
