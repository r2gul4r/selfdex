# Run 20260501-233915-subagent-model-effort-alignment

- project_key: selfdex
- goal: Align Selfdex project-scoped Codex subagents with the latest official subagent config model and GPT-5.5 role-specific reasoning policy.
- selected_candidate: subagent-model-effort-alignment
- agents_used: main, reviewer
- subagent_permission: @selfdex permits official Codex subagents when useful; hard approval zones remain separate.
- repair_attempts: 1
- result: All project-scoped Selfdex subagents now use gpt-5.5 with role-specific reasoning effort, docs explain official role-name stability, and validators parse TOML key/value policy instead of relying on substring checks.
- next_candidate: Run or reinstall home-local @selfdex plugin if full selfdex doctor readiness is required on this machine.

## Write Sets

- .codex/agents/*.toml
- docs and campaign state model policy
- setup/plugin validators and regression tests

## Verification

- OpenAI official docs checked: Codex subagents/custom agents/config and GPT-5.5 reasoning guidance
- python -m unittest tests.test_selfdex_setup tests.test_selfdex_plugin tests.test_run_target_codex: pass, 24 tests after sandbox escalation
- python -m unittest discover -s tests: pass, 227 tests after sandbox escalation
- scripts/check_selfdex_plugin.py --root . --format json: pass
- scripts/check_doc_drift.py --root . --format json: pass
- scripts/check_campaign_budget.py --root . --include-git-diff --format json: pass
- git diff --check: pass with CRLF warnings only
- node bin/selfdex.js --help: pass
- node bin/selfdex.js install --dry-run: pass
- npm.cmd pack --dry-run --json: pass after sandbox escalation
- reviewer subagent: two P2 findings fixed, no P0/P1
