# Campaign State

## Campaign

- name: `selfdex-bootstrap`
- goal: `Make Selfdex the command center that reads a user-selected project, chooses the next improvement, evolution, or feature task, asks for approval, then safely delegates approved execution to Codex native agents and records the result.`
- risk_appetite: `medium-high`
- subagent_runtime: `official_codex_native_subagents`
- max_subagent_threads: `6`
- subagent_depth: `1`
- repair_attempts: `2`
- review_default: `non_trivial_implementation_only`
- reviewer_model: `gpt-5.5`
- reviewer_mode: `xhigh`
- direction_review_default: `recommend_and_wait_for_user_approval`
- direction_review_mode: `GPT Pro extended mode`
- explorer_default: `on_after_selfdex_invocation`
- parallel_default: `on_when_subtasks_are_independent`

## Model Usage Policy

- gpt_direction_review_role: `high-level product, milestone, roadmap, and priority direction only`
- gpt_direction_review_surface: `@chatgpt-apps or another user-approved GPT Pro extended review path when available`
- gpt_direction_review_scope: `project direction, product fit, improvement ideas, roadmap priorities, and additional feature opportunities`
- gpt_direction_review_approval: `user-approved-or-user-called-only`
- gpt_direction_review_auto_call: `False`
- gpt_direction_review_triggers: `project goals conflict or are unclear; candidate tasks are all strategically ambiguous; feature priority cannot be decided from code evidence alone; milestone or product direction needs to be reset; major surface such as ChatGPT Apps, MCP, public UI, or automation loop is being considered; user asks for product or strategy review`
- gpt_direction_review_non_triggers: `routine coding; tests; refactors; bug fixes; documentation drift; diff review`
- selfdex_role: `coordinate the loop, freeze contracts, manage approval, record evidence, and prevent uncontrolled autonomy`
- codex_role: `implement safely, verify, debug failures, review diffs, and stop when work becomes a product-direction question`
- code_review_surface: `Codex native reviewer subagent`
- fast_exploration_model: `gpt-5.4-mini-or-equivalent`
- demanding_agent_model: `gpt-5.5`
- reviewer_agent_model: `gpt-5.5`
- reviewer_reasoning_effort: `high-or-xhigh-for-risky-changes`
- product_direction_model: `GPT-Pro-extended-user-approved-only`
- prompt_guidance_role: `operating principle for roles, tool boundaries, success criteria, stop conditions, verification, and compact evidence`
- prompt_guidance_auto_call: `False`
- subagent_backend: `Codex native Subagents/MultiAgentV2`
- subagent_permission_trigger: `@selfdex invocation`
- legacy_topology_controls_active: `False`
- legacy_multiagent_baseline: `False`

## Subagent Permission Policy

- trigger: `@selfdex`
- meaning: `The user is asking Selfdex to run command-center mode and is also giving explicit permission to use Codex native Subagents/MultiAgentV2 when useful.`
- main_agent_role: `requirements, task selection, approval boundaries, integration, final reporting, and run records`
- automatic_read_only_lanes: `explorer; reviewer; docs_researcher; ci_or_log_analysis; summarization`
- write_capable_worker_rule: `Worker subagents require a frozen contract and disjoint write boundary.`
- legacy_runtime_terms_active: `False`

## First App Surface

- surface_kind: `read_only`
- write_capable_target_execution_exposed: `False`
- allowed_fields: `registered projects; next recommended task; latest run records; approval status`

## Hard Approval Zones

- destructive Git or filesystem operations
- secrets, credentials, private keys, or token access
- paid API calls
- public deployment
- database migration or production write
- cross-workspace edits
- npm publish
- git commit or git push unless the user explicitly asks or project policy enables the commit gate

## Current Locks

- none

## Candidate Queue

none

## Completed Queue Items

