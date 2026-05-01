# STATE

## Current Task

- task: `readme-bilingual-default-korean`
- phase: `local_verified`
- scope: `Make README.md the Korean default, add an English README mirror, and document the setup doctor / one-command install behavior with language links.`
- verification_target: `doc drift, campaign budget, markdown link sanity, package dry-run surface`

## Orchestration Profile

- score_total: `4`
- score_breakdown:
  - `public_readme_language_change`: 2
  - `npm_package_doc_surface`: 1
  - `state_and_record_update`: 1
- hard_triggers:
  - `public_documentation_surface`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `single_session_for_documentation_surface_change`
  - `no_unapproved_external_plugin_install`
  - `no_gmail_dependency_for_ci_status`
  - `preserve_existing_git_history`
  - `run_record_required`
- selected_skills:
  - `selfdex-autopilot`
- execution_topology: `single-session`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `The work is a tightly coupled README language split and package doc surface update; delegation would add translation drift.`
- spawn_decision: `no_spawn`
- selection_reason: `The user wants Korean as the default README language with English/Korean navigation and current install-doctor behavior documented.`

## Evaluation Plan

- evaluation_need: `focused`
- project_invariants:
  - `Do not run npm publish.`
  - `Do not install or modify official Codex/GitHub/ChatGPT Apps plugins without explicit user approval.`
  - `Do not hardcode secrets or read tokens.`
  - `Do not require Gmail for setup or CI feedback.`
  - `Keep npx selfdex install as the primary public path.`
  - `Keep target-project writes approval-gated.`
- task_acceptance:
  - `README.md is Korean by default.`
  - `README.md links to README.en.md and README.en.md links back to README.md.`
  - `Both language surfaces explain npx selfdex install and selfdex doctor.`
  - `Package files include README.en.md so the English link is available in packed artifacts.`
- non_goals:
  - `Do not implement background setup loops.`
  - `Do not call paid APIs.`
  - `Do not auto-connect GitHub accounts.`
  - `Do not auto-enable GPT Pro or model entitlements.`
  - `Do not change package name or version in this task.`
  - `Do not change installer or runtime behavior.`
- hard_checks:
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
  - `npm.cmd pack --dry-run --json`
  - `node bin/selfdex.js --help`
- llm_review_rubric:
  - `Does the README make Korean the default without losing English access?`
  - `Does the setup doctor explanation stay accurate?`
  - `Does package output include the linked English README?`
- evidence_required:
  - `changed files summary`
  - `verification command results`
  - `run artifact path`

## Writer Slot

- writer_slot: `main`
- write_set: `readme_bilingual_default_korean`
- write_sets:
  - `main`:
    - `STATE.md`
    - `STATE.json`
    - `CAMPAIGN_STATE.md`
    - `CAMPAIGN_STATE.json`
    - `README.md`
    - `README.en.md`
    - `package.json`
    - `runs/selfdex/`
    - `ERROR_LOG.md`
- shared_assets_owner: `main`

## Contract Freeze

- `README.md` should become the Korean default entrypoint.
- `README.en.md` should preserve the English public README content.
- Both files should expose language navigation links near the top.
- The changed install behavior must be visible: `npx selfdex install` installs the local plugin and runs `selfdex doctor`; account-bound integrations are reported, not silently installed.
- No runtime, installer, or package version behavior should change.

## Reviewer

- reviewer: `not_required`
- reviewer_mode: `none`
- reviewer_target: `setup doctor diff after local verification if risk remains`
- reviewer_focus: `installer safety, external plugin boundary, public CLI UX`
- reviewer_result: `No separate reviewer lane needed for a focused documentation language split.`

## Last Update

- timestamp: `2026-05-01T20:48:46+09:00`
- phase: `local_verified`
- status: `Bilingual README update verified and recorded.`
- verification_result:
  - `python scripts/check_doc_drift.py --root . --format json`: `pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `pass`
  - `git diff --check`: `pass with line-ending warnings only`
  - `rg language/install/doctor links in README.md README.en.md`: `pass`
  - `node bin/selfdex.js --help`: `pass`
  - `npm.cmd --cache C:/tmp/npm-cache-selfdex pack --dry-run --json`: `pass after sandbox escalation, README.en.md included`
- run_artifact: `runs/selfdex/20260501-204846-readme-bilingual-default-korean.md`

## Retrospective

- task: `readme-bilingual-default-korean`
- score_total: `4`
- evaluation_fit: `matched`
- orchestration_fit: `single-session selected because README.md and README.en.md must stay wording-aligned.`
- predicted_topology: `single-session`
- actual_topology: `single-session`
- spawn_count: `0`
- rework_or_reclassification: `new user request after setup doctor completion`
- reviewer_findings: `none`
- verification_outcome: `pass`
- next_gate_adjustment: `Default public documentation should remain Korean while preserving English access.`
