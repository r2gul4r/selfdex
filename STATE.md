# STATE

## Current Task

- task: `normalize_quality_signals coverage parser helper extraction`
- phase: `closeout`
- scope: `narrow refactor in coverage parsing helpers without schema changes, focused regression test`
- verification_target: `compileall scripts and tests, unittest discover, normalize smoke, planner json/markdown, budget checker json, git diff --check`

## Orchestration Profile

- score_total: `5`
- score_breakdown:
  - `single_file_refactor`: 1
  - `large_normalizer_hotspot`: 1
  - `coverage_parser_schema_risk`: 1
  - `helper_extraction`: 1
  - `focused_test_update`: 1
  - `verification_required`: 1
- hard_triggers:
  - `none`
- selected_rules:
  - `narrow_refactor`
  - `preserve_normalized_schema`
  - `preserve_coverage_output`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `one file and one tightly coupled coverage parsing path; no independent write sets`
- spawn_decision: `do_not_spawn; helper extraction is local and easier to verify in one lane`
- selection_reason: `Planner still selects normalize_quality_signals.py responsibility refactor after commit 606c833; continue with a smaller coverage parser slice.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `Coverage parsing is split into smaller helpers.`
  - `Focused test covers explicit coverage dict and text coverage parsing behavior.`
  - `Normalized repo metrics JSON schema remains unchanged.`
  - `Coverage output keys and summary behavior stay equivalent.`
  - `No broad rewrite of generic tool-result normalization.`
- non_goals:
  - `Do not edit codex_multiagent.`
  - `Do not touch installers or global Codex config.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
  - `Do not scan or write other projects in this task.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . | python .\scripts\normalize_quality_signals.py | Out-Null`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/normalize_quality_signals.py --changed-path tests/test_normalize_quality_signals.py --changed-path STATE.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether helper extraction preserves coverage precedence.`
  - `Check whether explicit coverage, line coverage, total coverage, table coverage, and percent hint outputs remain stable.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `normalize quality signals coverage parser refactor`
- write_sets:
  - `main`:
    - `scripts/normalize_quality_signals.py`
    - `tests/test_normalize_quality_signals.py`
    - `runs/20260424-142036-normalize-coverage-parser.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Refactor only coverage parsing helper boundaries.
- Add focused regression coverage for explicit coverage and text coverage parsing.
- Preserve field names, data types, precedence, and JSON output shape.
- Do not split files or introduce new dependencies.
- Record the completed run under `runs/` and update the latest campaign run summary.
- Do not touch installers, global Codex config, codex_multiagent, secrets, deploys, paid APIs, or DB files.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual normalize_quality_signals coverage parser review`

## Last Update

- timestamp: `2026-04-24T14:21:14+09:00`
- phase: `closeout`
- status: `normalize_quality_signals coverage parser helper extraction completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 31 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . | python .\scripts\normalize_quality_signals.py | Out-Null`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/normalize_quality_signals.py --changed-path tests/test_normalize_quality_signals.py --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=clean_markdown_value 중복 정리`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed with LF-to-CRLF warnings for scripts/normalize_quality_signals.py and tests/test_normalize_quality_signals.py`
- note: `This task starts after commit 606c833.`

## Retrospective

- task: `normalize_quality_signals coverage parser helper extraction`
- score_total: `5`
- evaluation_fit: `good; focused coverage tests and normalize smoke cover the extracted helpers`
- orchestration_fit: `good; single-session matched one-file helper extraction`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Next candidate is clean_markdown_value 중복 정리.`
