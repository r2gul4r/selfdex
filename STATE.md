# STATE

## Current Task

- task: `one-command-setup-doctor`
- phase: `local_verified`
- scope: `Make npx selfdex install finish with a complete default setup check: Selfdex plugin installed, local fallbacks available, recommended Codex/GitHub integrations reported, and no Gmail dependency.`
- verification_target: `setup doctor tests, npm CLI tests, bootstrap installer tests, doc drift, campaign budget, pack/publish dry-runs`

## Orchestration Profile

- score_total: `7`
- score_breakdown:
  - `installer_behavior_change`: 2
  - `cli_surface_change`: 2
  - `integration_boundary`: 1
  - `docs_and_tests`: 1
  - `publish_surface`: 1
- hard_triggers:
  - `installer_default_behavior_change`
  - `plugin_permission_boundary`
  - `npm_public_surface`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `single_session_for_tightly_coupled_installer_change`
  - `no_unapproved_external_plugin_install`
  - `no_gmail_dependency_for_ci_status`
  - `preserve_existing_git_history`
  - `run_record_required`
- selected_skills:
  - `selfdex-autopilot`
- execution_topology: `single-session`
- orchestration_value: `medium`
- agent_budget: `0`
- efficiency_basis: `The install, doctor, docs, and tests must use one consistent UX contract; splitting this across agents would increase wording and behavior drift.`
- spawn_decision: `no_spawn`
- selection_reason: `The user wants one install to create the best possible default Codex setup, while external integrations remain user-authorized boundaries.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Do not run npm publish.`
  - `Do not install or modify official Codex/GitHub/ChatGPT Apps plugins without explicit user approval.`
  - `Do not hardcode secrets or read tokens.`
  - `Do not require Gmail for setup or CI feedback.`
  - `Keep npx selfdex install as the primary public path.`
  - `Keep target-project writes approval-gated.`
- task_acceptance:
  - `npx selfdex install runs the Selfdex plugin install and then a setup doctor by default.`
  - `The setup doctor reports core Selfdex plugin readiness.`
  - `The setup doctor reports recommended integrations such as GitHub plugin availability without trying to force-install them.`
  - `The setup doctor reports GitHub Actions fallback availability.`
  - `The CLI exposes selfdex doctor for rechecking setup after installation.`
  - `Docs explain that one install completes core setup and reports remaining user-auth integration steps.`
- non_goals:
  - `Do not implement background setup loops.`
  - `Do not call paid APIs.`
  - `Do not auto-connect GitHub accounts.`
  - `Do not auto-enable GPT Pro or model entitlements.`
  - `Do not change package name or version in this task.`
- hard_checks:
  - `python -m unittest discover -s tests -p "test_selfdex_setup.py"`
  - `python -m unittest discover -s tests -p "test_npm_cli.py"`
  - `python -m unittest discover -s tests -p "test_bootstrap_installer.py"`
  - `python -m compileall -q scripts tests`
  - `node bin/selfdex.js --help`
  - `node bin/selfdex.js install --dry-run`
  - `node bin/selfdex.js doctor --help`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
  - `npm.cmd pack --dry-run --json`
  - `npm.cmd publish --access public --dry-run`
- llm_review_rubric:
  - `Does the installer make core setup complete without pretending it can install external account-bound plugins?`
  - `Does the doctor give actionable status instead of vague advice?`
  - `Does this preserve safety and approval boundaries?`
- evidence_required:
  - `changed files summary`
  - `verification command results`
  - `run artifact path`

## Writer Slot

- writer_slot: `main`
- write_set: `one_command_setup_doctor`
- write_sets:
  - `main`:
    - `STATE.md`
    - `STATE.json`
    - `CAMPAIGN_STATE.md`
    - `CAMPAIGN_STATE.json`
    - `README.md`
    - `docs/SELFDEX_FINAL_GOAL.md`
    - `docs/SELFDEX_HANDOFF.md`
    - `install.ps1`
    - `bin/selfdex.js`
    - `scripts/check_selfdex_setup.py`
    - `tests/test_selfdex_setup.py`
    - `tests/test_npm_cli.py`
    - `tests/test_bootstrap_installer.py`
    - `runs/selfdex/`
    - `ERROR_LOG.md`
- shared_assets_owner: `main`

## Contract Freeze

- `npx selfdex install` should install the Selfdex plugin and run setup doctor by default.
- Add `--skip-doctor` / `-SkipDoctor` only for troubleshooting or automation that wants installer-only behavior.
- `selfdex doctor` should re-run setup checks against an installed checkout.
- Core setup may be completed by Selfdex itself; external Codex/GitHub/ChatGPT Apps plugin connection must be reported as recommended user action, not silently installed.
- GitHub Actions feedback remains GitHub-based; Gmail is not part of the default setup.

## Reviewer

- reviewer: `not_required`
- reviewer_mode: `none`
- reviewer_target: `setup doctor diff after local verification if risk remains`
- reviewer_focus: `installer safety, external plugin boundary, public CLI UX`
- reviewer_result: `No separate reviewer lane used; single-session verification covered installer safety, external plugin boundary, and public CLI UX.`

## Last Update

- timestamp: `2026-05-01T20:35:42+09:00`
- phase: `local_verified`
- status: `Setup doctor implementation verified and recorded.`
- verification_result:
  - `python -m unittest discover -s tests -p "test_selfdex_setup.py"`: `pass`
  - `python -m unittest discover -s tests -p "test_npm_cli.py"`: `pass`
  - `python -m unittest discover -s tests -p "test_bootstrap_installer.py"`: `pass`
  - `python -m unittest discover -s tests`: `pass, 211 tests after sandbox escalation`
  - `python -m compileall -q scripts tests`: `pass`
  - `node bin/selfdex.js --help`: `pass`
  - `node bin/selfdex.js install --dry-run`: `pass`
  - `node bin/selfdex.js doctor --help`: `pass`
  - `python scripts/check_doc_drift.py --root . --format json`: `pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `pass`
  - `git diff --check`: `pass with line-ending warnings only`
  - `npm.cmd pack --dry-run --json`: `pass after sandbox escalation`
  - `npm.cmd publish --access public --dry-run`: `pass after sandbox escalation`
- run_artifact: `runs/selfdex/20260501-203542-one-command-setup-doctor.md`

## Retrospective

- task: `one-command-setup-doctor`
- score_total: `7`
- evaluation_fit: `matched`
- orchestration_fit: `single-session selected because CLI, installer, doctor, and docs need one coherent UX.`
- predicted_topology: `single-session`
- actual_topology: `single-session`
- spawn_count: `0`
- rework_or_reclassification: `new user request after CI repair`
- reviewer_findings: `none`
- verification_outcome: `pass`
- next_gate_adjustment: `Publish remains blocked on npm 2FA or OTP, not on Selfdex local verification.`
