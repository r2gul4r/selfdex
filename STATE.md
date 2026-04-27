# STATE

## Current Task

- task: `repair Windows subprocess smoke UTF-8 handling after home update`
- phase: `verified`
- scope: `make subprocess-based script/module smoke tests inherit a stable UTF-8 stdout encoding on Windows`
- verification_target: `focused extractor smoke test, full unittest suite, planner smoke, doc drift, git diff --check`

## Orchestration Profile

- score_total: `3`
- score_breakdown:
  - `windows_verification_regression`: 2
  - `single_helper_test_surface`: 1
- hard_triggers:
  - `none`
- selected_rules:
  - `verification_required`
  - `windows_powershell_compatibility`
  - `single_write_lane`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `single shared test helper controls the failing subprocess smoke path; delegation would add handoff without independent write ownership`
- spawn_decision: `no_spawn_handoff_cost_exceeds_gain`
- selection_reason: `After syncing the home updates, full unittest verification failed because subprocess smoke tests decoded child Python output as UTF-8 while the child process emitted locale-encoded Korean text on Windows.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Do not change external project behavior.`
  - `Do not touch codex_multiagent, global config, installers, secrets, deploys, paid APIs, databases, or production systems.`
  - `Keep the fix inside the failing verification surface.`
  - `Do not use destructive Git or filesystem commands.`
- task_acceptance:
  - `Subprocess script/module smoke helper forces UTF-8 child stdout/stderr encoding.`
  - `Focused extractor smoke test passes on Windows.`
  - `Full unittest suite passes.`
  - `Planner smoke and diff checks remain clean.`
- non_goals:
  - `Do not refactor candidate extraction behavior.`
  - `Do not change planner scoring.`
  - `Do not modify external project registry contents.`
- hard_checks:
  - `python -m unittest discover -s tests -p test_candidate_extractors.py`
  - `python -m unittest discover -s tests`
  - `python -m compileall -q scripts tests`
  - `python scripts/plan_next_task.py --root . --format json`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check the helper fix is limited to subprocess smoke environment setup.`
  - `Check no test hides real command failures.`
- evidence_required:
  - `failing full-suite output before fix`
  - `focused extractor smoke result`
  - `full repository verification result`

## Writer Slot

- writer_slot: `main`
- write_set: `windows subprocess smoke repair`
- write_sets:
  - `main`:
    - `STATE.md`
    - `ERROR_LOG.md`
    - `tests/script_smoke_utils.py`
- shared_assets_owner: `main`

## Contract Freeze

- Add UTF-8 child process environment handling to the shared subprocess smoke helper.
- Preserve direct script and module command coverage.
- Record the verification failure and resolution in `ERROR_LOG.md`.
- Do not alter extractor scoring or output schemas.

## Reviewer

- reviewer: `not_selected`
- reviewer_target: `none`
- reviewer_focus: `focused and full unittest coverage exercise the changed helper`
- reviewer_result: `not run`

## Last Update

- timestamp: `2026-04-27T09:37:20+09:00`
- phase: `verified`
- status: `home updates synced locally; Windows subprocess smoke encoding repair completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed before repair`
  - `python -m unittest discover -s tests`: `failed before repair; subprocess reader hit UnicodeDecodeError while reading extract_refactor_candidates.py output`
  - `python -m unittest discover -s tests -p test_candidate_extractors.py`: `passed after repair; ran 5 tests`
  - `python -m compileall -q scripts tests`: `passed after repair`
  - `python -m unittest discover -s tests`: `passed after repair; ran 139 tests`
  - `python scripts/plan_next_task.py --root . --format json`: `passed before repair; selected tests/test_candidate_quality_template.py 외 1개 경로 중복 정리`
  - `python scripts/plan_next_task.py --root . --format json`: `passed after repair; selected tests/test_candidate_quality_template.py 외 1개 경로 중복 정리`
  - `python scripts/plan_next_task.py --root . --format markdown`: `passed after repair`
  - `python scripts/check_doc_drift.py --root . --format json`: `passed after repair; status=pass`
  - `python scripts/check_campaign_budget.py --root . --changed-path STATE.md --changed-path ERROR_LOG.md --changed-path tests/script_smoke_utils.py --format json`: `passed after repair; status=pass, violation_count=0`
  - `git diff --check`: `passed after repair; exit 0 with LF-to-CRLF working-copy warning for tests/script_smoke_utils.py`

## Retrospective

- task: `repair Windows subprocess smoke UTF-8 handling after home update`
- score_total: `3`
- selected_profile: `autopilot-single`
- actual_topology: `autopilot-single`
- verification_outcome: `passed`
- rework_or_reclassification: `new verification repair task created after syncing home commits`
- reviewer_findings: `not run; focused and full tests covered the changed helper`
- next_gate_adjustment: `keep subprocess smoke helpers responsible for child process encoding when tests parse JSON containing Korean text`
