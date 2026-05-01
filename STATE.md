# STATE

## Current Task

- task: `subagent-model-effort-alignment`
- phase: `local_verified`
- scope: `Verify the current official Codex subagent naming/config model, keep official role names, align all project-scoped Selfdex subagents to GPT-5.5, and make setup/plugin checks catch stale model or reasoning-effort drift.`
- verification_target: `focused setup/plugin tests, official subagent policy validators, doc drift, campaign boundary check, diff check, reviewer subagent`

## Orchestration Profile

- runtime_basis: `official_codex_native_subagents`
- trigger_basis: `The user asked to re-check whether the latest Codex multi-agent/subagent update is applied, called out stale-looking subagent names, and requested all subagents use GPT-5.5 with role-specific reasoning effort.`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `use_official_codex_subagents_terms`
  - `official_subagent_docs_checked`
  - `preserve_hard_approval_zones`
  - `validate_codex_policy_surface_in_doctor`
  - `align_project_scoped_agents_to_gpt_5_5`
  - `role_specific_reasoning_effort`
  - `run_record_required`
- selected_skills:
  - `selfdex-autopilot`
  - `selfdex-commit-gate`
- selected_agents:
  - `main`
  - `explorer`
  - `worker`
  - `reviewer`
  - `docs_researcher`
- subagent_permission: `@selfdex invocation is explicit standing permission for Selfdex to recommend and use Codex native subagents when useful.`
- subagent_limits:
  - `Read-only explorer, reviewer, docs_researcher, CI/log analysis, and summarization lanes may be used automatically after @selfdex is invoked.`
  - `Write-capable worker lanes require a frozen contract and disjoint write boundary.`
  - `Commit, push, publish, deploy, production writes, secret access, destructive filesystem operations, and destructive Git operations still require separate explicit approval.`
- selection_reason: `Official Codex docs confirm built-in/custom subagent roles and project-scoped .codex/agents TOML files; current Selfdex drift is model/effort policy, not role-name replacement.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Do not run npm publish.`
  - `Do not install or modify official Codex/GitHub/ChatGPT Apps plugins without explicit user approval.`
  - `Do not hardcode secrets or read tokens.`
  - `Do not require Gmail for setup or CI feedback.`
  - `Keep npx selfdex install as the primary public path.`
  - `Keep target-project writes approval-gated.`
  - `Do not create automatic background commit loops.`
  - `Do not run git commit or git push as part of this implementation unless explicitly requested after the patch is ready.`
- task_acceptance:
  - `@selfdex invocation is documented as explicit permission to use official Codex native Subagents/MultiAgentV2 when useful.`
  - `Active docs and plugin skill text no longer present single-session, delegated-parallel, score_total, or agent_budget as the Selfdex runtime model.`
  - `Official agent roles are documented and wired: main, explorer, worker, reviewer, docs_researcher.`
  - `GPT Pro / ChatGPT Apps direction review is documented as product-strategy and feature-direction review, not code diff review.`
  - `Codex native reviewer subagent is documented as the code review path for non-trivial implementation.`
  - `.codex/config.toml and .codex/agents/*.toml define the project-scoped official subagent setup and selfdex doctor validates them.`
  - `Validation fails if the active plugin returns to old topology wording or omits the @selfdex subagent permission boundary.`
- non_goals:
  - `Do not delete historical run records.`
  - `Do not remove historical codex_multiagent evidence files.`
  - `Do not auto-spawn agents during this implementation turn.`
  - `Do not change package name or version in this task.`
  - `Do not change installer runtime behavior beyond documentation and validation alignment.`
- hard_checks:
  - `python -m unittest tests.test_selfdex_setup tests.test_selfdex_plugin`
  - `python scripts/check_selfdex_plugin.py --root . --format json`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
- evidence_required:
  - `changed files summary`
  - `verification command results`
  - `run artifact path`

## Writer Slot

