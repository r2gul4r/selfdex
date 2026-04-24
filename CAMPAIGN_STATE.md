# Campaign State

## Campaign

- name: `selfdex-bootstrap`
- goal: `Build an aggressive autonomous Codex improvement harness that can scan, rank, plan, implement, verify, repair, and record repository improvements.`
- risk_appetite: `medium-high`
- default_agent_budget: `2`
- max_agent_budget: `4`
- repair_attempts: `2`
- review_default: `on`
- explorer_default: `on`
- parallel_default: `on_when_disjoint`

## Hard Approval Zones

- destructive Git or filesystem operations
- secrets, credentials, private keys, or token access
- paid API calls
- public deployment
- database migration or production write
- cross-workspace edits

## Current Locks

- none

## Candidate Queue

- Add real unit tests for `scripts/plan_next_task.py`.
- Add fixture-based tests for candidate extractors.
- Add generated report drift checks for Selfdex docs.
- Add a run recorder that writes `runs/YYYYMMDD-HHMMSS-<slug>.md`.
- Add a campaign budget checker that rejects out-of-contract work.

## Latest Run

- status: `bootstrap`
- summary: `Initial aggressive autopilot scaffold created from codex_multiagent analysis assets.`
