# STATE

## Current Task

- task: `Bootstrap the empty selfdex repository as an aggressive autonomous Codex harness.`
- phase: `implementation`
- scope: `initial scaffold, imported analysis scripts, autopilot policy, campaign state`
- verification_target: `python compile, planner smoke, git diff --check`

## Orchestration Profile

- score_total: `6`
- score_breakdown:
  - `new_repository_bootstrap`: 1
  - `multi_file_scaffold`: 1
  - `policy_surface`: 1
  - `script_import`: 1
  - `verification_required`: 1
  - `future_delegation_contract`: 1
- hard_triggers:
  - `policy_and_authority_wording`
- selected_rules:
  - `aggressive_autopilot_scaffold`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low_for_this_bootstrap`
- agent_budget: `0`
- spawn_decision: `do_not_spawn; current host policy requires explicit subagent request and bootstrap write sets are tightly coupled`
- selection_reason: `Initial scaffold touches policy and repository shape, but all writes are one coherent bootstrap slice.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `Repository has AGENTS.md, AUTOPILOT.md, CAMPAIGN_STATE.md, STATE.md, README.md, scripts, docs, profiles, and runs scaffold.`
  - `Next-task planner can produce markdown and JSON.`
  - `Core Python scripts compile.`
- non_goals:
  - `Do not import conservative global installer behavior.`
  - `Do not create a deployment path.`
  - `Do not grant destructive or credential authority.`
- hard_checks:
  - `python -m compileall -q scripts`
  - `python scripts/plan_next_task.py --root . --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether the policy is meaningfully more aggressive while preserving hard approval gates.`
  - `Check whether imported assets are useful without dragging in installer-specific scope.`
- evidence_required:
  - `verification command output`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `initial repository scaffold`
- write_sets:
  - `main`:
    - `AGENTS.md`
    - `AUTOPILOT.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
    - `README.md`
    - `scripts/**`
    - `docs/**`
    - `profiles/**`
    - `examples/**`
    - `runs/**`
- shared_assets_owner: `main`

## Contract Freeze

- Keep selfdex as an aggressive autonomous harness, not a conservative installer kit.
- Import analysis assets from codex_multiagent only when they support scanning, ranking, planning, or verification.
- Keep hard approval zones explicit.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual policy and scaffold review`

## Last Update

- timestamp: `2026-04-24T00:00:00+09:00`
- phase: `closeout`
- status: `Initial aggressive autopilot scaffold created.`
- verification_result:
  - `python -m compileall -q scripts`: `passed`
  - `python scripts/plan_next_task.py --root . --format json`: `passed`
  - `python scripts/plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed`
- note: `PowerShell wildcard py_compile was replaced with compileall for cross-shell verification.`