- Add real unit tests for `scripts/plan_next_task.py`.
- Add `work_type` classification to planner candidates.
- Add a Socratic evaluator for candidate decisions.
- Add a run recorder that writes `runs/YYYYMMDD-HHMMSS-<slug>.md`.
- Add a project registry for read-only multi-project analysis.
- Add an orchestration planner that records spawn decisions and write sets.
- Add fixture-based tests for candidate extractors.
- Add a campaign budget checker that rejects out-of-contract work.
- Add generated report drift checks for Selfdex docs.
- Clean stale verification entrypoints and document the quality signal sample payload.
- Add MCP connection autonomy rules for ordinary server connection commands.
- Broaden command autonomy to all ordinary non-destructive workflow commands.
- Split planner orchestration-fit heuristics out of `scripts/plan_next_task.py`.
- Split file metric models and line analysis out of `scripts/collect_repo_metrics.py`.
- Add a dependency-free coverage signal check path to repository verification.
- Add an integration test for test-gap extraction feeding planner selection.
- Suppress feature-gap detector stopword self-reference false positives.
- Add external validation readiness reporting for 2-3 read-only project registration.
- Register three existing sibling repositories as external read-only validation targets.
- Add shared generated/dependency directory exclusions before external read-only scans.
- Add external read-only candidate snapshot generation and binary-safe metric scanning.
- Support candidate quality templates generated from external read-only snapshots.
- Mark external validation reports with unscored candidates as needing scoring.
- Exclude lockfiles and Codex backup artifacts from refactor candidate snapshots.
- Make external candidate snapshots support explicit user-selected repository scopes.
- Add read-only external project planning with a Codex execution prompt.
- Update generated Codex execution prompts to GPT-5.5-style prompt and skill routing.
- Add target-project Codex orchestration with project-scoped run records.
- Add project direction intelligence before hygiene-only target candidate planning.
- Rewrite README around Selfdex as a local AI project lead.
- Make target Codex execution truly bounded.
- Create external validation proof package.
- Add CI and machine-readable project registry.
- Improve planner evidence, clustering, run-history demotion, and write-boundary quality.
- Deduplicate run-history penalty helpers.
- Split project direction evidence and opportunity responsibilities.
- Deduplicate project-direction product signal detection blocks.
- Split target Codex app-server session responsibilities.
- Deduplicate shared slug normalization helpers.
- Deduplicate target Codex blocked CLI tests.
- Deduplicate external validation test payload fixtures.
- Deduplicate external project registry test fixtures.
- Wrap the read-only control surface snapshot as a dependency-free local MCP JSON-RPC tool scaffold.
- Align model usage, approval gates, JSON source-of-truth enforcement, and read-only control-surface approval status.
- Package Selfdex as a repo-local Codex plugin for future `@selfdex` project-session invocation.
- Add a one-command installer for home-local `@selfdex` plugin setup from a cloned checkout.
- Add a true one-line PowerShell bootstrap installer that clones or updates Selfdex and installs the `@selfdex` plugin.
- Add an npm-compatible CLI so the post-publish command can be `npx selfdex install`.
- Reposition Selfdex runtime policy around GPT-5.5 prompt guidance, lightweight default execution, and optional Codex native Subagents.
- Fix GitHub Actions bootstrap installer test portability and add a GitHub-only post-push status check routine.
- Add one-command setup doctor to the installer and CLI.
- Make README Korean-first with an English mirror.
- Add commit gate after review and verification.
- Replace legacy local orchestration logic with official Codex native Subagents/MultiAgentV2 policy.
- Separate GPT Pro / ChatGPT Apps product direction review from Codex reviewer subagent code review and harden subagent readiness checks.

## Latest Run

- status: `local_verified`
- project_key: `selfdex`
- artifact_path: `runs/selfdex/20260501-231320-review-routing-and-subagent-readiness.md`
- summary: `Selfdex now separates GPT Pro / ChatGPT Apps product direction review from Codex reviewer subagent code review, wires docs_researcher into planner recommendations, and validates .codex subagent policy files in the setup doctor.`
