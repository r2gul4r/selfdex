# Run Record: candidate-extractor-hotspot-fixture

- timestamp: `2026-04-25T16:56:04+09:00`
- task: `deduplicate candidate extractor hotspot metrics fixture`
- score_total: `4`
- selected_profile: `autopilot-single`
- actual_topology: `autopilot-single`
- agent_budget: `0`
- spawn_decision: `do_not_spawn; handoff cost exceeds parallel gain`

## Contract

- Replace duplicated hotspot file and metrics payload setup in `tests/test_candidate_extractors.py`.
- Preserve extractor behavior and assertions.
- Keep the change to a single test fixture helper extraction.

## Changes

- Added `write_hotspot_file()` for the repeated `scripts/hotspot.py` fixture.
- Added `hotspot_metrics_payload()` for the repeated metrics payload.
- Reused those helpers in the hotspot candidate test and script/module metrics-input smoke test.

## Verification

- `python -m compileall -q scripts tests` passed.
- `python -m unittest discover -s tests -p test_candidate_extractors.py` failed in sandbox due Temp writes, then passed after approved escalation with 5 tests.
- `python scripts/extract_refactor_candidates.py --root . --format json` passed; the selected candidate extractor hotspot duplicate candidate disappeared.
- `python scripts/plan_next_task.py --root . --format json` passed and selected the next cross-file subprocess smoke fixture duplicate.
- `python scripts/plan_next_task.py --root . --format markdown` passed.
- `python -m unittest discover -s tests` failed in sandbox due Temp/root fixture write permissions, then passed after approved escalation with 110 tests.
- `python scripts/check_campaign_budget.py --root . --format json` passed.
- `python scripts/check_doc_drift.py --root . --format json` passed.
- `git diff --check` passed with LF-to-CRLF warnings only.

## Outcome

- Hotspot metrics fixture setup now has one source in the candidate extractor tests.
- Planner moved to a cross-file duplicated subprocess smoke pattern between candidate extractor and repo metrics tests.

## Next Recommended Task

- Deduplicate script/module subprocess smoke command setup across the relevant tests.
