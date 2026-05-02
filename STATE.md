# STATE

## Current Task

- task: `node-only-selfdex-doctor`
- phase: `local_verified`
- scope: `Start the Python-free public path by making selfdex doctor run a Node-native core setup check without requiring Python by default.`
- verification_target: `npm CLI focused tests, node doctor smoke, doc drift check, campaign budget check, git diff check`

## Orchestration Profile

- runtime_basis: `official_codex_native_subagents`
- trigger_basis: `The next goal is Python-free public path; the smallest safe first step is removing Python from the default selfdex doctor path while keeping Python tooling as legacy/advanced fallback.`
- selected_rules:
  - `state_before_writes`
  - `contract_freeze_before_implementation`
  - `use_official_codex_subagents_terms`
  - `preserve_hard_approval_zones`
  - `python_free_public_path_first_slice`
  - `node_native_doctor_default`
  - `preserve_python_fallback`
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
- selection_reason: `This is a bounded CLI and docs change with one write-capable lane; no subagent split is needed.`

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
  - `selfdex doctor runs a Node-native core setup check by default and does not require Python.`
  - `selfdex doctor --python <path> keeps the existing legacy Python doctor delegation path.`
  - `Node-native doctor reports plugin directory, marketplace entry, global skill, root config, project-scoped subagent policy files, Git availability, recommended integration hints, and manual GPT Pro status.`
  - `README Korean and English docs explain that doctor is Node-native while advanced legacy scripts may still use Python.`
  - `No npm package version change is made.`
- non_goals:
  - `Do not delete historical run records.`
  - `Do not remove historical codex_multiagent evidence files.`
  - `Do not auto-spawn agents during this implementation turn.`
  - `Do not change package name or version.`
  - `Do not change installer runtime behavior in this slice.`
  - `Do not change official Codex/GitHub/ChatGPT Apps plugin installation state.`
- hard_checks:
  - `python -m unittest tests.test_npm_cli`
  - `node bin/selfdex.js doctor --install-root . --format json`
  - `node bin/selfdex.js doctor --install-root . --format markdown`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
- evidence_required:
  - `changed files summary`
  - `verification command results`
  - `run artifact path`

## Writer Slot

- writer_slot: `main`
- write_set: `node_only_selfdex_doctor`
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
    - `runs/selfdex/`
    - `ERROR_LOG.md`
- shared_assets_owner: `main`

## Contract Freeze

- Default `selfdex doctor` must be Node-native and must not fail just because Python is absent.
- Existing Python doctor can still be invoked intentionally with `--python <path>`.
- Node-native doctor must keep output compatible with `--format json|markdown` and return non-zero only for blocking high-severity core failures.
- This slice does not rewrite installer, read-only planner, campaign checks, or advanced Python scripts.
- No npm publish, package version change, deploy, secret access, or destructive action is part of this fix.
- Hard approval zones remain unchanged.

## Reviewer

- reviewer: `review_complete`
- reviewer_mode: `local_verification_plus_diff_review`
- reviewer_target: `Node-native doctor behavior, legacy Python fallback boundary, README dependency wording`
- reviewer_focus: `Does the default doctor path actually avoid Python while preserving setup safety signals?`
- reviewer_result: `Local review found the Node-native doctor keeps the core setup checks, avoids Python by default, and preserves explicit legacy Python delegation through --python. No blocking issues remain.`

## Last Update

- timestamp: `2026-05-02T13:07:29+09:00`
- phase: `local_verified`
- status: `Default selfdex doctor now runs a Node-native setup check without requiring Python; legacy Python doctor remains available through --python.`
- verification_result:
  - `python -m unittest tests.test_npm_cli`: `pass, 8 tests`
  - `node bin/selfdex.js doctor --install-root C:\Users\Administrator\selfdex --format json`: `pass, runtime node-native`
  - `node bin/selfdex.js doctor --install-root C:\Users\Administrator\selfdex --format markdown`: `pass`
  - `python scripts/check_doc_drift.py --root . --format json`: `pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `pass`
  - `git diff --check`: `pass with CRLF warnings only`
- run_artifact: `runs/selfdex/20260502-130700-node-only-doctor.md`

## Retrospective

- task: `node-only-selfdex-doctor`
- evaluation_fit: `matched`
- runtime_fit: `official_codex_native_subagents`
- actual_agent_usage: `main implementation; no subagents spawned for this focused CLI slice.`
- verification_outcome: `pass`
- next_gate_adjustment: `Python-free public path should move one user-facing CLI command at a time and keep Python advanced tooling as fallback until replaced.`
