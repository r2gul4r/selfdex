# Run Record: feature-gap-test-source-filter

- timestamp: `2026-04-25T16:49:04+09:00`
- task: `suppress test-sourced feature gap candidates`
- score_total: `5`
- selected_profile: `autopilot-single`
- actual_topology: `autopilot-single`
- agent_budget: `0`
- spawn_decision: `do_not_spawn; handoff cost exceeds parallel gain`

## Contract

- Stop feature-gap candidate generation from treating test files as production feature gaps.
- Keep test records available for evidence and missing-test checks.
- Preserve payload schema and direct script/module execution compatibility.

## Changes

- Updated `scripts/extract_feature_gap_candidates.py` so `scan_file` returns no candidates for records marked as test files.
- Added focused coverage in `tests/test_feature_gap_evidence.py` proving test files are skipped as candidate sources.

## Verification

- `python -m compileall -q scripts tests` passed.
- `python -m unittest discover -s tests -p test_feature_gap_evidence.py` passed with 6 tests.
- `python scripts/extract_feature_gap_candidates.py --root . --format json` passed; test-sourced feature-gap candidates dropped from 10 candidates to 5 production-tooling candidates.
- `python scripts/extract_feature_gap_candidates.py --root . --format markdown` passed.
- `python scripts/plan_next_task.py --root . --format json` passed; planner advanced past the `test_feature_*` feature-gap false positives.
- `python scripts/plan_next_task.py --root . --format markdown` passed.
- `python -m unittest discover -s tests` failed in sandbox due Temp/root fixture write permissions, then passed after approved escalation with 110 tests.
- `python scripts/check_campaign_budget.py --root . --format json` passed.
- `python scripts/check_doc_drift.py --root . --format json` passed.
- `git diff --check` passed with LF-to-CRLF warnings only.

## Outcome

- Tests are still scanned as evidence, but no longer become feature-gap implementation candidates.
- The next planner-selected task is now a test refactor duplicate in `tests/test_plan_next_task.py`.

## Next Recommended Task

- Deduplicate repeated campaign queue fixture setup in `tests/test_plan_next_task.py`.
