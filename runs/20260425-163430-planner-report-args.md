# Run Record: planner-report-args

- timestamp: `2026-04-25T16:45:00+09:00`
- task: `deduplicate planner report parse args`
- score_total: `5`
- selected_profile: `autopilot-single`
- actual_topology: `autopilot-single`
- agent_budget: `0`
- spawn_decision: `do_not_spawn; handoff cost exceeds parallel gain`

## Contract

- Move shared planner report argument wiring into `scripts/argparse_utils.py`.
- Move shared planner JSON loading and planner candidate extraction into a helper.
- Preserve external validation and candidate quality template CLI flags, defaults, output payloads, and exit behavior.
- Keep the work local to report CLI helper dedupe.

## Changes

- Added `scripts/planner_payload_utils.py` for shared `load_json` and `planner_candidates`.
- Updated `scripts/build_external_validation_report.py` and `scripts/prepare_candidate_quality_template.py` to use shared argument and payload helpers.
- Added focused tests for planner payload helper behavior.
- Documented the new helper in `README.md`.

## Verification

- `python -m compileall -q scripts tests` passed.
- `python -m unittest discover -s tests -p test_argparse_utils.py` passed.
- `python -m unittest discover -s tests -p test_planner_payload_utils.py` failed in sandbox due Temp write permissions, then passed after approved escalation.
- `python -m unittest discover -s tests -p test_candidate_quality_template.py` passed.
- `python -m unittest discover -s tests -p test_external_validation_report.py` failed in sandbox due Temp write permissions, then passed after approved escalation.
- `python scripts/build_external_validation_report.py --root . --planner examples/external_validation_planner_sample.json --format json` passed.
- `python scripts/build_external_validation_report.py --root . --planner examples/external_validation_planner_sample.json --format markdown` passed.
- `python scripts/prepare_candidate_quality_template.py --planner examples/external_validation_planner_sample.json --format json` passed.
- `python scripts/prepare_candidate_quality_template.py --planner examples/external_validation_planner_sample.json --format markdown` passed.
- `python -m unittest discover -s tests` failed in sandbox due Temp/root fixture write permissions, then passed after approved escalation with 109 tests.
- `python scripts/extract_refactor_candidates.py --root . --format json` passed; `parse_args` duplicate candidate no longer appears.
- `python scripts/plan_next_task.py --root . --format json` passed and selected the next feature-gap false-positive candidate.
- `python scripts/plan_next_task.py --root . --format markdown` passed.
- `python scripts/check_campaign_budget.py --root . --format json` passed.
- `python scripts/check_doc_drift.py --root . --format json` passed.
- `git diff --check` passed with LF-to-CRLF warnings only.

## Outcome

- The report CLI duplicate candidate was removed from the planner's top selection.
- The next planner candidate is now a feature-gap false positive around test helper names.

## Next Recommended Task

- Suppress feature-gap candidates that originate from test function/helper names rather than production feature gaps.
