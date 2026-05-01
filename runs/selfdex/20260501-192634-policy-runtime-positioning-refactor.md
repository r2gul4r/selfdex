# Policy Runtime Positioning Refactor

- status: `completed`
- project_key: `selfdex`
- task: `policy/runtime-positioning refactor`
- score_total: `6`
- topology: `single-session`
- agent_budget_used: `0`
- reviewer_basis: `GPT-5.5 xhigh Socratic plan review accepted with changes before implementation`

## Contract

- Reposition Selfdex as a GPT-5.5 prompt-guided command center.
- Keep GPT-5.5 prompt guidance as an operating principle, not automatic model invocation.
- Keep lightweight `single-session` as the default lane.
- Use Codex native Subagents/MultiAgentV2 only when explorer, worker, or reviewer lanes split cleanly.
- Remove `codex_multiagent` from the active registry and mirror while preserving historical run artifacts.
- Keep npm publish blocked until the policy, docs, skills, registry, and verification are aligned.

## Changes

- Updated public README, autopilot policy, final-goal, handoff, and both Selfdex skills around the new runtime model.
- Removed `codex_multiagent` from the active project registry.
- Replaced missing `fs` active proof target with existing read-only `apex_analist`, so the active external validation set is `daboyeo` and `apex_analist`.
- Added campaign state fields for prompt-guidance operating principle, lightweight default lane, optional native Subagents backend, and no legacy multi-agent baseline.

## Verification

- `rg -n "codex_multiagent|Codex Multi-Agent|conservative safety baseline|MultiAgentV2|Subagents|gpt-5.5" .`: passed; active references are legacy/reference, no active baseline wording.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed.
- `python scripts/check_external_validation_readiness.py --root . --format json`: passed, status `ready`.
- `python -m unittest discover -s tests -p "test_project_registry.py"`: passed, 4 tests after sandbox escalation.
- `python -m unittest discover -s tests -p "test_external_validation_readiness.py"`: passed, 4 tests after sandbox escalation.
- `git diff --check`: passed with existing line-ending warnings only.
- `node bin/selfdex.js --help`: passed.
- `node bin/selfdex.js install --dry-run`: passed.
- `npm.cmd pack --dry-run --json`: passed.
- `npm.cmd publish --access public --dry-run`: passed; no package was published.

## Result

Selfdex no longer presents `codex_multiagent` as its active baseline. The public
runtime story is now lightweight, GPT-5.5 prompt-guided, approval-gated, and
optionally backed by Codex native Subagents only when the work actually splits.

## Next Candidate

- After user approval, proceed to the separate npm publish step.
