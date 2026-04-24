# STATE

## Current Task

- task: `scripts/plan_next_task.py responsibility split`
- phase: `closeout`
- scope: `extract orchestration-fit classification logic from plan_next_task.py into a focused helper module while preserving planner output schema`
- verification_target: `compileall scripts/tests, unittest discover, planner json/markdown, campaign budget, doc drift, git diff --check`

## Orchestration Profile

- score_total: `8`
- score_breakdown:
  - `planner_refactor`: 1
  - `large_file_hotspot`: 1
  - `orchestration_decision_semantics`: 1
  - `new_helper_module`: 1
  - `test_update_required`: 1
  - `state_and_run_record_required`: 1
  - `verification_required`: 1
  - `commit_required`: 1
- hard_triggers:
  - `workflow_policy_touching_planner`
  - `large_single_file_collision_risk`
- selected_rules:
  - `preserve_planner_json_markdown_contract`
  - `preserve_campaign_queue_priority`
  - `preserve_orchestration_fit_fields`
  - `no_global_config_edit`
  - `no_installers`
  - `no_secrets_deploy_paid_api_db`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `medium`
- agent_budget: `0`
- efficiency_basis: `the first safe slice is a tightly coupled extraction from one planner file to one helper module plus tests; write ownership overlaps too much for parallel workers`
- spawn_decision: `do_not_spawn; implement the smallest responsibility split locally and verify output compatibility`
- selection_reason: `Planner selected scripts/plan_next_task.py responsibility split. The lowest-risk useful slice is moving orchestration-fit classification out of the planner while preserving public output.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Selfdex planner must keep campaign queue candidates ahead of imported scan candidates.`
  - `Planner JSON and Markdown output fields must remain compatible.`
  - `Orchestration fit must remain advisory and not become unconditional spawn authorization.`
  - `Only C:\lsh\git\selfdex may be modified.`
- task_acceptance:
  - `Create a focused helper module for orchestration fit classification.`
  - `Keep plan_next_task.py as the CLI/coordinator.`
  - `Keep planner output schema and topology semantics stable.`
  - `Allow the selected next candidate to advance if reducing plan_next_task.py hotspot score changes the scan ranking.`
  - `Add or update tests around the extracted helper behavior.`
  - `Record the run and update campaign state.`
- non_goals:
  - `Do not redesign candidate ranking.`
  - `Do not change campaign queue parsing semantics.`
  - `Do not edit codex_multiagent or any other repository.`
  - `Do not edit global config or installer files.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/plan_next_task.py --changed-path scripts/plan_orchestration_fit.py --changed-path tests/test_plan_orchestration_fit.py --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-164000-plan-orchestration-fit-split.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether the extracted module imports only generic candidate-like protocols instead of planner internals.`
  - `Check whether planner output remains stable.`
  - `Check whether tests cover small, high-collision, and disjoint large fit cases.`
- evidence_required:
  - `verification command output`
  - `planner selected candidate and topology`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `planner orchestration fit extraction`
- write_sets:
  - `main`:
    - `scripts/plan_next_task.py`
    - `scripts/plan_orchestration_fit.py`
    - `tests/test_plan_orchestration_fit.py`
    - `README.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
    - `runs/20260424-164000-plan-orchestration-fit-split.md`
- shared_assets_owner: `main`

## Contract Freeze

- Extract orchestration-fit dataclass and helper functions from `scripts/plan_next_task.py`.
- New helper module may depend on a candidate-like protocol, not on the planner's concrete `Candidate` dataclass.
- Preserve planner JSON and Markdown schema; the selected next candidate may advance because this task intentionally reduces the plan_next_task.py hotspot.
- Do not change command autonomy policy, global config, installers, or external systems.
- Record and commit the change.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual compatibility review`

## Last Update

- timestamp: `2026-04-24T16:52:00+09:00`
- phase: `closeout`
- status: `planner orchestration-fit extraction completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 50 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=scripts/collect_repo_metrics.py responsibility split; topology=autopilot-mixed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/plan_next_task.py --changed-path scripts/plan_orchestration_fit.py --changed-path tests/test_plan_orchestration_fit.py --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-164000-plan-orchestration-fit-split.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `git diff --check`: `passed with LF-to-CRLF warning for scripts/plan_next_task.py`
- note: `The selected next candidate changed because the refactor reduced plan_next_task.py hotspot pressure; this is expected progress, not schema drift.`

## Retrospective

- task: `scripts/plan_next_task.py responsibility split`
- score_total: `8`
- evaluation_fit: `good; focused helper tests cover noop, small duplicate, high-collision hotspot, and disjoint duplicate cases`
- orchestration_fit: `good; single-session fit matched the tightly coupled first extraction slice`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `contract adjusted to allow candidate advancement after hotspot score reduction`
- reviewer_findings: `manual compatibility review only`
- verification_outcome: `passed`
- next_gate_adjustment: `Next planner-selected task is scripts/collect_repo_metrics.py responsibility split.`
