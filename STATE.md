# STATE

## Current Task

- task: `selfdex durable handoff memory`
- phase: `closeout`
- scope: `write a repo-local handoff note that summarizes current Selfdex goal, rules, commits, verification, and next task for use on another machine`
- verification_target: `doc drift check, campaign budget check, git diff --check`

## Orchestration Profile

- score_total: `4`
- score_breakdown:
  - `handoff_documentation`: 1
  - `cross_machine_continuity`: 1
  - `state_and_readme_update`: 1
  - `commit_required`: 1
- hard_triggers:
  - `none`
- selected_rules:
  - `repo_local_memory_only`
  - `do_not_edit_global_memory_folder`
  - `no_global_config_edit`
  - `no_installers`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `single documentation artifact plus README/STATE update; no parallel slice exists`
- spawn_decision: `do_not_spawn; write and verify locally`
- selection_reason: `User asked to save the conversation memory. System memory is read-only here, so store a repo-local handoff note that travels with the repository.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Do not update Codex memory files directly.`
  - `Do not edit global Codex config or installers.`
  - `Only C:\lsh\git\selfdex may be modified.`
- task_acceptance:
  - `Add a concise handoff document under docs/.`
  - `Document final goal, safety rules, latest commits, verification baseline, next planner candidate, and subagent lesson.`
  - `Link the handoff document from README core files.`
  - `Commit the result.`
- non_goals:
  - `Do not change planner behavior.`
  - `Do not modify scripts or tests.`
  - `Do not push unless separately requested.`
- hard_checks:
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path docs/SELFDEX_HANDOFF.md --changed-path README.md --changed-path STATE.md --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether the note is specific enough for another machine to resume.`
  - `Check whether it avoids implying direct access to private memory storage.`
- evidence_required:
  - `doc drift result`
  - `campaign budget result`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `handoff documentation`
- write_sets:
  - `main`:
    - `docs/SELFDEX_HANDOFF.md`
    - `README.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Store handoff memory in `docs/SELFDEX_HANDOFF.md`.
- Keep it concise and actionable.
- Do not edit external memory folders or global Codex config.
- Commit the change after verification.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual handoff clarity review`

## Last Update

- timestamp: `2026-04-24T18:03:00+09:00`
- phase: `closeout`
- status: `repo-local handoff memory saved.`
- verification_result:
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path docs/SELFDEX_HANDOFF.md --changed-path README.md --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `git diff --check`: `passed`

## Retrospective

- task: `selfdex durable handoff memory`
- score_total: `4`
- evaluation_fit: `good; concise handoff covers goal, rules, commits, verification, next task, and subagent lesson`
- orchestration_fit: `good; documentation-only local write set`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `none`
- verification_outcome: `passed`
- next_gate_adjustment: `Use docs/SELFDEX_HANDOFF.md as cross-machine continuity context.`
