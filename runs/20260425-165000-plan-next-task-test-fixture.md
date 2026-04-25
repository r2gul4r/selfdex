# Run Record: plan-next-task-test-fixture

- timestamp: `2026-04-25T16:52:33+09:00`
- task: `deduplicate plan_next_task imported refactor test fixture`
- score_total: `4`
- selected_profile: `autopilot-single`
- actual_topology: `autopilot-single`
- agent_budget: `0`
- spawn_decision: `do_not_spawn; handoff cost exceeds parallel gain`

## Contract

- Replace duplicated inline imported-refactor payload setup in `tests/test_plan_next_task.py`.
- Preserve planner runtime behavior and all assertions.
- Keep the refactor limited to a single test helper.

## Changes

- Added `imported_refactor_payload()` in `tests/test_plan_next_task.py`.
- Replaced the two duplicated inline refactor payload blocks selected by the planner.

## Verification

- `python -m compileall -q scripts tests` passed.
- `python -m unittest discover -s tests -p test_plan_next_task.py` failed in sandbox due Temp writes, then passed after approved escalation with 11 tests.
- `python scripts/extract_refactor_candidates.py --root . --format json` passed; the selected plan_next_task duplicate candidate disappeared.
- `python scripts/plan_next_task.py --root . --format json` passed and selected the next test fixture duplicate candidate.
- `python scripts/plan_next_task.py --root . --format markdown` passed.
- `python -m unittest discover -s tests` failed in sandbox due Temp/root fixture write permissions, then passed after approved escalation with 110 tests.
- `python scripts/check_campaign_budget.py --root . --format json` passed.
- `python scripts/check_doc_drift.py --root . --format json` passed.
- `git diff --check` passed with LF-to-CRLF warnings only.

## Outcome

- The duplicated imported-refactor fixture setup is now a single helper.
- Planner moved to the next duplicated fixture candidate in `tests/test_candidate_extractors.py`.

## Next Recommended Task

- Deduplicate repeated metrics fixture payload setup in `tests/test_candidate_extractors.py`.
