# STATE

## Current Task

- task: `plan selected external project read-only`
- phase: `verified`
- scope: `add a safe command that scans one selected external project read-only and emits a Codex-ready task contract without writing the target project`
- verification_target: `external project planning tests, planner smoke, campaign budget, doc drift, git diff --check`

## Orchestration Profile

- score_total: `6`
- score_breakdown:
  - `external_project_boundary`: 2
  - `new_cli_contract_artifact`: 2
  - `verification_required`: 1
  - `product_direction_recenter`: 1
- hard_triggers:
  - `external_project_boundary`
- selected_rules:
  - `read_only_external_planning`
  - `no_external_writes`
  - `codex_execution_prompt_required`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `medium`
- agent_budget: `0`
- efficiency_basis: `single new planning command plus docs/tests is tightly coupled; no disjoint write set worth spawning`
- spawn_decision: `no_spawn_user_requested_continuation_but_developer_policy_requires_explicit_subagent_request`
- selection_reason: `User clarified Selfdex must become a supervised automatic developer control plane, starting with read-only planning for a selected external project before any write-enabled execution.`

## Evaluation Plan

- evaluation_need: `high`
- project_invariants:
  - `Do not write external repositories.`
  - `Do not implement automatic external writes yet.`
  - `Do not claim Selfdex is already a fully autonomous developer.`
  - `Do not add external dependencies.`
  - `Do not perform destructive Git operations.`
  - `Do not commit unless separately requested.`
  - `Preserve hard approval gates for secrets, deploys, paid calls, database/prod writes, destructive actions, and cross-workspace writes.`
- task_acceptance:
  - `A command can plan one registered project by project id or one ad-hoc project path read-only.`
  - `The output includes selected candidate, rationale, write boundaries, likely inspect/modify files, verification commands, risk, approval requirement, and Codex execution prompt.`
  - `The command can write an optional planning artifact under runs/ without writing the external project.`
  - `README and final-goal docs explain the path from read-only planning to isolated worktree patching and supervised PR-ready modification.`
  - `Run record and campaign latest run are updated.`
- non_goals:
  - `Do not modify any external project.`
  - `Do not create branches or worktrees in external projects.`
  - `Do not execute generated Codex prompts.`
  - `Do not auto-score candidates as human-approved.`
  - `Do not change PROJECT_REGISTRY.md format.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `python scripts/plan_next_task.py --root . --format json`
  - `python scripts/plan_next_task.py --root . --format markdown`
  - `python scripts/check_campaign_budget.py --root . --format json`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check the planning command never writes target project files.`
  - `Check execution prompt is usable but still requires human approval before external writes.`
  - `Check docs preserve bounded, auditable framing while pointing toward supervised modification.`
- evidence_required:
  - `focused external planning test result`
  - `registry project planning smoke result`
  - `ad-hoc project path planning smoke result`
  - `full repository verification result`
  - `run record path`

## Writer Slot

- writer_slot: `main`
- write_set: `external project planning command`
- write_sets:
  - `main`:
    - `STATE.md`
    - `CAMPAIGN_STATE.md`
    - `README.md`
    - `docs/SELFDEX_FINAL_GOAL.md`
    - `scripts/plan_external_project.py`
    - `tests/test_plan_external_project.py`
    - `runs/20260425-201500-external-project-plan-apex-analist.md`
- shared_assets_owner: `main`

## Contract Freeze

- Add a read-only planning CLI for a single selected external project.
- Reuse existing external candidate snapshot scanning where possible.
- Generate a task contract artifact and Codex execution prompt.
- Keep external project modification out of scope.
- Use bundled Python if `python` is not on PATH.

## Reviewer

- reviewer: `not_selected`
- reviewer_target: `none`
- reviewer_focus: `local tests and explicit read-only boundary cover this first planning step`
- reviewer_result: `not run`

## Last Update

- timestamp: `2026-04-25T20:15:00+09:00`
- phase: `verified`
- status: `read-only external project planning command implemented and verified.`
- verification_result:
  - `python -m unittest discover -s tests -p test_plan_external_project.py`: `passed after sandbox escalation; ran 4 tests`
  - `python scripts/plan_external_project.py --root . --project-id apex_analist --format json`: `passed; status=ready, external_project_writes_performed=false`
  - `python scripts/plan_external_project.py --root . --project-root ..\apex_analist --project-name apex_analist --format markdown`: `passed; status=ready`
  - `python scripts/plan_external_project.py --root . --project-id apex_analist --record-run --timestamp 20260425-201500 --format markdown`: `passed; wrote runs/20260425-201500-external-project-plan-apex-analist.md`
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed after sandbox escalation; ran 139 tests`
  - `python scripts/plan_next_task.py --root . --format json`: `passed`
  - `python scripts/plan_next_task.py --root . --format markdown`: `passed`
  - `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
  - `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
  - `git diff --check`: `passed; exit 0 with LF-to-CRLF working-copy warnings`

## Retrospective

- task: `plan selected external project read-only`
- score_total: `6`
- selected_profile: `autopilot-single`
- actual_topology: `autopilot-single`
- verification_outcome: `passed`
- collisions_or_reclassifications: `reclassified because user clarified the target product is a supervised developer control plane for selected projects`
- next_rule_change: `consider write-enabled target project contract after read-only planning is verified`
