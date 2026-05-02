# STATE

## Current Task

- task: `node-native-selfdex-install`
- phase: `local_verified`
- scope: `Continue the Python-free public path by making the default npm CLI install flow run clone/update, plugin install, and setup doctor without requiring Python.`
- verification_target: `npm CLI focused tests, node install dry-run, node doctor smoke, doc drift check, campaign budget check, git diff check, npm pack dry-run`

## Orchestration Profile

- runtime_basis: `official_codex_native_subagents`
- trigger_basis: `The previous slice removed Python from the default doctor path; the remaining public-path blocker is that npx selfdex install still delegates to install.ps1 and Python installer scripts.`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `use_official_codex_subagents_terms`
  - `preserve_hard_approval_zones`
  - `python_free_public_path_second_slice`
  - `node_native_install_default`
  - `preserve_legacy_powershell_fallback`
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
- selection_reason: `This is a bounded CLI, docs, and focused-test change with one write-capable lane; no subagent split is needed.`

## Evaluation Plan

- evaluation_need: `focused_cli_surface`
- project_invariants:
  - `Do not run npm publish.`
  - `Do not install or modify official Codex/GitHub/ChatGPT Apps plugins without explicit user approval.`
  - `Do not hardcode secrets or read tokens.`
  - `Do not require Gmail for setup or CI feedback.`
  - `Keep npx selfdex install as the primary public path.`
  - `Keep target-project writes approval-gated.`
  - `Do not create automatic background commit loops.`
  - `Do not run git commit or git push unless explicitly requested after this patch is verified.`
- task_acceptance:
  - `selfdex install uses Node-native clone/update, plugin copy, marketplace update, global skill install, and Node-native doctor by default.`
  - `selfdex install --dry-run previews the Node-native path and performs no writes.`
  - `selfdex install no longer requires Python unless the user intentionally uses legacy PowerShell/Python scripts outside the default npm path.`
  - `Existing install options remain compatible: --install-root, --plugin-home, --repo-url, --branch, --skip-plugin-install, --skip-doctor.`
  - `README Korean and English docs describe the Python-free npm install path and legacy script boundary.`
  - `No npm package version change is made.`
- non_goals:
  - `Do not port read-only planning or target Codex Python scripts in this slice.`
  - `Do not delete historical run records.`
  - `Do not remove install.ps1 or Python scripts.`
  - `Do not change package name or version.`
  - `Do not change official Codex/GitHub/ChatGPT Apps plugin installation state.`
  - `Do not run npm publish.`
- hard_checks:
  - `python -m unittest tests.test_npm_cli`
  - `node bin/selfdex.js install --dry-run --install-root C:/tmp/selfdex-npx-dry-run`
  - `node bin/selfdex.js doctor --install-root C:\Users\Administrator\selfdex --format json`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
  - `npm pack --dry-run --json`
- evidence_required:
  - `changed files summary`
  - `verification command results`
  - `run artifact path`

## Writer Slot

- writer_slot: `main`
- write_set: `node_native_selfdex_install`
- write_sets:
  - `main`:
    - `STATE.md`
    - `STATE.json`
    - `CAMPAIGN_STATE.md`
    - `CAMPAIGN_STATE.json`
    - `bin/selfdex.js`
    - `README.md`
    - `README.en.md`
    - `tests/test_npm_cli.py`
    - `plugins/selfdex/skills/selfdex/SKILL.md`
    - `runs/selfdex/`
    - `ERROR_LOG.md`
- shared_assets_owner: `main`

## Contract Freeze

- Default `selfdex install` must not invoke Python for plugin install or setup doctor.
- Node-native install must clone/update the selected checkout, copy the local plugin package into the Codex plugin home, install the global `selfdex` skill, update the marketplace entry, write `selfdex-root.json`, and run the Node-native doctor unless skipped.
- The legacy PowerShell/Python installer scripts remain available as fallback artifacts, but the npm CLI default path must not depend on them.
- Dry-run must preview the Node-native path and must not clone, update, copy, or modify marketplace files.
- No npm publish, package version change, deploy, secret access, or destructive action is part of this fix.
- Hard approval zones remain unchanged.

## Reviewer

- reviewer: `review_complete`
- reviewer_mode: `local_verification_plus_diff_review`
- reviewer_target: `Node-native install behavior, plugin copy safety, README dependency wording`
- reviewer_focus: `Does the default npm install path actually avoid Python while preserving setup safety and existing CLI options?`
- reviewer_result: `Local review found the Node-native install path no longer invokes Python, preserves existing install options, writes only the selected plugin home during actual install, keeps dry-run write-free, and reports concise install errors instead of Node stack traces. No blocking issues remain.`

## Last Update

- timestamp: `2026-05-02T13:37:42+09:00`
- phase: `local_verified`
- status: `Default selfdex install now uses the Node-native clone/update, plugin copy, global skill install, marketplace update, and Node-native doctor path without requiring Python.`
- verification_result:
  - `python -m unittest tests.test_npm_cli`: `pass, 9 tests`
  - `node bin/selfdex.js install --dry-run --install-root C:\tmp\selfdex-npx-dry-run`: `pass, Node-native dry-run and no writes`
  - `node bin/selfdex.js install --use-existing-checkout --install-root . --plugin-home .tmp-tests\manual-node-install --skip-doctor`: `pass, temp plugin install copied 6 files`
  - `node bin/selfdex.js doctor --install-root C:\Users\Administrator\selfdex --format json`: `pass, runtime node-native`
  - `python scripts/check_doc_drift.py --root . --format json`: `pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `pass`
  - `git diff --check`: `pass with CRLF warnings only`
  - `npm pack --dry-run --json`: `pass, selfdex@0.1.2 package includes 5 files`
- run_artifact: `runs/selfdex/20260502-133742-node-native-selfdex-install.md`

## Retrospective

- task: `node-native-selfdex-install`
- evaluation_fit: `matched`
- runtime_fit: `official_codex_native_subagents`
- actual_agent_usage: `main implementation; no subagents spawned for this focused CLI slice.`
- verification_outcome: `pass`
- next_gate_adjustment: `The public npx path is now Python-free for install and doctor; remaining Python dependency is limited to advanced planning/execution/checker scripts and legacy fallback commands.`
