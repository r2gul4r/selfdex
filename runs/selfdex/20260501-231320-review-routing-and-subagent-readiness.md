# Run 20260501-231320-review-routing-and-subagent-readiness

- project_key: selfdex
- goal: Separate GPT Pro / ChatGPT Apps direction review from Codex code review and harden official subagent readiness.
- selected_candidate: review-routing-and-subagent-readiness
- agents_used: main, reviewer
- subagent_permission: @selfdex permits official Codex subagents when useful; hard approval zones remain separate.
- repair_attempts: 1
- result: implemented and locally verified
- next_candidate: scripts/check_campaign_budget.py responsibility split

## Write Sets

- docs and skills: direction review vs code review routing
- scripts/tests: docs_researcher planner path, setup doctor .codex validation, commit-gate mirror warning block

## Verification

- focused unittest: pass, 30 tests
- full unittest discover: pass, 223 tests
- plugin/doc/campaign checks: pass
- npm pack --dry-run --json: pass
- reviewer subagent: P0/P1 none; P2 findings fixed
