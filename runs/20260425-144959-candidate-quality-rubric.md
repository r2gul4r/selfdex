# Run 20260425-144959-candidate-quality-rubric

- goal: Add a candidate quality rubric for supervised external validation
- selected_candidate: documentation-only rubric for candidate usefulness scoring
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Added `docs/CANDIDATE_QUALITY_RUBRIC.md` and linked it from README and the final-goal roadmap so planner candidates can be judged by human-useful quality before planner behavior changes.
- next_candidate: design a read-only external validation report format or add a small rubric evaluator script

## Write Sets

- docs/CANDIDATE_QUALITY_RUBRIC.md
- README.md
- docs/SELFDEX_FINAL_GOAL.md
- CAMPAIGN_STATE.md
- ERROR_LOG.md
- STATE.md
- runs/20260425-144959-candidate-quality-rubric.md

## Verification

- `python` was not available on PATH; verification used bundled Python at `C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests`: passed after rerun outside sandbox because the suite writes temporary fixture directories.
- `python scripts/plan_next_task.py --root . --format json`: passed.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed.
- `ERROR_LOG.md`: updated with the resolved sandbox Temp write limitation.
