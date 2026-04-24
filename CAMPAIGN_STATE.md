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

## Latest Run

- status: `collect-metrics-utils-split`
- summary: `Extracted FileMetrics/GitHistory/DuplicateGroup models and line-analysis helpers from scripts/collect_repo_metrics.py into scripts/repo_metrics_utils.py, added helper plus direct/module CLI tests, fixed reviewer-found import-boundary risk, and advanced the next planner candidate to scripts/extract_refactor_candidates.py responsibility split.`
