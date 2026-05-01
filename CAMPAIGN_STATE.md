# Campaign State

## Campaign

- name: `selfdex-bootstrap`
- goal: `Make Selfdex the command center that reads a user-selected project, chooses the next improvement, evolution, or feature task, asks for approval, then safely delegates execution to Codex and records the result.`
- risk_appetite: `medium-high`
- default_agent_budget: `2`
- max_agent_budget: `4`
- repair_attempts: `2`
- review_default: `non_trivial_implementation_only`
- reviewer_model: `gpt-5.5`
- reviewer_mode: `xhigh`
- direction_review_default: `recommend_and_wait_for_user_approval`
- direction_review_mode: `GPT Pro extended mode`
- explorer_default: `on`
- parallel_default: `on_when_disjoint`

## Model Usage Policy

- gpt_direction_review_role: `high-level product, milestone, roadmap, and priority direction only`
- gpt_direction_review_approval: `user-approved-or-user-called-only`
- gpt_direction_review_auto_call: `False`
- gpt_direction_review_triggers: `project goals conflict or are unclear; candidate tasks are all strategically ambiguous; feature priority cannot be decided from code evidence alone; milestone or product direction needs to be reset; major surface such as ChatGPT Apps, MCP, public UI, or automation loop is being considered; user asks for product or strategy review`
- gpt_direction_review_non_triggers: `routine coding; tests; refactors; bug fixes; documentation drift; diff review`
- selfdex_role: `coordinate the loop, freeze contracts, manage approval, record evidence, and prevent uncontrolled autonomy`
- codex_role: `implement safely, verify, debug failures, review diffs, and stop when work becomes a product-direction question`
- fast_exploration_model: `mini-or-medium`
- candidate_contract_model: `gpt-5.5-high`
- complex_or_risky_model: `gpt-5.5-xhigh`
- routine_implementation_model: `medium-or-high`
- final_code_review_model: `gpt-5.5-xhigh`
- product_direction_model: `GPT-Pro-extended-user-approved-only`
- prompt_guidance_role: `operating principle for roles, tool boundaries, success criteria, stop conditions, verification, and compact evidence`
- prompt_guidance_auto_call: `False`
- lightweight_default_lane: `single-session`
- subagent_backend: `Codex native Subagents/MultiAgentV2 optional when explorer, worker, or reviewer lanes split cleanly`
- legacy_multiagent_baseline: `False`

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

## Latest Run

- status: `local_verified`
- project_key: `selfdex`
- artifact_path: `runs/selfdex/20260501-203542-one-command-setup-doctor.md`
- summary: `npx selfdex install now installs the local plugin and runs setup doctor by default; account-bound Codex/GitHub/ChatGPT integrations are reported as user actions.`
