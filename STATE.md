# STATE

## Current Task

- task: `오케스트레이션 크기/효율/안전 판단 개선`
- phase: `closeout`
- scope: `planner emits task size, collision risk, parallel gain, verification independence, and orchestration value before recommending subagents`
- verification_target: `compileall scripts and tests, unittest discover, planner json/markdown, budget checker json, doc drift, git diff --check`

## Orchestration Profile

- score_total: `8`
- score_breakdown:
  - `planner_policy_change`: 1
  - `orchestration_decision_fields`: 1
  - `task_size_classification`: 1
  - `parallel_gain_collision_model`: 1
  - `safety_gate_semantics`: 1
  - `test_update_required`: 1
  - `documentation_required`: 1
  - `verification_required`: 1
- hard_triggers:
  - `workflow_policy_change`
  - `orchestration_semantics`
- selected_rules:
  - `preserve_campaign_queue_priority`
  - `score_is_not_spawn_decision`
  - `concurrent_state_only_when_write_sets_split`
  - `main_owns_campaign_state_and_runs`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `the change is planner logic plus tests/docs in one coupled write set; a sidecar reviewer would not have an independent write target`
- spawn_decision: `do_not_spawn; implement locally and verify planner behavior with focused tests`
- selection_reason: `User asked to turn the discussion into an improvement plan and implement it. Current planner can rank candidates but cannot strongly distinguish tiny/small/large work for safe multi-agent use.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `score_total and priority_score must not become automatic spawn buttons.`
  - `Concurrent state is a large-task accelerator, not the default path.`
- task_acceptance:
  - `plan_next_task.py emits orchestration_fit fields: task_size_class, estimated_write_set_count, shared_file_collision_risk, handoff_cost, parallel_gain, verification_independence, orchestration_value.`
  - `recommended_topology uses orchestration_fit instead of decision=pick alone.`
  - `tiny/small helper tasks recommend autopilot-single with no spawn.`
  - `large tasks with high collision risk recommend sidecar/mixed, not blind parallel workers.`
  - `large tasks with disjoint write-set signals can recommend concurrent-state parallelization.`
  - `Markdown output shows the fit fields so the decision is auditable.`
  - `A durable doc records the plan, decision model, and safety gates.`
- non_goals:
  - `Do not implement background loops or daemon behavior.`
  - `Do not change installer or global Codex config.`
  - `Do not edit codex_multiagent.`
  - `Do not spawn subagents in this implementation task.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/plan_next_task.py --changed-path tests/test_plan_next_task.py --changed-path docs/ORCHESTRATION_DECISION_PLAN.md --changed-path README.md --changed-path runs/20260424-152019-orchestration-fit-planner.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether score and priority remain ranking inputs, not direct spawn authorization.`
  - `Check whether small tasks are blocked from wasteful concurrent-state overhead.`
  - `Check whether large single-file tasks prefer explorer/reviewer sidecars instead of parallel workers.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate and orchestration_fit`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `planner orchestration fit`
- write_sets:
  - `main`:
    - `scripts/plan_next_task.py`
    - `tests/test_plan_next_task.py`
    - `docs/ORCHESTRATION_DECISION_PLAN.md`
    - `README.md`
    - `runs/20260424-152019-orchestration-fit-planner.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Add orchestration fit fields to planner JSON and Markdown output.
- Preserve candidate ranking, campaign queue priority, and existing collector fallback behavior.
- Make topology recommendation depend on task size, estimated write-set separability, collision risk, handoff cost, parallel gain, and verification independence.
- Document the model as a durable Selfdex plan.
- Do not introduce external dependencies.
- Record the completed run under `runs/` and update the latest campaign run summary.
- Do not touch installers, global Codex config, codex_multiagent, secrets, deploys, paid APIs, or DB files.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual planner topology and safety-gate review`

## Last Update

- timestamp: `2026-04-24T15:20:19+09:00`
- phase: `closeout`
- status: `planner orchestration fit improvement completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 46 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=scripts/plan_next_task.py 책임 분리와 경계 정리; fit=large/high-collision/medium-value`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/plan_next_task.py --changed-path tests/test_plan_next_task.py --changed-path docs/ORCHESTRATION_DECISION_PLAN.md --changed-path README.md --changed-path runs/20260424-152019-orchestration-fit-planner.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `git diff --check`: `passed with LF-to-CRLF warnings for scripts/plan_next_task.py and tests/test_plan_next_task.py`
- note: `This task turns the discussion about efficiency, speed, and safety into planner behavior.`

## Retrospective

- task: `planner orchestration fit improvement`
- score_total: `8`
- evaluation_fit: `good; unit tests cover small single, large high-collision sidecar, and disjoint concurrent-state recommendations`
- orchestration_fit: `good; planner no longer uses decision=pick alone as a spawn trigger`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Next candidate is scripts/plan_next_task.py responsibility split; planner recommends sidecar-first because collision risk is high.`