- writer_slot: `main`
- write_set: `subagent_model_effort_alignment`
- write_sets:
  - `main`:
    - `STATE.md`
    - `STATE.json`
    - `CAMPAIGN_STATE.md`
    - `CAMPAIGN_STATE.json`
    - `AGENTS.md`
    - `AUTOPILOT.md`
    - `README.md`
    - `README.en.md`
    - `docs/SELFDEX_FINAL_GOAL.md`
    - `.agents/skills/selfdex-autopilot/SKILL.md`
    - `.codex/config.toml`
    - `.codex/agents/explorer.toml`
    - `.codex/agents/worker.toml`
    - `.codex/agents/reviewer.toml`
    - `.codex/agents/docs-researcher.toml`
    - `plugins/selfdex/skills/selfdex/SKILL.md`
    - `scripts/check_selfdex_plugin.py`
    - `scripts/check_selfdex_setup.py`
    - `scripts/check_campaign_budget.py`
    - `scripts/run_target_codex.py`
    - `scripts/record_run.py`
    - `tests/test_selfdex_plugin.py`
    - `tests/test_selfdex_setup.py`
    - `tests/test_campaign_budget.py`
    - `tests/test_run_target_codex.py`
    - `docs/ORCHESTRATION_DECISION_PLAN.md`
    - `runs/selfdex/`
    - `ERROR_LOG.md`
- shared_assets_owner: `main`

## Contract Freeze

- `@selfdex` is the user-facing invocation for Selfdex command-center mode.
- Calling `@selfdex` means the user explicitly permits Selfdex to use official Codex native Subagents/MultiAgentV2 when useful.
- Selfdex must use official Codex terms in active policy: main agent, subagent, agent thread, explorer, worker, reviewer, docs_researcher.
- Official built-in role names `explorer` and `worker` stay unchanged; `reviewer` and `docs_researcher` stay as the documented/custom review pattern already used by Codex docs.
- Selfdex must stop presenting `single-session`, `delegated-*`, `score_total`, and `agent_budget` as active runtime controls.
- All project-scoped `.codex/agents/*.toml` files must use `model = "gpt-5.5"`.
- Role-specific reasoning effort is frozen as `explorer=low`, `docs_researcher=medium`, `worker=high`, and `reviewer=xhigh`.
- Read-only subagents can run after `@selfdex` when useful; write-capable workers still need frozen write boundaries.
- GPT Pro / ChatGPT Apps direction review is for product direction, product fit, improvement ideas, and additional features.
- Code diff review stays with Codex native reviewer subagents.
- `docs_researcher` must be reachable from planner recommendations when official docs, API, SDK, MCP, ChatGPT Apps, OpenAI, model, or GPT behavior matters.
- `selfdex doctor` must fail or warn clearly when the project-scoped `.codex` subagent policy files are missing or stale.
- Hard approval zones remain unchanged.

## Reviewer

- reviewer: `required_by_policy_surface_change`
- reviewer_mode: `local_verification_plus_diff_review`
- reviewer_target: `official subagent model and reasoning-effort alignment, doctor/plugin validator coverage, role-name compatibility with official Codex docs`
- reviewer_focus: `Do active docs overclaim renamed roles? Do validators catch stale GPT-5.4-mini or missing role-specific effort?`
- reviewer_result: `Codex native reviewer subagent found no P0/P1 findings. Two P2 findings were fixed inside scope: agent policy validators now parse TOML key/value pairs instead of substring matching, and focused tests cover missing model_reasoning_effort separately from stale model values.`

## Last Update

- timestamp: `2026-05-01T23:39:30+09:00`
- phase: `local_verified`
- status: `Subagent model and reasoning-effort alignment implemented, reviewer P2 findings repaired, verified, and recorded.`
- verification_result:
  - `OpenAI official docs checked: Codex subagents/custom agents/config and GPT-5.5 reasoning guidance`
  - `python -m unittest tests.test_selfdex_setup tests.test_selfdex_plugin tests.test_run_target_codex`: `pass, 24 tests after sandbox escalation`
  - `python -m unittest discover -s tests`: `pass, 227 tests after sandbox escalation`
  - `python scripts/check_selfdex_plugin.py --root . --format json`: `pass`
  - `python scripts/check_doc_drift.py --root . --format json`: `pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `pass`
  - `git diff --check`: `pass with CRLF warnings only`
  - `node bin/selfdex.js --help`: `pass`
  - `node bin/selfdex.js install --dry-run`: `pass`
  - `npm.cmd pack --dry-run --json`: `pass after sandbox escalation`
  - `reviewer subagent`: `P0/P1 none; two P2 findings fixed`
- run_artifact: `runs/selfdex/20260501-233915-subagent-model-effort-alignment.md`

## Retrospective

- task: `subagent-model-effort-alignment`
- evaluation_fit: `matched`
- runtime_fit: `official_codex_native_subagents`
- actual_agent_usage: `main implementation plus Codex native reviewer subagent.`
- verification_outcome: `pass`
- next_gate_adjustment: `Doctor and plugin checks should reject any Selfdex project-scoped subagent that falls back to stale GPT-5.4-mini or loses the frozen role-specific reasoning effort.`
