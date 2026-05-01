# Selfdex Final Goal

Selfdex is a bounded, auditable command center for user-selected project
improvement work.

Its fixed final goal is to read a project the user selected, understand what
the project is trying to become, choose the next useful improvement,
evolution, or feature task, ask the user for approval, then safely delegate the
approved work to Codex and record the result.

```text
select project -> understand direction -> choose next work -> ask approval
-> freeze contract -> delegate to Codex safely -> verify -> record -> repeat
```

Selfdex should inspect itself first, then explicitly registered projects
read-only, and turn repository signals into concrete, reviewable work without
losing safety, traceability, or user control. It is not yet proven as a general
autonomous engineer; that claim requires external read-only validation.

Selfdex is not a repackaged multi-agent kit. It uses GPT-5.5 prompt guidance as
the operating discipline for clear roles, tool boundaries, success criteria,
stop conditions, verification, and compact evidence. Codex native Subagents are
an optional backend for separable work, not the default engine.

The intended end state is active, supervised development. Given a target
project, Selfdex should infer the project's direction, suggest better next
moves even when the user did not name them, rank small useful tasks, freeze one
contract, produce a Codex execution prompt, execute only after approval on an
isolated branch, verify, attempt bounded repair, produce a patch or PR-ready
summary, and record evidence under `runs/<project_key>/`.

## Role Split

- GPT / Pro extended mode is for high-level direction only: product direction,
  milestones, roadmap decisions, and strategic priority. It is not called
  automatically for every task.
- Selfdex translates direction into bounded work. It reads the selected project
  read-only first, extracts candidates, chooses exactly one small safe
  high-leverage task, freezes the contract, asks for approval before
  target-project writes, and records the result.
- Codex implements and verifies. It reads files, edits code, runs checks,
  debugs failures, reviews diffs, and repairs implementation issues without
  silently redefining project direction.

GPT direction review is recommended only when project goals conflict, all
candidates are strategically ambiguous, feature priority cannot be decided from
code evidence, a milestone or product direction needs reset, a major surface
such as ChatGPT Apps, MCP, public UI, or automation loop is being considered,
or the user explicitly asks for product or strategy review.

Do not use GPT direction review for routine coding, tests, refactors, bug
fixes, documentation drift, or diff review. Those stay inside Selfdex/Codex
execution unless they become product-direction questions.

## Model Usage Rules

- Fast exploration and lightweight scans: mini or medium.
- Candidate evaluation and contract freeze: `gpt-5.5` high.
- Complex architecture, risky changes, security, permissions, and broad
  refactors: `gpt-5.5` xhigh.
- Routine implementation: medium or high.
- Final code review, large diff review, and security-sensitive review:
  `gpt-5.5` xhigh.
- Product direction, milestone, and strategic priority: GPT / Pro extended
  mode only when the user approves or calls it.

These rules describe routing discipline. They do not authorize automatic GPT
Pro extended calls. For routine work, first improve prompt shape, tool
instructions, output contracts, and verification before increasing effort.

## Runtime Model

- Default lane: lightweight `single-session` for small documentation, test,
  local policy, or narrow implementation tasks.
- Bounded lane: `single-session` with frozen state contract for non-trivial but
  tightly coupled implementation.
- Optional backend: Codex native Subagents/MultiAgentV2 when read-only
  exploration, implementation, or review can be split cleanly and verified
  independently.
- No legacy baseline: historical `codex_multiagent` validation artifacts may be
  cited as reference evidence, but `codex_multiagent` is not the active Selfdex
  baseline or proof set.

## Operating Contract

- Selfdex is user-invoked, not a background daemon.
- Cross-project analysis starts read-only through a project registry.
- Cross-project writes require explicit approval for the target project. One
  automated loop runs one selected task at a time on a new branch.
- Destructive commands, secrets, paid APIs, deploys, database writes, and
  production changes remain hard approval zones.
- Subagents are an orchestration decision-support tool, not a goal. Use them
  only when host support, task authority, write sets, discovery lanes, reviewer
  checks, and verification independence make delegation safer or faster than
  local work.
