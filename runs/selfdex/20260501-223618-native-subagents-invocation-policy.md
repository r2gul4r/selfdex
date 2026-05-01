# Run 20260501-223618-native-subagents-invocation-policy

- project_key: selfdex
- goal: Replace Selfdex legacy local orchestration logic with official Codex native Subagents/MultiAgentV2 runtime policy.
- selected_candidate: native-subagents-invocation-policy
- agents_used: main
- subagent_permission: @selfdex invocation permits official Codex native Subagents/MultiAgentV2 when useful; no subagents were spawned for this patch.
- repair_attempts: 1
- result: implemented and locally verified
- next_candidate: scripts/check_campaign_budget.py responsibility split and boundary cleanup

## Write Sets

- policy docs, @selfdex plugin skill, Codex agent config, planner/check scripts, tests, state, run records

## Verification

- python -m unittest discover -s tests: pass (218 tests)
- python -m unittest tests.test_campaign_budget tests.test_selfdex_plugin tests.test_record_run tests.test_commit_gate tests.test_plan_subagent_fit tests.test_plan_next_task: pass (44 tests)
- python scripts/check_selfdex_plugin.py --root . --format json: pass
- python scripts/check_campaign_budget.py --root . --include-git-diff --format json: pass
- python scripts/check_doc_drift.py --root . --format json: pass
- python scripts/plan_next_task.py --root . --format json: pass
- node bin/selfdex.js --help / --version / install --dry-run: pass
- npm.cmd pack --dry-run --json: pass after sandbox escalation
- git diff --check: pass with CRLF warnings only
