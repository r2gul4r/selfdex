# Run 20260424-161000-mcp-connection-autonomy

- goal: Allow ordinary MCP server connection commands to run automatically while preserving dangerous-command guardrails
- selected_candidate: mcp connection command auto-run policy
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Added narrow MCP connection autonomy policy to AGENTS.md; ordinary MCP connection/status diagnostics can auto-run while dangerous operations remain gated.
- next_candidate: scripts/plan_next_task.py 책임 분리와 경계 정리

## Write Sets

- AGENTS.md
- CAMPAIGN_STATE.md
- STATE.md

## Verification

- campaign budget check: passed; violation_count=0
- doc drift check: passed; finding_count=0
- git diff --check: passed
