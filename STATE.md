# STATE

## Current Task

- task: `normalize_quality_signals repo metric helper extraction`
- phase: `closeout`
- scope: `narrow refactor in repo metric normalization helpers without schema changes, focused regression test`
- verification_target: `compileall scripts and tests, unittest discover, normalize smoke, planner json/markdown, budget checker json, git diff --check`

## Orchestration Profile

- score_total: `5`
- score_breakdown:
  - `single_file_refactor`: 1
  - `large_normalizer_hotspot`: 1
  - `repo_metric_schema_risk`: 1
  - `helper_extraction`: 1
  - `focused_test_update`: 1
  - `verification_required`: 1
- hard_triggers:
  - `none`
- selected_rules:
  - `narrow_refactor`
  - `preserve_normalized_schema`
  - `preserve_repo_metrics_output`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `one file and one tightly coupled repo-metric normalization path; no independent write sets`
- spawn_decision: `do_not_spawn; helper extraction is local and easier to verify in one lane`
- selection_reason: `Planner selected normalize_quality_signals.py responsibility refactor from scan fallback with priority_score=54.05.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `Repo metric axis normalization is split into smaller helpers.`
  - `Focused test covers normalized repo metric schema and ranking behavior.`
  - `Normalized repo metrics JSON schema remains unchanged.`
  - `Top signal, priority score, grade, and summary behavior stay equivalent.`
  - `No broad rewrite of generic tool-result normalization.`
- non_goals:
  - `Do not edit codex_multiagent.`
  - `Do not touch installers or global Codex config.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
  - `Do not scan or write other projects in this task.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . --pretty | python .\scripts\normalize_quality_signals.py --pretty`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/normalize_quality_signals.py --changed-path tests/test_normalize_quality_signals.py --changed-path STATE.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether helper extraction preserves metric contribution math.`
  - `Check whether output keys and summary shape remain stable.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `normalize quality signals refactor`
- write_sets:
  - `main`:
    - `scripts/normalize_quality_signals.py`
    - `tests/test_normalize_quality_signals.py`
    - `runs/20260424-141655-normalize-quality-signals-refactor.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Refactor only repo metrics normalization helper boundaries.
- Add focused regression coverage for repo metric normalization.
- Preserve field names, data types, priority math, and JSON output shape.
- Do not split files or introduce new dependencies.
- Record the completed run under `runs/` and update the latest campaign run summary.
- Do not touch installers, global Codex config, codex_multiagent, secrets, deploys, paid APIs, or DB files.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual normalize_quality_signals schema-preservation review`

## Last Update

- timestamp: `2026-04-24T14:17:16+09:00`
- phase: `closeout`
- status: `normalize_quality_signals repo metric helper extraction completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 29 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . | python .\scripts\normalize_quality_signals.py | Out-Null`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/normalize_quality_signals.py --changed-path tests/test_normalize_quality_signals.py --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=scripts/normalize_quality_signals.py 책임 분리와 경계 정리`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed with LF-to-CRLF warning for scripts/normalize_quality_signals.py`
- note: `This task starts after commit 682a8af; planner still flags the same file as the next broad hotspot.`

## Retrospective

- task: `normalize_quality_signals helper extraction`
- score_total: `5`
- evaluation_fit: `good; focused test and normalize smoke cover the extracted repo metric helpers`
- orchestration_fit: `good; single-session matched one-file helper extraction`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `expanded scope to add a focused regression test before verification`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Continue splitting normalize_quality_signals.py hotspot if planner keeps selecting it.`
