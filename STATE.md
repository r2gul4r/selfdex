# STATE

## Current Task

- task: `selfdex-readme-skill-usage-docs`
- phase: `local_verified`
- scope: `Document the installed Selfdex skill surfaces and usage flow in README, then commit and push the documentation update.`
- verification_target: `README Korean/English usage review, doc drift check, campaign budget check, git diff check, commit gate, GitHub Actions`

## Orchestration Profile

- runtime_basis: `official_codex_native_subagents`
- trigger_basis: `The installed @ mention surface now shows Selfdex as a skill, and the user asked to add skill usage details to README and commit/push the docs.`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `use_official_codex_subagents_terms`
  - `preserve_hard_approval_zones`
  - `document_skill_usage_surface`
  - `user_requested_commit_and_push`
  - `run_record_required`
- selected_skills:
  - `selfdex-autopilot`
  - `selfdex-commit-gate`
- selected_agents:
  - `main`
- subagent_permission: `@selfdex invocation is explicit standing permission for Selfdex to recommend and use Codex native subagents when useful.`
- subagent_limits:
  - `Read-only explorer, reviewer, docs_researcher, CI/log analysis, and summarization lanes may be used automatically after @selfdex is invoked.`
  - `Write-capable worker lanes require a frozen contract and disjoint write boundary.`
  - `Commit, push, publish, deploy, production writes, secret access, destructive filesystem operations, and destructive Git operations still require separate explicit approval.`
- selection_reason: `This is a focused documentation update over README usage text and state mirrors; no subagent split is needed.`

## Evaluation Plan

- evaluation_need: `focused_documentation_surface`
- project_invariants:
  - `Do not run npm publish.`
  - `Do not install or modify official Codex/GitHub/ChatGPT Apps plugins without explicit user approval.`
  - `Do not hardcode secrets or read tokens.`
  - `Do not require Gmail for setup or CI feedback.`
  - `Keep npx selfdex install as the primary public path.`
  - `Keep target-project writes approval-gated.`
  - `Do not create automatic background commit loops.`
  - `Git commit and git push are explicitly requested for this documentation update.`
- task_acceptance:
  - `README Korean usage explains the global Selfdex skill entry, repo-local helper skills, and file-search results.`
  - `README English usage mirrors the same skill usage guidance.`
  - `The docs keep account-bound plugins such as GitHub and ChatGPT Apps as manual/recommended integrations, not silent installer side effects.`
  - `No npm package version or installer runtime behavior changes are made.`
- non_goals:
  - `Do not delete historical run records.`
  - `Do not remove historical codex_multiagent evidence files.`
  - `Do not auto-spawn agents during this implementation turn.`
  - `Do not change package name or version.`
  - `Do not change installer runtime behavior.`
  - `Do not change official Codex/GitHub/ChatGPT Apps plugin installation state.`
- hard_checks:
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
  - `python scripts/check_commit_gate.py --root . --commit-message "docs: document selfdex skill usage" --format json`
  - `python scripts/check_github_actions_status.py --root . --sha <pushed_sha> --branch main --event push --format json`
- evidence_required:
  - `changed files summary`
  - `verification command results`
  - `run artifact path`

## Writer Slot

- writer_slot: `main`
- write_set: `selfdex_readme_skill_usage_docs`
- write_sets:
  - `main`:
    - `STATE.md`
    - `STATE.json`
    - `CAMPAIGN_STATE.md`
    - `CAMPAIGN_STATE.json`
    - `README.md`
    - `README.en.md`
    - `runs/selfdex/`
    - `ERROR_LOG.md`
- shared_assets_owner: `main`

## Contract Freeze

- README usage must explain that the primary installed entry is the `Selfdex` global skill shown in the Codex `@` menu.
- README usage must distinguish global `Selfdex` from repo-local helper skills such as `Selfdex Autopilot` and `Selfdex Commit Gate`.
- README usage must explain that file search results in the `@` menu are not the intended command entry.
- README usage must include the basic target-project invocation and close-out/commit-gate expectation.
- No package, installer, runtime, npm publish, deploy, secret access, or destructive action is part of this fix.
- Git commit and push are approved by the current user request.
- Hard approval zones remain unchanged.

## Reviewer

- reviewer: `review_complete`
- reviewer_mode: `local_verification_plus_diff_review`
- reviewer_target: `README Korean/English skill usage wording, install boundary wording, commit-gate readiness`
- reviewer_focus: `Does the README tell users which @ entry to select and avoid implying that account-bound plugins are silently installed?`
- reviewer_result: `Local README review found the Korean and English usage guidance clear: it identifies the global Selfdex skill, separates helper skills from file results, and keeps account-bound plugin installs as manual actions. No blocking issues remain.`

## Last Update

- timestamp: `2026-05-02T02:17:36+09:00`
- phase: `local_verified`
- status: `README Korean and English usage docs now explain the Selfdex skill entries and commit-gate close-out flow.`
- verification_result:
  - `python scripts/check_doc_drift.py --root . --format json`: `pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `pass`
  - `git diff --check`: `pass with CRLF warnings only`
- run_artifact: `runs/selfdex/20260502-021700-readme-skill-usage-docs.md`

## Retrospective

- task: `selfdex-readme-skill-usage-docs`
- evaluation_fit: `matched`
- runtime_fit: `official_codex_native_subagents`
- actual_agent_usage: `main implementation; no subagents spawned for this focused documentation update.`
- verification_outcome: `pass`
- next_gate_adjustment: `README usage docs should keep the global skill, repo-local helper skills, and file-search fallback clearly separated.`
