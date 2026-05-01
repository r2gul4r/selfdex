# STATE

## Current Task

- task: `selfdex-skill-mention-install-fix`
- phase: `local_verified`
- scope: `Fix the installer so @selfdex appears as a Codex skill mention instead of only leaving file-search results.`
- verification_target: `installer dry run, setup/plugin tests, doctor against Codex home, local skill install, npm package dry run, diff check`

## Orchestration Profile

- runtime_basis: `official_codex_native_subagents`
- trigger_basis: `After installing into Codex home, the user showed @ mention results containing only Selfdex repo skills and file matches; the @selfdex command-center entry is not exposed as a plugin mention.`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `use_official_codex_subagents_terms`
  - `preserve_hard_approval_zones`
  - `installer_must_install_global_selfdex_skill`
  - `doctor_must_detect_skill_mention_surface`
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
- selection_reason: `This is a focused installer and doctor fix for the @ mention surface; no subagent split is needed.`

## Evaluation Plan

- evaluation_need: `focused_installer_surface`
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
  - `Installer copies the repo-local Selfdex plugin package into the Codex discovery home.`
  - `Installer also copies a global Selfdex skill to skills/selfdex so the @ mention menu can expose Selfdex as a skill.`
  - `Doctor reports a high-severity failure when the global skills/selfdex/SKILL.md entry is missing.`
  - `README Korean and English docs explain that file-only @ results are not a complete install signal.`
  - `Package version is bumped to 0.1.2 because 0.1.1 is already published.`
- non_goals:
  - `Do not delete historical run records.`
  - `Do not remove historical codex_multiagent evidence files.`
  - `Do not auto-spawn agents during this implementation turn.`
  - `Do not change package name.`
  - `Do not change official Codex/GitHub/ChatGPT Apps plugin installation state.`
- hard_checks:
  - `python -m unittest tests.test_install_selfdex_plugin tests.test_selfdex_setup`
  - `node bin/selfdex.js install --dry-run`
  - `node bin/selfdex.js doctor --install-root . --format markdown`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `npm.cmd pack --dry-run --json`
  - `git diff --check`
- evidence_required:
  - `changed files summary`
  - `verification command results`
  - `run artifact path`

## Writer Slot

- writer_slot: `main`
- write_set: `selfdex_skill_mention_install_fix`
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

- `npx selfdex install` must install both the plugin package and a global `selfdex` skill into the Codex discovery home.
- The `@` mention surface may show Selfdex under Skills rather than Plugins; file-only matches are not a successful install signal.
- `selfdex doctor` must fail if the global `skills/selfdex/SKILL.md` entry is missing.
- Manual `--home` remains available for explicit alternate Codex plugin/skill roots.
- Since `selfdex@0.1.1` is already published, any npm release for this fix must use `selfdex@0.1.2`.
- No commit, push, npm publish, deploy, secret access, or destructive action is part of this fix unless separately requested.
- Hard approval zones remain unchanged.

## Reviewer

- reviewer: `review_complete`
- reviewer_mode: `local_verification_plus_diff_review`
- reviewer_target: `installer copy behavior, doctor detection, public install wording, npm package surface`
- reviewer_focus: `Does npx install create a Codex-discoverable Selfdex skill, and does doctor catch the missing-skill failure mode?`
- reviewer_result: `Local diff review found one state mismatch: Current Task phase still said implementation while verification was already local_verified. Fixed in STATE.md. No blocking issues remain in the focused installer surface.`

## Last Update

- timestamp: `2026-05-02T01:47:00+09:00`
- phase: `local_verified`
- status: `Installer now installs a global Selfdex skill for the @ mention surface, local Codex-home skill install was repaired, and focused verification passed.`
- verification_result:
  - `python -m unittest tests.test_install_selfdex_plugin tests.test_selfdex_setup`: `pass, 15 tests after sandbox-escalated rerun for Windows temp fixture writes`
  - `node bin/selfdex.js install --dry-run`: `pass`
  - `node bin/selfdex.js doctor --install-root . --format markdown`: `pass; selfdex-global-skill pass`
  - `python scripts/check_doc_drift.py --root . --format json`: `pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `pass`
  - `npm.cmd pack --dry-run --json`: `pass for selfdex@0.1.2`
  - `git diff --check`: `pass with CRLF warnings only`
- run_artifact: `runs/selfdex/20260502-014200-selfdex-skill-mention-install-fix.md`

## Retrospective

- task: `selfdex-skill-mention-install-fix`
- evaluation_fit: `matched`
- runtime_fit: `official_codex_native_subagents`
- actual_agent_usage: `main implementation and local diff review; no subagents spawned for this focused installer fix.`
- verification_outcome: `pass`
- next_gate_adjustment: `Doctor must keep treating missing global skills/selfdex/SKILL.md as a blocking setup issue because the UI may otherwise fall back to file search.`
