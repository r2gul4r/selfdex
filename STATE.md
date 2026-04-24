# STATE

## Current Task

- task: `parse_args 중복 정리`
- phase: `closeout`
- scope: `shared extractor CLI and area helpers without behavior change`
- verification_target: `compileall scripts and tests, unittest discover, extractor smoke checks, doc drift, planner json/markdown, budget checker json, git diff --check`

## Orchestration Profile

- score_total: `6`
- score_breakdown:
  - `multi_file_duplicate_reduction`: 1
  - `shared_extractor_helpers`: 1
  - `extractor_cli_contract_risk`: 1
  - `remaining_area_classifier_duplicate`: 1
  - `doc_drift_update`: 1
  - `focused_test_update`: 1
  - `verification_required`: 1
- hard_triggers:
  - `none`
- selected_rules:
  - `narrow_refactor`
  - `preserve_extractor_cli_flags`
  - `preserve_extractor_json_markdown_outputs`
  - `preserve_doc_drift`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `small duplicated argparse options and area classifier logic across two extractor scripts; helper, call sites, docs, and tests are one integrated write set`
- spawn_decision: `do_not_spawn; no independent worker/reviewer write set worth the handoff`
- selection_reason: `Planner selected parse_args duplicate cleanup with priority_score=51.75 after commit a35b542; verification showed the same candidate now points at the adjacent classify_area duplicate, so the task was reclassified before further implementation writes.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `Common root, format, and pretty argparse options are provided by a shared helper.`
  - `Common extractor area labels and classify_area logic are provided by a shared helper.`
  - `extract_feature_gap_candidates.py and extract_refactor_candidates.py use the helpers.`
  - `Focused tests cover the shared helper defaults, custom options, and area classification.`
  - `README documents the new helper so doc drift stays clean.`
  - `Extractor JSON/Markdown smoke checks remain compatible.`
- non_goals:
  - `Do not edit codex_multiagent.`
  - `Do not touch installers or global Codex config.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
  - `Do not scan or write other projects in this task.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_feature_gap_candidates.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/argparse_utils.py --changed-path scripts/repo_area_utils.py --changed-path scripts/extract_feature_gap_candidates.py --changed-path scripts/extract_refactor_candidates.py --changed-path tests/test_argparse_utils.py --changed-path tests/test_repo_area_utils.py --changed-path README.md --changed-path runs/20260424-143948-shared-extractor-helpers.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether CLI flags and defaults are unchanged.`
  - `Check whether helper stays generic instead of coupling feature/refactor extractor internals.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `shared extractor helper refactor`
- write_sets:
  - `main`:
    - `scripts/argparse_utils.py`
    - `scripts/repo_area_utils.py`
    - `scripts/extract_feature_gap_candidates.py`
    - `scripts/extract_refactor_candidates.py`
    - `tests/test_argparse_utils.py`
    - `tests/test_repo_area_utils.py`
    - `README.md`
    - `runs/20260424-143948-shared-extractor-helpers.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Refactor only shared extractor CLI and area classification helpers.
- Add focused tests for helper defaults, optional arguments, and area classification.
- Preserve feature/refactor extractor CLI flags, defaults, and output schemas.
- Do not split files or introduce new dependencies.
- Record the completed run under `runs/` and update the latest campaign run summary.
- Do not touch installers, global Codex config, codex_multiagent, secrets, deploys, paid APIs, or DB files.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual extractor helper call-site compatibility review`

## Last Update

- timestamp: `2026-04-24T14:39:48+09:00`
- phase: `closeout`
- status: `shared extractor helper refactor completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 37 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_feature_gap_candidates.py --root . --format json`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format json`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/argparse_utils.py --changed-path scripts/repo_area_utils.py --changed-path scripts/extract_feature_gap_candidates.py --changed-path scripts/extract_refactor_candidates.py --changed-path tests/test_argparse_utils.py --changed-path tests/test_repo_area_utils.py --changed-path README.md --changed-path runs/20260424-143948-shared-extractor-helpers.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=scripts/normalize_quality_signals.py 책임 분리와 경계 정리`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed with LF-to-CRLF warnings for two extractor files`
- note: `This task starts after commit a35b542 and reclassified once when the remaining duplicate was classify_area under the parse_args-selected block.`

## Retrospective

- task: `shared extractor helper refactor`
- score_total: `6`
- evaluation_fit: `good; helper tests, extractor smoke checks, doc drift, planner, and budget checker all pass`
- orchestration_fit: `good; single-session matched the tightly coupled extractor helper cleanup`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `one scope expansion from argparse-only to extractor helper cleanup after the refactor scanner still selected the adjacent classify_area duplicate`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Next candidate is scripts/normalize_quality_signals.py responsibility split.`
