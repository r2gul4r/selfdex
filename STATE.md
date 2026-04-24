# STATE

## Current Task

- task: `general non-destructive command auto-run policy`
- phase: `closeout`
- scope: `broaden autonomy from MCP connection commands to ordinary non-destructive commands across the workflow`
- verification_target: `campaign budget check, doc drift check, git diff --check`

## Orchestration Profile

- score_total: `7`
- score_breakdown:
  - `permission_policy_change`: 1
  - `global_command_autonomy`: 1
  - `destructive_command_boundary`: 1
  - `workspace_write_boundary`: 1
  - `state_and_run_record_required`: 1
  - `verification_required`: 1
  - `commit_required`: 1
- hard_triggers:
  - `permission_semantics`
  - `workflow_policy_change`
- selected_rules:
  - `describe_existing_authority_not_host_bypass`
  - `dangerous_operations_remain_approval_gated`
  - `non_destructive_commands_auto_run`
  - `no_global_config_edit`
  - `no_installers`
  - `no_secrets_deploy_paid_api_db`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `the change is one tightly coupled policy wording update plus state/run records; delegation would not add independent verification`
- spawn_decision: `do_not_spawn; implement policy wording locally`
- selection_reason: `User asked to auto-run commands generally, not only MCP server commands, while excluding destructive commands. This is permission wording and needs a narrow safety boundary.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Selfdex remains aggressive but bounded.`
  - `Repository rules cannot bypass host-level approval requirements.`
  - `Non-destructive commands should run without needless confirmation.`
  - `Destructive filesystem, drive, Git, installer/global config, secrets, deploy, paid API, and DB operations remain gated.`
  - `Only C:\lsh\git\selfdex may be modified.`
- task_acceptance:
  - `AGENTS.md defines general non-destructive command autonomy.`
  - `AGENTS.md keeps host-level approval prompts authoritative.`
  - `AGENTS.md explicitly blocks destructive drive/delete/format/partition operations from auto-run.`
  - `AGENTS.md keeps destructive Git, global config, installer, secret, deploy, paid API, and DB boundaries explicit.`
  - `CAMPAIGN_STATE.md and runs/ record the policy update.`
- non_goals:
  - `Do not edit global Codex config.`
  - `Do not install or modify tools or MCP servers.`
  - `Do not touch codex_multiagent or any other repository.`
  - `Do not run destructive commands.`
- hard_checks:
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path AGENTS.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-162500-general-command-autonomy.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether the new autonomy wording could be misread as approval for destructive or cross-workspace operations.`
  - `Check whether host approval and secret/global-config boundaries remain explicit.`
  - `Check whether ordinary command auto-run is broad enough to reduce unnecessary prompts.`
- evidence_required:
  - `diff review`
  - `campaign budget result`
  - `doc drift result`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `general command autonomy policy`
- write_sets:
  - `main`:
    - `AGENTS.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
    - `runs/20260424-162500-general-command-autonomy.md`
- shared_assets_owner: `main`

## Contract Freeze

- Replace MCP-only autonomy wording with a general non-destructive command autonomy rule in `AGENTS.md`.
- Ordinary read-only, diagnostic, build, test, lint, format, local script, Git inspection, and configured MCP connection commands may run automatically when needed for the current task.
- Workspace writes remain bounded by the active task contract and write set.
- Dangerous drive, volume, partition, format, recursive delete, destructive Git, installer/global config, secrets, deploy, paid API, and DB commands remain blocked or approval-gated.
- Do not edit global config or installer files.
- Record and commit the change.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual permission-boundary review`

## Last Update

- timestamp: `2026-04-24T16:32:00+09:00`
- phase: `closeout`
- status: `general non-destructive command autonomy policy completed.`
- verification_result:
  - `manual policy review`: `passed; wording broadly auto-runs ordinary non-destructive commands and keeps host approval authoritative`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path AGENTS.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-162500-general-command-autonomy.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `git diff --check`: `passed`
  - `git status --short`: `only declared task files changed before commit`
- note: `Command autonomy now covers normal inspection, Git reads, local scripts, verification, formatting, builds, diagnostics, and MCP connection checks, while destructive or high-risk operations remain gated.`

## Retrospective

- task: `general non-destructive command auto-run policy`
- score_total: `7`
- evaluation_fit: `good; wording review focused on destructive and cross-workspace ambiguity`
- orchestration_fit: `good; single-session was appropriate for one policy document plus state/run records`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `manual permission-boundary review only`
- verification_outcome: `passed`
- next_gate_adjustment: `Next planner-selected implementation remains scripts/plan_next_task.py responsibility split.`
