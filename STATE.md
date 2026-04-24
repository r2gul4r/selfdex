# STATE

## Current Task

- task: `clean_markdown_value 중복 정리`
- phase: `closeout`
- scope: `shared markdown helper for campaign/state markdown parsing without behavior change`
- verification_target: `compileall scripts and tests, unittest discover, doc drift, planner json/markdown, budget checker json, git diff --check`

## Orchestration Profile

- score_total: `5`
- score_breakdown:
  - `multi_file_duplicate_reduction`: 1
  - `shared_markdown_parser`: 1
  - `planner_contract_risk`: 1
  - `budget_checker_contract_risk`: 1
  - `focused_test_update`: 1
  - `verification_required`: 1
- hard_triggers:
  - `none`
- selected_rules:
  - `narrow_refactor`
  - `preserve_campaign_queue_parsing`
  - `preserve_budget_checker_parsing`
  - `preserve_doc_drift`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `small duplicated markdown helpers across two scripts; shared helper plus tests is one tightly coupled write set`
- spawn_decision: `do_not_spawn; cross-file duplicate cleanup is small and easier to integrate locally`
- selection_reason: `Planner selected clean_markdown_value duplicate cleanup with priority_score=51.75 after commit a44fed9.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `clean_markdown_value is implemented once in a shared helper.`
  - `plan_next_task.py and check_campaign_budget.py use the shared helper.`
  - `Focused tests cover markdown value cleaning and section extraction.`
  - `README documents the new helper so doc drift stays clean.`
  - `Planner and budget checker outputs remain compatible.`
- non_goals:
  - `Do not edit codex_multiagent.`
  - `Do not touch installers or global Codex config.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
  - `Do not scan or write other projects in this task.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/markdown_utils.py --changed-path scripts/plan_next_task.py --changed-path scripts/check_campaign_budget.py --changed-path tests/test_markdown_utils.py --changed-path README.md --changed-path STATE.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether shared helper return types match both existing call sites.`
  - `Check whether the helper avoids coupling planner and budget checker behavior to unrelated code.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `shared markdown helper refactor`
- write_sets:
  - `main`:
    - `scripts/markdown_utils.py`
    - `scripts/plan_next_task.py`
    - `scripts/check_campaign_budget.py`
    - `tests/test_markdown_utils.py`
    - `README.md`
    - `runs/20260424-142451-shared-markdown-helper.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Refactor only shared markdown parsing helpers.
- Add focused tests for markdown value cleaning and section extraction.
- Preserve planner and budget checker output schemas.
- Do not split files or introduce new dependencies.
- Record the completed run under `runs/` and update the latest campaign run summary.
- Do not touch installers, global Codex config, codex_multiagent, secrets, deploys, paid APIs, or DB files.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual markdown helper call-site compatibility review`

## Last Update

- timestamp: `2026-04-24T14:25:15+09:00`
- phase: `closeout`
- status: `shared markdown helper refactor completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 33 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/markdown_utils.py --changed-path scripts/plan_next_task.py --changed-path scripts/check_campaign_budget.py --changed-path tests/test_markdown_utils.py --changed-path README.md --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=parse_args 중복 정리`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed with LF-to-CRLF warnings for scripts/check_campaign_budget.py and scripts/plan_next_task.py`
- note: `This task starts after commit a44fed9.`

## Retrospective

- task: `shared markdown helper refactor`
- score_total: `5`
- evaluation_fit: `good; helper tests, doc drift, planner, and budget checker all pass`
- orchestration_fit: `good; single-session matched small cross-file helper cleanup`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Next candidate is parse_args 중복 정리.`
