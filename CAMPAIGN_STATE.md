# Campaign State

## Campaign

- name: `selfdex-bootstrap`
- goal: `Build a bounded recursive improvement harness that can register projects, scan, ask Socratic questions, classify work, rank candidates, orchestrate agents when useful, implement, verify, record, and repeat.`
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

none

## Completed Queue Items

- Add real unit tests for `scripts/plan_next_task.py`.
- Add `work_type` classification to planner candidates.
- Add a Socratic evaluator for candidate decisions.
- Add a run recorder that writes `runs/YYYYMMDD-HHMMSS-<slug>.md`.
- Add a project registry for read-only multi-project analysis.
- Add an orchestration planner that records spawn decisions and write sets.
- Add fixture-based tests for candidate extractors.
- Add a campaign budget checker that rejects out-of-contract work.
- Add generated report drift checks for Selfdex docs.
- Clean stale verification entrypoints and document the quality signal sample payload.
- Add MCP connection autonomy rules for ordinary server connection commands.
- Broaden command autonomy to all ordinary non-destructive workflow commands.
- Split planner orchestration-fit heuristics out of `scripts/plan_next_task.py`.
- Split file metric models and line analysis out of `scripts/collect_repo_metrics.py`.
- Add a dependency-free coverage signal check path to repository verification.
- Add an integration test for test-gap extraction feeding planner selection.
- Suppress feature-gap detector stopword self-reference false positives.
- Add external validation readiness reporting for 2-3 read-only project registration.
- Register three existing sibling repositories as external read-only validation targets.
- Add shared generated/dependency directory exclusions before external read-only scans.
- Add external read-only candidate snapshot generation and binary-safe metric scanning.
- Support candidate quality templates generated from external read-only snapshots.
- Mark external validation reports with unscored candidates as needing scoring.
- Exclude lockfiles and Codex backup artifacts from refactor candidate snapshots.
- Make external candidate snapshots support explicit user-selected repository scopes.
- Add read-only external project planning with a Codex execution prompt.

## Latest Run

- status: `external-project-readonly-plan`
- summary: `Added a read-only planning command that selects one external project candidate, freezes a proposed task contract, emits a Codex execution prompt, and can record the plan under runs/.`
