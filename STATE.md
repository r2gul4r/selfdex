# STATE

## Current Task

- task: `extract_markdown_section 중복 정리`
- phase: `closeout`
- scope: `reuse markdown_utils.extract_markdown_section in check_doc_drift without behavior change`
- verification_target: `compileall scripts and tests, unittest discover, doc drift, planner json/markdown, budget checker json, git diff --check`

## Orchestration Profile

- score_total: `4`
- score_breakdown:
  - `small_cross_file_refactor`: 1
  - `shared_markdown_helper_reuse`: 1
  - `doc_drift_contract`: 1
  - `verification_required`: 1
- hard_triggers:
  - `none`
- selected_rules:
  - `narrow_refactor`
  - `preserve_doc_drift_output_schema`
  - `preserve_markdown_utils_contract`
  - `preserve_guardrails`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `one call site can reuse the existing markdown helper; no independent write set`
- spawn_decision: `do_not_spawn; helper reuse is smaller than delegation overhead`
- selection_reason: `Planner selected extract_markdown_section duplicate cleanup with priority_score=50.6 after commit 53b1dca.`

## Evaluation Plan

- evaluation_need: `light`
- project_invariants:
  - `Selfdex should be more aggressive than codex_multiagent.`
  - `Destructive commands, secrets, deploys, paid calls, DB migrations, and cross-workspace edits remain approval-gated.`
  - `Imported scripts should remain runnable without external dependencies.`
- task_acceptance:
  - `check_doc_drift.py imports the shared markdown section helper.`
  - `check_doc_drift.py preserves quick-start detection behavior.`
  - `Existing doc drift tests pass.`
  - `Planner advances or has a clear next candidate after the refactor.`
- non_goals:
  - `Do not edit codex_multiagent.`
  - `Do not touch installers or global Codex config.`
  - `Do not touch secrets, deploys, paid APIs, or databases.`
  - `Do not introduce a new helper module.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/check_doc_drift.py --changed-path runs/20260424-150256-doc-drift-markdown-helper.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether list-to-string conversion preserves the old Quick Start section comparison.`
- evidence_required:
  - `verification command output`
  - `selected planner candidate`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `doc drift markdown helper reuse`
- write_sets:
  - `main`:
    - `scripts/check_doc_drift.py`
    - `runs/20260424-150256-doc-drift-markdown-helper.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
- shared_assets_owner: `main`

## Contract Freeze

- Replace local `extract_markdown_section` in `scripts/check_doc_drift.py` with `scripts/markdown_utils.py`.
- Preserve the string behavior expected by Quick Start command checks.
- Add a focused test only if existing coverage does not catch the behavior.
- Do not introduce new dependencies or new generated-report scripts.
- Record the completed run under `runs/` and update the latest campaign run summary.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual doc-drift behavior preservation review`

## Last Update

- timestamp: `2026-04-24T15:02:56+09:00`
- phase: `closeout`
- status: `markdown helper reuse completed.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `passed; 43 tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path scripts/check_doc_drift.py --changed-path runs/20260424-150256-doc-drift-markdown-helper.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json`: `passed; selected=scripts/collect_repo_metrics.py 책임 분리와 경계 정리`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed`
  - `git diff --check`: `passed with LF-to-CRLF warning for scripts/check_doc_drift.py`
- note: `This task starts after commit 53b1dca.`

## Retrospective

- task: `doc drift markdown helper reuse`
- score_total: `4`
- evaluation_fit: `good; existing doc drift tests covered the helper return conversion`
- orchestration_fit: `good; single-session matched tiny helper reuse`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `manual review only; no subagent spawned`
- verification_outcome: `passed`
- next_gate_adjustment: `Next candidate is scripts/collect_repo_metrics.py responsibility split.`
