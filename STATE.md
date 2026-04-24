# STATE

## Current Task

- task: `build_duplicate_candidate + build_hotspot_candidate 중복 정리`
- phase: `closeout`
- scope: `share refactor candidate scoring and assembly helpers without output schema changes`
- verification_target: `compileall scripts and tests, unittest discover, refactor extractor smoke checks, planner json/markdown, budget checker json, git diff --check`

## Orchestration Profile

- score_total: `6`
- score_breakdown:
  - `single_file_duplicate_reduction`: 1
  - `refactor_candidate_schema_risk`: 1
  - `shared_scoring_helpers`: 1
  - `focused_test_update`: 1
  - `planner_followup_required`: 1
  - `verification_required`: 1
- hard_triggers:
  - `behavior_schema_preservation`
- selected_rules:
  - `narrow_refactor`
  - `preserve_refactor_candidate_json_schema`
  - `preserve_markdown_report_shape`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `duplicate and hotspot candidate builders share scoring/assembly logic inside one file; write ownership is tightly coupled and tests are one fixture surface`
- spawn_decision: `do_not_spawn; no disjoint write set worth the handoff`
- selection_reason: `Planner selected build_duplicate_candidate + build_hotspot_candidate duplicate cleanup with priority_score=50.6 after commit e365cf4.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `Common refactor scoring flow is extracted from duplicate and hotspot candidate builders.`
  - `Duplicate-block and hotspot candidates keep the same JSON fields and source_signals shape.`
  - `Focused tests cover duplicate and hotspot candidates through fixture metrics.`
  - `Refactor extractor JSON and Markdown smoke checks pass.`
  - `Planner advances or has a clear next candidate after the refactor.`
- non_goals:
  - `Do not edit codex_multiagent.`
  - `Do not touch installers or global Codex config.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
  - `Do not change candidate scoring semantics except shared internal ownership.`
  - `Do not scan or write other projects in this task.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format markdown`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/extract_refactor_candidates.py --changed-path tests/test_candidate_extractors.py --changed-path runs/20260424-145920-refactor-candidate-builder-cleanup.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether common scoring extraction preserves priority_score, priority_grade, decision, and common_axes.`
  - `Check whether duplicate and hotspot source_signals remain candidate-kind specific.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `refactor candidate builder duplicate cleanup`
- write_sets:
  - `main`:
    - `scripts/extract_refactor_candidates.py`
    - `tests/test_candidate_extractors.py`
    - `runs/20260424-145920-refactor-candidate-builder-cleanup.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Extract only shared scoring/assembly helpers inside `scripts/extract_refactor_candidates.py`.
- Preserve refactor extractor CLI flags, JSON schema, Markdown report shape, and candidate ranking semantics.
- Add or update focused fixture tests for duplicate and hotspot candidates.
- Do not introduce new dependencies or new generated-report scripts.
- Record the completed run under `runs/` and update the latest campaign run summary.
- Do not touch installers, global Codex config, codex_multiagent, secrets, deploys, paid APIs, or DB files.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual refactor-candidate schema preservation review`

## Last Update

- timestamp: `2026-04-24T14:59:20+09:00`
- phase: `closeout`
- status: `refactor candidate builder duplicate cleanup completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 43 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format json`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format markdown`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/extract_refactor_candidates.py --changed-path tests/test_candidate_extractors.py --changed-path runs/20260424-145920-refactor-candidate-builder-cleanup.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=extract_markdown_section 중복 정리`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed with LF-to-CRLF warnings for scripts/extract_refactor_candidates.py and tests/test_candidate_extractors.py`
- note: `This task starts after commit e365cf4.`

## Retrospective

- task: `refactor candidate builder duplicate cleanup`
- score_total: `6`
- evaluation_fit: `good; fixture tests, extractor smoke checks, planner, and budget checker all pass`
- orchestration_fit: `good; single-session matched the one-file schema-preserving cleanup`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Next candidate is extract_markdown_section duplicate cleanup.`
