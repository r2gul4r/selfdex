# Run 20260425-152218-validation-cli-argparse-helpers

- goal: Deduplicate validation CLI argument wiring
- selected_candidate: parse_args duplicate cleanup
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Added shared argparse helpers for planner payload, project id, and json/markdown format arguments, then rewired validation report and candidate quality template CLIs without changing their behavior.
- next_candidate: finish the remaining internal refactor hotspot or add a documented end-to-end read-only validation workflow

## Write Sets

- scripts/argparse_utils.py
- scripts/build_external_validation_report.py
- scripts/prepare_candidate_quality_template.py
- tests/test_argparse_utils.py
- CAMPAIGN_STATE.md
- STATE.md
- ERROR_LOG.md
- runs/20260425-152218-validation-cli-argparse-helpers.md

## Verification

- `python` was not available on PATH; verification used bundled Python at `C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests -p test_argparse_utils.py`: passed; ran 4 tests.
- `python -m unittest discover -s tests -p test_external_validation_report.py`: passed after rerun outside sandbox because tests write temporary fixture directories; ran 4 tests.
- `python -m unittest discover -s tests -p test_candidate_quality_template.py`: passed; ran 3 tests.
- `python scripts/build_external_validation_report.py --planner examples/external_validation_planner_sample.json --quality examples/candidate_quality_sample.json --format json`: passed.
- `python scripts/prepare_candidate_quality_template.py --planner examples/external_validation_planner_sample.json --format json`: passed.
- `python -m unittest discover -s tests`: passed after rerun outside sandbox because the suite writes temporary fixture directories; ran 76 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed; selected `scripts/extract_refactor_candidates.py 책임 분리와 경계 정리` next.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings.
- `ERROR_LOG.md`: updated with the resolved sandbox Temp write limitation for full-suite verification.
