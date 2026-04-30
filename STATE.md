# STATE

## Current Task

- task: `implement target Codex orchestrator with project-scoped run records`
- phase: `verified`
- scope: `add a Selfdex command that plans one target-project candidate, creates an isolated branch, runs target Codex through an app-server adapter, and stores results under runs/<project_key>/`
- verification_target: `focused orchestrator, plan artifact, record-run, campaign-budget tests plus full repository checks`

## Orchestration Profile

- score_total: `8`
- score_breakdown:
  - `cross_project_execution_path`: 2
  - `branch_creation_and_git_state`: 2
  - `codex_app_server_adapter`: 2
  - `project_scoped_run_records`: 1
  - `campaign_budget_policy_change`: 1
- hard_triggers:
  - `external_source_dependency`
  - `cross_workspace_write_path`
  - `workflow_policy_change`
  - `automation_execution_surface`
- selected_rules:
  - `state_before_writes`
  - `single_write_lane`
  - `target_branch_isolation`
  - `project_scoped_runs`
  - `verification_required`
- selected_skills:
  - `selfdex-autopilot`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `The implementation touches one tightly coupled orchestration path and host policy does not grant subagent authorization for this turn.`
- spawn_decision: `no_spawn_host_policy_and_coupled_write_surface`
- selection_reason: `The user approved implementing Selfdex as the central controller that automatically executes one target-project Codex task at a time and records results in per-project run folders.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Do not modify external project files during this implementation.`
  - `Do not run target Codex automation during tests; use fake adapters.`
  - `Do not touch secrets, deploys, paid APIs, databases, production systems, installers, or global Codex config.`
  - `Preserve existing GPT-5.5 prompt and repo skill changes already in the working tree.`
  - `Target project writes must be isolated to a new branch when execution is enabled.`
- task_acceptance:
  - `Target orchestration command can build a one-candidate plan and record a blocked, dry-run, or completed result.`
  - `Project run artifacts are written under runs/<project_key>/<timestamp>-<task-slug>.md.`
  - `Registered project_id wins for project key; ad-hoc project_name is next; folder name is fallback.`
  - `Project keys are path-safe slugs, including spaces, symbols, and Korean input.`
  - `Different projects produce separate run directories.`
  - `Campaign budget check allows normal runs/<project_key>/ artifacts without false hard-approval failures.`
- non_goals:
  - `Do not make Codex SDK/app-server work around this machine's WindowsApps codex.exe Access denied issue.`
  - `Do not run real target-project Codex execution as part of implementation verification.`
  - `Do not add multi-candidate loops; keep one candidate per run.`
  - `Do not write run artifacts inside target repositories.`
- hard_checks:
  - `python -m unittest discover -s tests -p test_run_target_codex.py`
  - `python -m unittest discover -s tests -p test_plan_external_project.py`
  - `python -m unittest discover -s tests -p test_record_run.py`
  - `python -m unittest discover -s tests -p test_campaign_budget.py`
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check external writes require explicit execute mode and branch isolation.`
  - `Check run artifacts cannot collide across projects.`
  - `Check app-server adapter failures are recorded as blocked/failed without hiding them.`
- evidence_required:
  - `focused orchestrator tests`
  - `project-scoped artifact tests`
  - `campaign budget acceptance for runs/<project_key>`
  - `full repository verification`

## Writer Slot

- writer_slot: `main`
- write_set: `target codex orchestrator and project-scoped run records`
- write_sets:
  - `main`:
    - `STATE.md`
    - `CAMPAIGN_STATE.md`
    - `README.md`
    - `AUTOPILOT.md`
    - `docs/SELFDEX_FINAL_GOAL.md`
    - `scripts/plan_external_project.py`
    - `scripts/record_run.py`
    - `scripts/run_target_codex.py`
    - `scripts/check_campaign_budget.py`
    - `tests/test_plan_external_project.py`
    - `tests/test_record_run.py`
    - `tests/test_run_target_codex.py`
    - `tests/test_campaign_budget.py`
    - `runs/selfdex/20260430-111200-target-codex-orchestrator.md`
    - `AGENTS.md`
    - `ERROR_LOG.md`
    - `.agents/skills/selfdex-autopilot/SKILL.md`
    - `runs/20260430-104000-gpt55-codex-skill-update.md`
- shared_assets_owner: `main`

## Contract Freeze

- Implement a target Codex orchestrator script that plans one candidate, prepares a branch when execution is enabled, invokes a Codex app-server adapter, captures status, and writes a Selfdex run artifact.
- Keep default behavior non-mutating for target repos unless an explicit execute flag is provided.
- Store all new run artifacts under `runs/<project_key>/`.
- Update existing plan/run record helpers so project-scoped run paths are supported and tested.
- Update campaign/docs to describe folder-wide approval, one-candidate execution, branch isolation, and project-scoped records.
- Preserve previous uncommitted GPT-5.5 prompt and skill-routing changes.

## Reviewer

- reviewer: `not_selected`
- reviewer_target: `none`
- reviewer_focus: `focused tests plus full suite cover the target orchestrator and project-scoped artifact policy`
- reviewer_result: `not run`

## Last Update

- timestamp: `2026-04-30T11:19:17+09:00`
- phase: `verified`
- status: `target Codex orchestration and project-scoped run records implemented.`
- verification_result:
  - `python -m unittest discover -s tests -p test_run_target_codex.py`: `passed; ran 4 tests`
  - `python -m unittest discover -s tests -p test_plan_external_project.py`: `passed; ran 5 tests`
  - `python -m unittest discover -s tests -p test_record_run.py`: `passed; ran 5 tests`
  - `python -m unittest discover -s tests -p test_campaign_budget.py`: `passed; ran 7 tests`
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; ran 147 tests`
  - `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `passed; status=pass, violation_count=0`
  - `git diff --check`: `passed; exit 0 with LF-to-CRLF working-copy warnings for touched Python files`

## Retrospective

- task: `implement target Codex orchestrator with project-scoped run records`
- score_total: `8`
- evaluation_fit: `full checks were useful because the change touched orchestration, recording paths, and campaign-budget policy`
- orchestration_fit: `autopilot-single fit because the write surface was tightly coupled and host policy did not grant subagent spawning`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none after contract freeze`
- reviewer_findings: `not run; focused tests and full suite covered the target orchestrator and recording policy`
- verification_outcome: `passed`
- next_gate_adjustment: `keep real target Codex execution out of unit verification and require fake adapters for app-server tests`
