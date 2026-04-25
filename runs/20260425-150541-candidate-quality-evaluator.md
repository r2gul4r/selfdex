# Run 20260425-150541-candidate-quality-evaluator

- goal: Add a local candidate quality evaluator CLI
- selected_candidate: standalone rubric scorer for candidate quality payloads
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Added `scripts/evaluate_candidate_quality.py`, focused evaluator tests, and README/rubric documentation links so candidate quality scores can be checked locally without changing planner ranking behavior.
- next_candidate: wire candidate quality summaries into external read-only validation reports

## Write Sets

- scripts/evaluate_candidate_quality.py
- tests/test_candidate_quality_evaluator.py
- README.md
- docs/CANDIDATE_QUALITY_RUBRIC.md
- CAMPAIGN_STATE.md
- STATE.md
- ERROR_LOG.md
- runs/20260425-150541-candidate-quality-evaluator.md

## Verification

- `python` was not available on PATH; verification used bundled Python at `C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests -p test_candidate_quality_evaluator.py`: passed; ran 8 tests.
- `python scripts/evaluate_candidate_quality.py --format json` with stdin payload: passed; verdict `strong`, total `14`.
- `python scripts/evaluate_candidate_quality.py --format markdown` with stdin payload: passed.
- `python -m unittest discover -s tests`: passed after rerun outside sandbox because the suite writes temporary fixture directories; ran 67 tests.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed.
- `ERROR_LOG.md`: updated with the resolved PowerShell stdin BOM issue and sandbox Temp write limitation.
