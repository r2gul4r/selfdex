# Autopilot Policy

Selfdex runs as a supervised, bounded, and auditable local improvement loop for
Codex work.

## Final Goal Contract

`docs/SELFDEX_FINAL_GOAL.md` is the north-star contract. It defines Selfdex as
a user-invoked control harness for long-running Codex sessions:

```text
register projects -> understand direction -> scan -> ask -> classify -> rank -> freeze -> orchestrate -> implement -> verify -> record -> repeat
```

The loop may analyze explicitly registered projects read-only, but
cross-project writes stay approval-gated. External read-only validation is
required before treating Selfdex as generally useful beyond this repository.

## Loop

1. Infer the project direction: purpose, audience, product signals,
   constraints, and strategic opportunities.
2. Scan repository signals.
3. Ask the Socratic evaluation questions for non-trivial candidates.
4. Classify each candidate as repair, hardening, improvement, capability, or
   automation.
5. Rank direction opportunities first, then hygiene gaps, by strategic fit,
   user value, novelty, feasibility, evidence, risk, reversibility, and
   verification fit.
6. Pick the smallest high-leverage task.
7. Freeze acceptance, non-goals, write sets, and checks.
8. Recommend or use explorer, worker, and reviewer lanes when host policy,
   authorization, and budget allow it.
9. For approved target projects, run one candidate through a target-project
   Codex session on a new branch.
10. Integrate outputs.
11. Verify.
12. Repair inside the same contract when checks fail.
13. Record the run under `runs/<project_key>/` and advance the campaign queue.

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

## Control Knobs

- `risk_appetite`: `medium-high` by default, bounded by hard approval zones.
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

Folder-wide approval can allow Selfdex to run Codex inside a registered target
folder, but it does not bypass the hard approval zones above.

## Candidate Selection

Prefer candidates that:

- move the project toward a clearer product or technical direction
- reveal a better next feature, workflow, or capability the user may not have
  explicitly requested
- directly improve the audit-and-control loop
- add missing capability needed for supervised long-running Codex work
- reduce verification blind spots
- shrink future handoff cost
- add missing tests for core scripts
- make planning and run records more machine-readable

Defer candidates that:

- require unclear external authority
- cannot be verified locally
- need broad architecture changes before value is proven
- overlap active write locks

## External Validation

Selfdex should not claim general autonomous engineering ability from internal
self-improvement alone. The next proof point is read-only validation on 2-3
external repositories registered in `PROJECT_REGISTRY.md`. A candidate is useful
only when a human reviewer agrees it describes a real problem, has user value,
is small enough to freeze, can be verified locally, and is low-risk to reverse.

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

Target-project execution records are grouped by project:

```text
runs/<project_key>/YYYYMMDD-HHMMSS-<slug>.md
```
