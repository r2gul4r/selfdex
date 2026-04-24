# STATE

## Current Task

- task: `scripts/collect_repo_metrics.py responsibility split`
- phase: `closeout`
- scope: `extract file metric dataclasses and line-analysis helpers from collect_repo_metrics.py into a focused helper module`
- verification_target: `compileall scripts/tests, unittest discover, collect metrics smoke, planner json/markdown, campaign budget, doc drift, git diff --check`

## Orchestration Profile

- score_total: `8`
- score_breakdown:
  - `collector_refactor`: 1
  - `large_file_hotspot`: 1
  - `metrics_schema_contract`: 1
  - `new_helper_module`: 1
  - `test_update_required`: 1
  - `state_and_run_record_required`: 1
  - `verification_required`: 1
  - `commit_required`: 1
- hard_triggers:
  - `metrics_schema_contract`
  - `large_single_file_collision_risk`
- selected_rules:
  - `preserve_collect_repo_metrics_json_schema`
  - `preserve_duplicate_and_git_history_behavior`
  - `no_global_config_edit`
  - `no_installers`
  - `no_secrets_deploy_paid_api_db`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `medium`
- agent_budget: `1`
- efficiency_basis: `the first safe slice is coupled extraction of dataclasses and line analysis from one collector file into one helper module; duplicate and git-history behavior remain in the coordinator`
- spawn_decision: `spawn_reviewer_after_patch; use read-only review once write-set collision risk is gone`
- selection_reason: `Planner selected scripts/collect_repo_metrics.py responsibility split. The smallest useful slice is moving file metric models and low-level line analysis out of the collector while preserving output schema.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `collect_repo_metrics.py JSON schema must remain stable.`
  - `duplication group output and git history fields must remain stable.`
  - `Planner output may advance if hotspot score changes after the split.`
  - `Only C:\lsh\git\selfdex may be modified.`
- task_acceptance:
  - `Create a focused helper module for file metric models and line-analysis helpers.`
  - `Keep collect_repo_metrics.py as CLI/coordinator for scanning, duplicate grouping, git history, summary, and payload emission.`
  - `Add focused tests for the extracted helper behavior.`
  - `Update README so generated-report helper coverage stays documented.`
  - `Record the run and update campaign state.`
- non_goals:
  - `Do not redesign duplicate detection.`
  - `Do not redesign git history collection.`
  - `Do not change metric JSON schema.`
  - `Do not edit codex_multiagent or any other repository.`
  - `Do not edit global config or installer files.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . --paths scripts/collect_repo_metrics.py scripts/repo_metrics_utils.py --pretty`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/collect_repo_metrics.py --changed-path scripts/repo_metrics_utils.py --changed-path tests/test_repo_metrics_utils.py --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-171000-collect-metrics-utils-split.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether helper extraction preserves FileMetrics and DuplicateGroup to_dict shapes.`
  - `Check whether collect_repo_metrics.py still owns duplicate grouping and git history coordination.`
  - `Check whether tests cover language inference, comment/code counting, and FileMetrics serialization.`
- evidence_required:
  - `verification command output`
  - `planner selected candidate and topology`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `repo metrics helper extraction`
- write_sets:
  - `main`:
    - `scripts/collect_repo_metrics.py`
    - `scripts/repo_metrics_utils.py`
    - `tests/test_repo_metrics_utils.py`
    - `README.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
    - `runs/20260424-171000-collect-metrics-utils-split.md`
- shared_assets_owner: `main`

## Contract Freeze

- Extract file metrics dataclasses and file/line analysis helpers from `scripts/collect_repo_metrics.py`.
- Preserve collector CLI, payload schema, duplicate grouping, and git history behavior.
- Add focused tests for helper behavior.
- Preserve planner and doc drift behavior.
- Record and commit the change.

## Reviewer

- reviewer: `Boole`
- reviewer_target: `current patch`
- reviewer_focus: `import/package behavior, JSON schema compatibility, duplicate/git history preservation, test gaps`

## Last Update

- timestamp: `2026-04-24T17:42:00+09:00`
- phase: `closeout`
- status: `collect_repo_metrics helper extraction completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 55 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . --paths scripts/collect_repo_metrics.py scripts/repo_metrics_utils.py --pretty`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python -m scripts.collect_repo_metrics --root . --paths scripts\collect_repo_metrics.py scripts\repo_metrics_utils.py --pretty`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=scripts/extract_refactor_candidates.py responsibility split; topology=autopilot-mixed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/collect_repo_metrics.py --changed-path scripts/repo_metrics_utils.py --changed-path tests/test_repo_metrics_utils.py --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-171000-collect-metrics-utils-split.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `git diff --check`: `passed with LF-to-CRLF warning for scripts/collect_repo_metrics.py`
  - `reviewer Boole`: `found import-boundary and test-gap risks; fixed by package-aware imports and direct/module CLI test`
- note: `The selected next candidate changed because this refactor reduced collect_repo_metrics.py hotspot pressure; this is expected progress.`

## Retrospective

- task: `scripts/collect_repo_metrics.py responsibility split`
- score_total: `8`
- evaluation_fit: `good; helper tests cover line analysis and schema shape, CLI tests cover direct and module execution`
- orchestration_fit: `good; initial implementation stayed single-writer, reviewer sidecar added after patch to avoid write-set collision`
- predicted_topology: `autopilot-single plus reviewer`
- actual_topology: `autopilot-single plus reviewer`
- spawn_count: `1`
- rework_or_reclassification: `one bounded repair after reviewer found import-boundary test gap`
- reviewer_findings: `fixed`
- verification_outcome: `passed`
- next_gate_adjustment: `Next planner-selected task is scripts/extract_refactor_candidates.py responsibility split.`
