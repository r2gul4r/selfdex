# STATE

## Current Task

- task: `scripts/normalize_quality_signals.py 책임 분리와 경계 정리`
- phase: `closeout`
- scope: `split normalizer scoring and parsing helpers out of normalize_quality_signals.py without schema changes`
- verification_target: `compileall scripts and tests, unittest discover, doc drift, normalizer smoke checks, planner json/markdown, budget checker json, git diff --check`

## Orchestration Profile

- score_total: `8`
- score_breakdown:
  - `large_single_file_hotspot`: 1
  - `shared_quality_signal_scoring`: 1
  - `tool_result_parsing_boundaries`: 1
  - `schema_preservation_risk`: 1
  - `new_helper_module`: 1
  - `focused_test_update`: 1
  - `doc_drift_update`: 1
  - `verification_required`: 1
- hard_triggers:
  - `single_large_file_responsibility_split`
  - `behavior_schema_preservation`
- selected_rules:
  - `narrow_refactor`
  - `preserve_normalized_quality_signal_schema`
  - `preserve_cli_behavior`
  - `preserve_doc_drift`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `planner suggested mixed, but the actual implementation remains one tightly coupled normalizer helper extraction with shared schema-preservation checks; parallel write ownership would overlap`
- spawn_decision: `do_not_spawn; helper boundaries are coupled through normalize_payload and one regression suite, so handoff would add merge risk`
- selection_reason: `Planner selected scripts/normalize_quality_signals.py responsibility split with priority_score=51.75 after commit c1770fb.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `Repo metric caps, axis weights, score rounding, metric normalization, priority grading, and quality signal assembly move into a focused helper.`
  - `Tool-result parsing and coverage extraction move into focused helpers or imports while keeping public normalizer function names available where tests expect them.`
  - `normalize_quality_signals.py keeps the same CLI behavior and output schema.`
  - `Focused tests cover the extracted helper behavior and existing normalizer tests stay green.`
  - `README documents the new helper so doc drift stays clean.`
  - `Planner advances to a different candidate after the refactor.`
- non_goals:
  - `Do not edit codex_multiagent.`
  - `Do not touch installers or global Codex config.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
  - `Do not change normalizer JSON schemas except internal code ownership.`
  - `Do not scan or write other projects in this task.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . | python .\scripts\normalize_quality_signals.py --pretty`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/repo_quality_signal_utils.py --changed-path scripts/tool_result_utils.py --changed-path scripts/normalize_quality_signals.py --changed-path tests/test_repo_quality_signal_utils.py --changed-path tests/test_tool_result_utils.py --changed-path tests/test_normalize_quality_signals.py --changed-path README.md --changed-path runs/20260424-145351-normalizer-helper-extraction.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether repo metric scoring constants and helper outputs are identical after extraction.`
  - `Check whether normalize_quality_signals.py remains the CLI/schema owner while helpers own scoring and parsing internals.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `repo quality signal helper extraction`
- write_sets:
  - `main`:
    - `scripts/repo_quality_signal_utils.py`
    - `scripts/tool_result_utils.py`
    - `scripts/normalize_quality_signals.py`
    - `tests/test_repo_quality_signal_utils.py`
    - `tests/test_tool_result_utils.py`
    - `tests/test_normalize_quality_signals.py`
    - `README.md`
    - `runs/20260424-145351-normalizer-helper-extraction.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Extract normalizer helper logic from `scripts/normalize_quality_signals.py` into focused scoring and parsing modules.
- Preserve normalizer CLI flags, history behavior, and JSON output schema.
- Add focused helper tests and keep existing normalizer tests passing.
- Do not introduce external dependencies.
- Record the completed run under `runs/` and update the latest campaign run summary.
- Do not touch installers, global Codex config, codex_multiagent, secrets, deploys, paid APIs, or DB files.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual schema-preservation review against existing tests and smoke output`

## Last Update

- timestamp: `2026-04-24T14:53:51+09:00`
- phase: `closeout`
- status: `normalizer helper extraction completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 42 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\collect_repo_metrics.py --root . | python .\scripts\normalize_quality_signals.py --pretty`: `passed`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/repo_quality_signal_utils.py --changed-path scripts/tool_result_utils.py --changed-path scripts/normalize_quality_signals.py --changed-path tests/test_repo_quality_signal_utils.py --changed-path tests/test_tool_result_utils.py --changed-path tests/test_normalize_quality_signals.py --changed-path README.md --changed-path runs/20260424-145351-normalizer-helper-extraction.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=build_duplicate_candidate + build_hotspot_candidate 중복 정리`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed with LF-to-CRLF warning for scripts/normalize_quality_signals.py`
- note: `This task starts after commit c1770fb and expanded once when repo quality-signal extraction alone did not clear the hotspot.`

## Retrospective

- task: `normalizer helper extraction`
- score_total: `8`
- evaluation_fit: `good; helper tests, normalizer smoke, doc drift, planner, and budget checker all pass`
- orchestration_fit: `good; single-session handled coupled helper extraction without cross-agent merge risk`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `one bounded repair: added tool-result parsing split after first planner check still selected normalize_quality_signals.py`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Next candidate is build_duplicate_candidate + build_hotspot_candidate duplicate cleanup.`
