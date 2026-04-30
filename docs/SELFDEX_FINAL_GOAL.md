# Selfdex Final Goal

Selfdex is a bounded, auditable local control harness for long-running Codex
work.

Its final goal is to make Codex work more controllable than the default
request-response loop by adding a durable supervised improvement cycle:

```text
register projects -> scan -> ask -> classify -> rank -> freeze -> orchestrate -> implement -> verify -> record -> repeat
```

Selfdex should inspect itself first, then explicitly registered projects
read-only, and turn repository signals into concrete, reviewable work without
losing safety, traceability, or user control. It is not yet proven as a general
autonomous engineer; that claim requires external read-only validation.

The intended end state is still active, supervised development: given a target
project and a goal, Selfdex should inspect the repository, rank small useful
tasks, freeze one contract, produce a Codex/GPT execution prompt, execute only
after approval on an isolated branch, verify, attempt bounded repair, produce a
patch or PR-ready summary, and record evidence under `runs/<project_key>/`.

## Operating Contract

- Selfdex is user-invoked, not a background daemon.
- Cross-project analysis starts read-only through a project registry.
- Cross-project writes require explicit approval for the target project. One
  automated loop runs one selected task at a time on a new branch.
- Destructive commands, secrets, paid APIs, deploys, database writes, and
  production changes remain hard approval zones.
- Subagents are an orchestration decision-support tool, not a goal. Use them
  only when host support, task authority, write sets, discovery lanes, or
  reviewer checks make delegation safer or faster than local work.
- Every non-trivial run leaves evidence in `STATE.md`, `CAMPAIGN_STATE.md`, and
  eventually `runs/<project_key>/YYYYMMDD-HHMMSS-<slug>.md`.

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

Goal: prove external value by inspecting explicitly registered local projects
without writing to them.

- Add `PROJECT_REGISTRY.md` or a machine-readable equivalent.
- Record project path, role, verification commands, and write policy.
- Register 2-3 external repositories read-only before any cross-project write
  work is considered.
- Produce top candidates for each external project with source project and
  evidence.
- Manually score those candidates with `docs/CANDIDATE_QUALITY_RUBRIC.md` for
  whether they are real, valuable, small, locally verifiable, and low-risk.
- Treat human agreement on those criteria as the proof point for external
  usefulness.
- Keep cross-project writes disabled by default.

### Phase 2.5 - External Project Read-Only Planning

Goal: turn a selected external project candidate into a Codex-ready task
contract without modifying the target project.

- Accept either a registered `project_id` or an ad-hoc `project_root`.
- Scan the target project read-only and select one candidate.
- Emit a task contract with rationale, likely inspect files, proposed future
  write boundary, verification commands, risk level, approval requirement, and
  a Codex execution prompt.
- Optionally record the planning artifact under `runs/` in the Selfdex
  repository.
- Treat the output as the handoff into the future write-enabled stage, not as
  permission to edit the target project.

The next stage after this is supervised modification:

```text
read-only plan -> folder approval -> isolated branch -> bounded patch -> verification -> bounded repair -> PR-ready summary -> runs/<project_key>/ evidence
```

### Phase 3 - Socratic Planner

Goal: turn raw candidates into better decisions.

- Add a Socratic evaluator module.
- Attach answers, evidence, risk, and verification fit to each candidate.
- Separate `repair`, `hardening`, `improvement`, `capability`, and `automation`.
- Rank by campaign fit, leverage, human candidate quality, risk, reversibility,
  and verification strength.

### Phase 4 - Orchestration Engine

Goal: support honest orchestration decisions and host-supported delegation when
they genuinely reduce risk or time.

- Decide topology from write-set separability and verification independence.
- Support explorer-first, worker, and reviewer lane recommendations, and execute
  them only when the host Codex environment and task authority allow it.
- Keep one owner per write set.
- Record spawn decision, budget, and outcome.
- Avoid delegation when the next step is a single blocking discovery result.

### Phase 5 - Recursive Improvement Loop

Goal: complete one bounded improvement and naturally select the next supervised
task.

- Consume completed campaign queue items.
- Write run records automatically.
- Run bounded repair when verification fails.
- Update `CAMPAIGN_STATE.md` with result and next candidate.
- Keep improvements small enough to review and revert.
- Keep multi-project evidence separated by project key under `runs/`.

## Current North Star

Selfdex should become a bounded, auditable local control harness:

```text
It reads the registered workspaces, asks useful questions, picks the highest
leverage safe task, freezes boundaries, verifies the result, records evidence,
and makes the next session easy to resume without pretending it has unsafe or
unproven autonomy.
```
