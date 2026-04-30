# Project Direction Intelligence

- goal: add project direction understanding before target candidate planning
- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- selected candidate: user-approved direction shift
- topology: `autopilot-single`
- agent budget used: `0`
- project_key: `selfdex`

## Selected Candidate

- User clarified that Selfdex should not stop at code review, tiny bugfixes, TODO cleanup, or refactor hygiene.
- Selfdex should understand a project's direction, propose better next moves, and convert one strategic opportunity into a bounded executable task.

## Frozen Task Contract

- Add a deterministic project direction snapshot builder.
- Infer purpose, audience, product signals, technical signals, constraints, and strategic opportunities from local repository evidence.
- Feed direction opportunities into external target candidate snapshots before routine hygiene candidates.
- Extend target Codex task contracts with project direction context.
- Keep opportunities small, evidence-backed, locally verifiable, and reversible.

## Changed Files

- `CAMPAIGN_STATE.md`
- `README.md`
- `AUTOPILOT.md`
- `docs/SELFDEX_FINAL_GOAL.md`
- `scripts/build_project_direction.py`
- `scripts/build_external_candidate_snapshot.py`
- `scripts/plan_external_project.py`
- `scripts/planner_text_utils.py`
- `tests/test_build_project_direction.py`
- `tests/test_external_candidate_snapshot.py`
- `tests/test_plan_external_project.py`
- `runs/selfdex/20260430-114700-project-direction-intelligence.md`

## Result

- Added `scripts/build_project_direction.py`.
- Added `project_direction` as an external candidate source.
- Updated target planning prompts to say the task should move the project in a better direction with the smallest safe first step.
- Documented direction-first planning in Selfdex docs.
- final status: `completed`

## Verification

- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests -p test_build_project_direction.py`: passed, ran 3 tests.
- `python -m unittest discover -s tests -p test_external_candidate_snapshot.py`: passed, ran 6 tests.
- `python -m unittest discover -s tests -p test_plan_external_project.py`: passed, ran 5 tests.
- `python -m unittest discover -s tests -p test_planner_text_utils.py`: passed, ran 3 tests.
- `python -m unittest discover -s tests`: passed, ran 150 tests.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed, `violation_count=0`.
- `git diff --check`: passed; PowerShell reported LF-to-CRLF working-copy warnings only.

## Failure Or Stop Reason

- none
