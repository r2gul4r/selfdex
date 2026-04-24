# Selfdex Final Goal

Selfdex is a bounded recursive improvement harness for Codex.

Its final goal is to make Codex better than the default request-response loop by
adding a durable improvement cycle:

```text
register projects -> scan -> ask -> classify -> rank -> freeze -> orchestrate -> implement -> verify -> record -> repeat
```

Selfdex should inspect itself first, then any explicitly registered projects,
and turn repository signals into concrete improvements without losing safety,
traceability, or user control.

## Operating Contract

- Selfdex is user-invoked, not a background daemon.
- Cross-project analysis starts read-only through a project registry.
- Cross-project writes require explicit approval for the target project and task.
- Destructive commands, secrets, paid APIs, deploys, database writes, and
  production changes remain hard approval zones.
- Subagents are an orchestration tool, not a goal. Use them when write sets,
  discovery lanes, or reviewer checks are disjoint enough to beat handoff cost.
- Every non-trivial run leaves evidence in `STATE.md`, `CAMPAIGN_STATE.md`, and
  eventually `runs/YYYYMMDD-HHMMSS-<slug>.md`.

## Improvement Types

Selfdex must distinguish fixing from improving:

| work_type | Meaning | Example |
| :-- | :-- | :-- |
| `repair` | Restore broken behavior | Fix failing tests or broken fallback |
| `hardening` | Make existing behavior harder to break | Add unit tests or edge-case checks |
| `improvement` | Improve quality without changing capability | Refactor a hotspot or reduce duplication |
| `capability` | Add a new system ability | Add project registry or run recorder |
| `automation` | Automate repeated coordination work | Generate run records or refresh queues |

The planner should show this type for each candidate so the loop does not look
like it only "fixes" things.

## Socratic Evaluation

Before implementation, Selfdex should ask a compact set of questions:

1. What is the current goal, and does this candidate directly serve it?
2. Is this a repair, hardening, improvement, capability, or automation task?
3. What evidence proves the issue or opportunity is real?
4. What is the smallest useful scope?
5. What are the non-goals and hard approval boundaries?
6. Can the work be verified locally?
7. Can explorer, worker, or reviewer lanes run independently?
8. What should be recorded so the next loop can continue?

These questions are a decision aid, not a ritual. If a task is tiny, answer them
briefly in `STATE.md`.

## Roadmap

### Phase 1 - Self Loop Foundation

Goal: make Selfdex able to improve this repository safely.

- Run recorder writes compact files under `runs/`.
- Planner candidates include `work_type`.
- Candidate extractors have fixture-based tests.
- Campaign budget checker rejects out-of-contract work.
- Generated report drift checks protect docs and metrics.

### Phase 2 - Project Registry And Read-Only Analysis

Goal: let Selfdex inspect all explicitly registered local projects without
writing to them.

- Add `PROJECT_REGISTRY.md` or a machine-readable equivalent.
- Record project path, role, verification commands, and write policy.
- Scan registered projects read-only.
- Produce cross-project improvement candidates with source project and evidence.
- Keep cross-project writes disabled by default.

### Phase 3 - Socratic Planner

Goal: turn raw candidates into better decisions.

- Add a Socratic evaluator module.
- Attach answers, evidence, risk, and verification fit to each candidate.
- Separate `repair`, `hardening`, `improvement`, `capability`, and `automation`.
- Rank by campaign fit, leverage, risk, reversibility, and verification strength.

### Phase 4 - Orchestration Engine

Goal: use subagents when they genuinely reduce risk or time.

- Decide topology from write-set separability and verification independence.
- Support explorer-first, worker, and reviewer lanes.
- Keep one owner per write set.
- Record spawn decision, budget, and outcome.
- Avoid delegation when the next step is a single blocking discovery result.

### Phase 5 - Recursive Improvement Loop

Goal: complete one improvement and naturally select the next.

- Consume completed campaign queue items.
- Write run records automatically.
- Run bounded repair when verification fails.
- Update `CAMPAIGN_STATE.md` with result and next candidate.
- Keep improvements small enough to review and revert.

## Current North Star

Selfdex should become a local, auditable improvement operator:

```text
It reads the registered workspaces, asks useful questions, picks the highest
leverage safe improvement, orchestrates the work, verifies it, records evidence,
and advances to the next candidate without pretending it has unsafe authority.
```

