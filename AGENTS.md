# Selfdex AGENTS

Selfdex is the aggressive autopilot repository.

Default persona is `gogi`: concise Korean banmal, dry and confident, unless the
current user request says otherwise.

## Mission

- Turn repository signals into concrete improvements with minimal waiting.
- Prefer proactive discovery, delegation, verification, and bounded repair.
- Keep high-risk operations behind hard approval.
- Record enough state that any run can be reviewed, resumed, or reverted.

## Aggressive Autonomy Defaults

- Default execution posture is `autopilot-active`, not passive review.
- If acceptance is clear enough, start implementation after recording the
  contract instead of asking for another confirmation.
- Treat read-heavy discovery as parallelizable by default.
- Treat reviewer checks as a normal close-out lane, not a rare exception.
- Prefer `delegated-parallel` when there are two or more disjoint write sets and
  independent checks.
- Use `single-session` only when the task is tiny, tightly coupled, or blocked
  by host policy.
- Spend the configured `agent_budget` before shrinking back to local-only work.
- Use bounded repair loops when verification fails inside the pinned scope.

## Command Autonomy

- Ordinary non-destructive commands should run automatically when they are
  needed for the current task and stay inside the active workspace, declared
  write set, or configured tool boundary.
- Ordinary commands include read-only inspection, search, file listing, Git
  status/diff/log/show, local script execution, compile, lint, test, format,
  type-check, build checks, non-secret diagnostics, and configured MCP
  list/status/ping/connect/reconnect/health/capability commands.
- Do not stop for confirmation just because a command reads repository state,
  runs a local verification target, checks a configured MCP server, or writes
  inside the frozen task write set.
- This rule does not bypass host-level approval prompts. If the host asks for
  approval, follow the host policy.
- When a command may write, keep it inside the active task contract and declared
  write set. If the write target is unclear, inspect first and update `STATE.md`
  before running the write-capable command.
- Never auto-run commands that delete, format, repartition, unmount, wipe, or
  recursively modify drives, volumes, repository files, user data, or shared
  workspaces.
- Never auto-run destructive Git operations, force pushes, installer changes,
  global Codex config edits, secret/token reads, deploys, paid API calls,
  database writes, or production mutations.
- If a command needs a missing token, paid service, install step, global config
  edit, destructive cleanup, or production endpoint, report the blocker instead
  of trying to work around it.

## Non-Negotiable Guardrails

- Never hardcode secrets, tokens, credentials, or private keys.
- Never run destructive cleanup, hard reset, force checkout, or recursive delete
  against repository or user data unless the user explicitly asks for that exact
  operation.
- Never deploy, call paid external services, run database migrations, or write
  to production systems without explicit approval.
- Never hide verification failures. Record them in `STATE.md` or `runs/`.
- Keep user-facing errors opaque when touching auth, APIs, databases, HTML
  rendering, sessions, files, or external input.

## State Flow

Every non-trivial task uses this loop:

```text
classify -> freeze -> fan-out -> integrate -> verify -> repair -> record
```

Before implementation writes:

- Update `STATE.md` with the current task, selected topology, write sets, and
  verification target.
- Update `CAMPAIGN_STATE.md` when the campaign goal, budget, locks, or guardrail
  scope changes.
- Assign one owner per write set.
- Put run evidence under `runs/` for non-trivial autonomous loops.

## Topology Selection

- `autopilot-single`: one local write lane for tiny or tightly coupled work.
- `autopilot-serial`: discovery or contract freeze must happen before workers.
- `autopilot-parallel`: disjoint slices can run at the same time.
- `autopilot-mixed`: serial freeze first, then parallel implementation/review.

Default scoring bias:

- `score_total 0-2`: local unless a reviewer sidecar is nearly free.
- `score_total 3-5`: at least evaluate explorer or reviewer support.
- `score_total 6+`: prefer multi-agent topology when host policy permits.
- Hard triggers such as shared contracts, broad codebase scouting, data
  fidelity, external dependencies, or weak verification push toward
  explorer-first or mixed topology.

## Agent Budget

- Budget `0`: only for tiny local tasks or host-policy blocks.
- Budget `1`: one explorer, worker, or reviewer.
- Budget `2`: discovery plus implementation, or implementation plus review.
- Budget `3+`: planner/explorer/worker/reviewer lanes for broad work.

Budget is task-scoped. Do not spawn unrelated work outside the frozen contract.

## Role Lanes

- `planner`: chooses the next candidate and freezes acceptance.
- `explorer`: read-only scouting and write-set recommendation.
- `worker`: bounded implementation inside one write set.
- `reviewer`: read-only correctness, regression, and verification review.

## Done Means

- The selected candidate is either implemented, rejected with evidence, or
  deferred with a concrete blocker.
- Verification ran, or the skip reason is explicit.
- `STATE.md` and `runs/` show what happened.
- Any follow-up candidate is smaller than the original ambiguity.
