# Autopilot Policy

Selfdex runs as an aggressive but bounded improvement loop.

## Loop

1. Scan repository signals.
2. Rank gaps by goal fit, leverage, risk, and reversibility.
3. Pick the smallest high-leverage task.
4. Freeze acceptance, non-goals, write sets, and checks.
5. Fan out to agents when host policy and budget allow it.
6. Integrate outputs.
7. Verify.
8. Repair inside the same contract when checks fail.
9. Record the run.

## Campaign State

`CAMPAIGN_STATE.md` owns long-running intent:

- campaign goal
- risk appetite
- agent budget policy
- hard approval zones
- current locks
- latest run summary
- next candidate queue

`STATE.md` owns the current task only.

## Aggression Knobs

- `risk_appetite`: `medium-high` by default.
- `default_agent_budget`: `2`.
- `max_agent_budget`: `4`.
- `repair_attempts`: `2`.
- `review_default`: `on`.
- `explorer_default`: `on` for broad or uncertain work.
- `parallel_default`: `on` when write sets are disjoint.

## Approval Gates

The autopilot must stop for explicit approval before:

- destructive filesystem or Git history operations
- secrets or credential access
- paid API calls
- public deploys
- database migrations or production writes
- cross-workspace changes

## Candidate Selection

Prefer candidates that:

- directly improve the autonomous loop
- reduce verification blind spots
- shrink future handoff cost
- add missing tests for core scripts
- make planning and run records more machine-readable

Defer candidates that:

- require unclear external authority
- cannot be verified locally
- need broad architecture changes before value is proven
- overlap active write locks

## Run Record

Each non-trivial run should write a compact markdown note under `runs/`:

```text
runs/YYYYMMDD-HHMMSS-<slug>.md
```

Minimum fields:

- goal
- selected candidate
- topology
- agent budget used
- write sets
- verification
- repair attempts
- result
- next candidate
