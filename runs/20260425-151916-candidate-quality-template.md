# Run 20260425-151916-candidate-quality-template

- goal: Add a manual candidate quality scoring template generator
- selected_candidate: planner-to-quality-template CLI
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Added `scripts/prepare_candidate_quality_template.py`, focused tests, and README documentation so planner candidates can become human-fillable rubric payloads before evaluator/report generation.
- next_candidate: document the full read-only validation workflow or add a wrapper that chains planner output, template, evaluator, and report generation from explicit files

## Write Sets

- scripts/prepare_candidate_quality_template.py
- tests/test_candidate_quality_template.py
- README.md
- CAMPAIGN_STATE.md
- STATE.md
- ERROR_LOG.md
- runs/20260425-151916-candidate-quality-template.md

## Verification

- `python` was not available on PATH; verification used bundled Python at `C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests -p test_candidate_quality_template.py`: passed; ran 3 tests.
- `python scripts/prepare_candidate_quality_template.py --planner examples/external_validation_planner_sample.json --format json`: passed.
- `python scripts/prepare_candidate_quality_template.py --planner examples/external_validation_planner_sample.json --format markdown`: passed.
- `python -m unittest discover -s tests`: passed after rerun outside sandbox because the suite writes temporary fixture directories; ran 74 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed; selected `parse_args 중복 정리` next.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed.
- `ERROR_LOG.md`: updated with the resolved sandbox Temp write limitation for full-suite verification.
