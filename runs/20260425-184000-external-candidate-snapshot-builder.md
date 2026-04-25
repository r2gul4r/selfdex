# Run Record: External Candidate Snapshot Builder

- time: `2026-04-25T18:56:00+09:00`
- task: `repair external metric scan binary skips`
- score_total: `5`
- topology: `autopilot-single`
- agent_budget: `0`

## Contract

- Build read-only candidate snapshots for registered external projects.
- Keep external repositories read-only and write snapshot evidence only inside Selfdex.
- Keep `external_value_proven=false` until humans score candidate usefulness.
- Repair bounded scan failures that block external snapshot generation.

## Changes

- Added `scripts/build_external_candidate_snapshot.py`.
- Added `tests/test_external_candidate_snapshot.py`.
- Documented the snapshot builder in `README.md`.
- Updated `scripts/collect_repo_metrics.py` to skip binary/non-UTF-8 files before analysis.
- Extended `tests/test_repo_scan_excludes.py` with a binary asset fixture.

## Evidence

- Initial external snapshot smoke preserved write boundaries but found refactor scanner UTF-8 errors on binary assets in `apex_analist` and `mqyusimeji`.
- After the binary-skip repair, the snapshot smoke returned `project_count=3`, `candidate_count=10`, and `scanner_error_count=0`.
- `mqyubot` scanned cleanly but produced no candidates, which is useful external validation evidence rather than a hidden failure.

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_external_candidate_snapshot.py`: `passed after sandbox escalation; ran 4 tests`
- `python -m unittest discover -s tests -p test_repo_scan_excludes.py`: `passed after sandbox escalation; ran 4 tests`
- `python scripts/build_external_candidate_snapshot.py --root . --format json`: `passed; project_count=3, candidate_count=10, scanner_error_count=0`
- `python scripts/build_external_candidate_snapshot.py --root . --format markdown`: `passed; project_count=3, candidate_count=10, scanner_error_count=0`
- `python -m unittest discover -s tests`: `passed after sandbox escalation; ran 130 tests`
- `python scripts/check_external_validation_readiness.py --root . --format json`: `passed; status=ready, external_project_count=3`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- Selfdex now has a real external read-only snapshot loop.
- The generated candidates are not yet proof of value; the next step is converting snapshot candidates into rubric scoring templates and recording human quality judgments.
