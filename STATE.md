# STATE

## Current Task

- task: `codex-home-plugin-install-fix`
- phase: `local_verified`
- scope: `Fix the one-line installer so the @selfdex plugin is installed into the Codex discovery home instead of only the operating-system home.`
- verification_target: `installer dry run, setup/plugin tests, doctor against Codex home, npm package dry run, GitHub Actions, npm publish 0.1.1`

## Orchestration Profile

- runtime_basis: `official_codex_native_subagents`
- trigger_basis: `The published npx installer completed but the user reported the plugin does not appear in Codex, and local evidence shows the installer wrote C:\Users\Administrator\.agents while the app discovery home is C:\Users\Administrator\.codex.`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `use_official_codex_subagents_terms`
  - `preserve_hard_approval_zones`
  - `installer_default_must_match_codex_discovery_home`
  - `doctor_must_detect_plugin_home_mismatch`
  - `user_requested_commit_push_and_npm_publish`
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
- selection_reason: `This is a focused installer and doctor fix with a known failure mode; no subagent split is needed.`

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
- write_set: `codex_home_plugin_install_fix`
- write_sets:
  - `main`:
    - `STATE.md`
    - `STATE.json`
    - `CAMPAIGN_STATE.md`
    - `CAMPAIGN_STATE.json`
    - `package.json`
    - `bin/selfdex.js`
    - `install.ps1`
    - `README.md`
    - `README.en.md`
    - `scripts/check_selfdex_setup.py`
    - `scripts/install_selfdex_plugin.py`
    - `tests/test_selfdex_setup.py`
    - `tests/test_install_selfdex_plugin.py`
    - `runs/selfdex/`
    - `ERROR_LOG.md`
- shared_assets_owner: `main`

## Contract Freeze

- `npx selfdex install` must install the plugin into the Codex discovery home by default: `CODEX_HOME` when set, otherwise `$HOME/.codex`.
- `selfdex doctor` must check the same plugin home by default and surface the selected home in output.
- Manual `--home` remains available for explicit alternate plugin roots.
- The old OS-home install path may remain as a compatibility artifact, but it must not be the default success signal.
- User separately requested commit, push, and npm publish after local verification; publish target is `selfdex@0.1.1`.
- Hard approval zones remain unchanged.

## Reviewer

- reviewer: `required_by_policy_surface_change`
- reviewer_mode: `local_verification_plus_diff_review`
- reviewer_target: `official subagent model and reasoning-effort alignment, doctor/plugin validator coverage, role-name compatibility with official Codex docs`
- reviewer_focus: `Do active docs overclaim renamed roles? Do validators catch stale GPT-5.4-mini or missing role-specific effort?`
- reviewer_result: `Codex native reviewer subagent found no P0/P1 findings. Two P2 findings were fixed inside scope: agent policy validators now parse TOML key/value pairs instead of substring matching, and focused tests cover missing model_reasoning_effort separately from stale model values.`

## Last Update

- timestamp: `2026-05-02T01:29:00+09:00`
- phase: `local_verified`
- status: `Installer now targets Codex discovery home by default, local Codex-home plugin install was repaired, and focused verification passed.`
- verification_result:
  - `python -m unittest tests.test_install_selfdex_plugin tests.test_selfdex_setup`: `pass, 13 tests`
  - `node bin/selfdex.js install --dry-run`: `pass; plugin home resolves to C:\Users\Administrator\.codex`
  - `python scripts/check_selfdex_setup.py --root . --home C:\Users\Administrator\.codex --codex-home C:\Users\Administrator\.codex --format json`: `pass`
  - `npm.cmd pack --dry-run --json`: `pass`
  - `npm.cmd publish --access public --dry-run`: `pass for selfdex@0.1.1`
  - `git diff --check`: `pass with CRLF warnings only`
- run_artifact: `runs/selfdex/20260502-012900-codex-home-plugin-install-fix.md`

## Retrospective

- task: `subagent-model-effort-alignment`
- evaluation_fit: `matched`
- runtime_fit: `official_codex_native_subagents`
- actual_agent_usage: `main implementation plus Codex native reviewer subagent.`
- verification_outcome: `pass`
- next_gate_adjustment: `Doctor and plugin checks should reject any Selfdex project-scoped subagent that falls back to stale GPT-5.4-mini or loses the frozen role-specific reasoning effort.`
