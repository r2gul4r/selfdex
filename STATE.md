# STATE

## Current Task

- task: `mcp connection command auto-run policy`
- phase: `closeout`
- scope: `allow ordinary MCP server connection/status/diagnostic commands to run automatically while keeping dangerous operations approval-gated`
- verification_target: `campaign budget check, doc drift check, git diff --check`

## Orchestration Profile

- score_total: `6`
- score_breakdown:
  - `permission_policy_change`: 1
  - `mcp_connection_workflow`: 1
  - `dangerous_command_boundary`: 1
  - `state_and_run_record_required`: 1
  - `verification_required`: 1
  - `commit_required`: 1
- hard_triggers:
  - `permission_semantics`
  - `workflow_policy_change`
- selected_rules:
  - `describe_existing_authority_not_host_bypass`
  - `dangerous_drive_operations_remain_approval_gated`
  - `no_global_config_edit`
  - `no_installers`
  - `no_secrets_deploy_paid_api_db`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `the change is one tightly coupled policy wording update plus state/run records; delegation would add handoff cost without independent verification`
- spawn_decision: `do_not_spawn; implement policy wording locally`
- selection_reason: `User explicitly asked to auto-run ordinary MCP server connection commands except dangerous commands such as drive deletion. This is permission wording, so keep scope narrow and guardrail-heavy.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Selfdex remains aggressive but bounded.`
  - `Repository rules cannot bypass host-level approval requirements.`
  - `Dangerous filesystem, drive, volume, partition, format, destructive Git, installer/global config, secrets, deploy, paid API, and DB operations remain gated.`
  - `Only C:\lsh\git\selfdex may be modified.`
- task_acceptance:
  - `AGENTS.md defines ordinary MCP connection commands that may run automatically.`
  - `AGENTS.md explicitly blocks dangerous drive/delete/format/partition operations from auto-run.`
  - `The wording does not grant permission to edit global Codex config or installers.`
  - `The wording does not weaken secret/deploy/paid API/DB guardrails.`
  - `CAMPAIGN_STATE.md and runs/ record the policy update.`
- non_goals:
  - `Do not edit global Codex config.`
  - `Do not install or modify MCP servers.`
  - `Do not touch codex_multiagent or any other repository.`
  - `Do not run destructive commands.`
- hard_checks:
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path AGENTS.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-161000-mcp-connection-autonomy.md --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether the new autonomy wording could be misread as approval for destructive drive or data operations.`
  - `Check whether secret and global-config boundaries remain explicit.`
  - `Check whether ordinary MCP connection commands are clear enough to reduce unnecessary prompts.`
- evidence_required:
  - `diff review`
  - `campaign budget result`
  - `doc drift result`
  - `git status summary`

## Writer Slot

- writer_slot: `main`
- write_set: `mcp connection autonomy policy`
- write_sets:
  - `main`:
    - `AGENTS.md`
    - `CAMPAIGN_STATE.md`
    - `STATE.md`
    - `runs/20260424-161000-mcp-connection-autonomy.md`
- shared_assets_owner: `main`

## Contract Freeze

- Add a narrow MCP connection autonomy rule to `AGENTS.md`.
- Ordinary read-only/status/list/ping/connect/reconnect/diagnose MCP commands can run automatically.
- Dangerous drive, volume, partition, format, recursive delete, destructive Git, installer/global config, secrets, deploy, paid API, and DB commands remain blocked or approval-gated.
- Do not edit global config or installer files.
- Record and commit the change.

## Reviewer

- reviewer: `none`
- reviewer_target: `n/a`
- reviewer_focus: `manual permission-boundary review`

## Last Update

- timestamp: `2026-04-24T16:18:00+09:00`
- phase: `closeout`
- status: `MCP connection autonomy policy completed.`
- verification_result:
  - `manual policy review`: `passed; wording permits ordinary MCP connection diagnostics but does not bypass host approval`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path AGENTS.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --changed-path runs/20260424-161000-mcp-connection-autonomy.md --format json`: `passed; violation_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json`: `passed; finding_count=0`
  - `git diff --check`: `passed`
  - `git status --short`: `only declared task files changed before commit`
  - `commit`: `ready after final staging`
- note: `This policy reduces prompts for ordinary MCP server connection work while preserving dangerous-command, secret, deploy, paid API, DB, installer, and global-config boundaries.`

## Retrospective

- task: `mcp connection command auto-run policy`
- score_total: `6`
- evaluation_fit: `good; verification focused on contract/budget and wording review`
- orchestration_fit: `good; single-session was appropriate for one policy document plus state/run records`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none`
- reviewer_findings: `manual permission-boundary review only`
- verification_outcome: `passed`
- next_gate_adjustment: `Next planner-selected implementation remains scripts/plan_next_task.py responsibility split.`