- Machine-readable safety contracts live in `STATE.json` and
  `CAMPAIGN_STATE.json`; `STATE.md` and `CAMPAIGN_STATE.md` remain
  human-readable mirrors for review.
- If JSON and markdown mirrors differ, Selfdex must surface a warning and
  treat JSON as the source of truth for safety-critical checks.
- Every non-trivial run leaves evidence in the state files and eventually
  `runs/<project_key>/YYYYMMDD-HHMMSS-<slug>.md`.

## Improvement Types

Selfdex must distinguish fixing from improving:

| work_type | Meaning | Example |
| :-- | :-- | :-- |
| `repair` | Restore broken behavior | Fix failing tests or broken fallback |
| `hardening` | Make existing behavior harder to break | Add unit tests or edge-case checks |
| `improvement` | Improve quality without changing capability | Refactor a hotspot or reduce duplication |
| `capability` | Add a new system ability | Add project registry or run recorder |
| `automation` | Automate repeated coordination work | Generate run records or refresh queues |
| `direction` | Improve the project trajectory | Propose a new user workflow, product feedback loop, or strategy-backed capability |

The planner should show this type for each candidate so the loop does not look
like it only "fixes" things. Direction candidates should be evidence-backed,
small enough for one first step, and reversible.

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
- Maintain active external validation targets read-only before any cross-project
  write work is considered. The current active set excludes legacy
  `codex_multiagent` evidence and uses the remaining registered targets as the
  live proof set.
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
- Infer the project purpose, audience, product signals, constraints, and
  strategic opportunities before routine hygiene ranking.
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

### Phase 2.6 - Read-Only Control Surface

Goal: expose only the safe first app surface before any write-capable app or MCP
automation exists.

- Show registered projects.
- Show the next recommended task.
- Show latest run records.
- Show approval status.
- Do not expose target-project writes, branch creation, target Codex execution,
  secrets, deploys, paid APIs, databases, production writes, installer changes,
  or global config changes.

### Phase 2.7 - Project-Session Invocation

Goal: make Selfdex easy to call from the project session where the user is
already working.

- Package a repo-local Codex plugin named `selfdex`.
- After installation or enabling, allow `@selfdex` from a target project
  session.
- Treat the current session cwd as the selected project unless the user names
  another path.
- Route through Selfdex read-only planning before asking for approval.
- Keep plugin installation, global config edits, and write-capable target
  execution as explicit approval steps.
- Provide an npm-compatible installer entrypoint so the intended published
  command is `npx selfdex install`. The npm package must only bootstrap
  Selfdex and the local plugin; `npm publish`, package-name verification, and
  npm credentials remain separate approval-gated setup steps.
- Provide a true one-line bootstrap installer:
  `powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/r2gul4r/selfdex/main/install.ps1)))"`.
  It must clone or update Selfdex, then install the home-local plugin. The
  clone-first plugin installer remains available as
  `python scripts/install_selfdex_plugin.py --root . --yes --format markdown`.

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
- Support explorer-first, worker, and reviewer lane recommendations through
  Codex native Subagents, and execute them only when the host environment, task
  authority, ownership, and verification split allow it.
- Keep one owner per write set.
- Record spawn decision, budget, and outcome.
- Avoid delegation when the next step is a single blocking discovery result.

### Phase 5 - Recursive Improvement Loop

Goal: complete one bounded improvement and naturally select the next supervised
task.

- Consume completed campaign queue items.
- Write run records automatically.
- Run bounded repair when verification fails.
- After approved commit/push steps, read GitHub Actions status directly instead
  of routing CI feedback through Gmail.
- Update `CAMPAIGN_STATE.md` with result and next candidate.
- Keep improvements small enough to review and revert.
- Keep multi-project evidence separated by project key under `runs/`.

## Current North Star

Selfdex should become a bounded, auditable local command center:

```text
It reads the project the user chose, decides the next useful improvement,
evolution, or feature task, asks approval, sends only approved bounded work to
Codex, verifies the result, records evidence, and makes the next session easy
to resume without pretending it has unsafe or unproven autonomy.
```
