# Autopilot Policy

Selfdex runs as a supervised, bounded, and auditable local improvement loop for
Codex work.

## Final Goal Contract

`docs/SELFDEX_FINAL_GOAL.md` is the north-star contract. It defines Selfdex as
a user-invoked command center for supervised Codex work on a selected project:

```text
select project -> understand direction -> choose next work -> ask approval -> freeze -> delegate to Codex -> review -> verify -> commit gate -> record -> repeat
```

The loop may analyze explicitly registered projects read-only, but
cross-project writes stay approval-gated. External read-only validation is
required before treating Selfdex as generally useful beyond this repository.

Selfdex is not based on the old `codex_multiagent` kit or the earlier local
topology scoring layer. Historical `codex_multiagent` validation records remain
useful as legacy evidence, but the active runtime model is GPT-5.5
prompt-guided coordination with official Codex native Subagents/MultiAgentV2.

## Role Split And Model Use

- GPT / Pro extended mode decides what is worth doing only at the product,
  milestone, roadmap, and priority level. Selfdex may recommend this review,
  but the user must explicitly approve or call it. When `@chatgpt-apps` is
  available, Selfdex treats it as the product/app direction-review surface for
  project purpose, improvement ideas, and additional feature opportunities.
- Selfdex coordinates the loop: read-only discovery, candidate extraction,
  one-task selection, contract freeze, approval management, run records, and
  autonomy limits.
- Codex decides how to implement safely: file edits, tests, debugging, diff
  review, and bounded repairs. Code review is handled by the Codex native
  `reviewer` subagent, not by the product-direction review path.

Use GPT direction review only when goals conflict, candidates are strategically
ambiguous, code evidence cannot decide feature priority, product direction must
reset, a major surface such as ChatGPT Apps, MCP, public UI, or automation loop
is being considered, or the user asks for strategy review. Do not use it for
routine coding, tests, refactors, bug fixes, documentation drift, or diff
review.

Model routing:

- Fast exploration / lightweight scans: mini or medium.
- Candidate evaluation / contract freeze: `gpt-5.5` high.
- Complex architecture / risky changes / security / permissions / broad
  refactors: `gpt-5.5` xhigh.
- Routine implementation: medium or high.
- Final code review / large diff review / security-sensitive review:
  `gpt-5.5` xhigh.
- Product direction / milestone / strategic priority: GPT / Pro extended mode,
  only when user-approved.

GPT-5.5 prompt guidance is an operating principle, not an automatic model call.
Prefer clear role boundaries, tool guidance, success criteria, stop conditions,
and verification commands before increasing reasoning effort.

## Codex Native Subagents

Calling `@selfdex` is explicit permission for Selfdex to recommend and use
official Codex native Subagents/MultiAgentV2 when useful.

- The main agent owns requirements, task choice, approval boundaries,
  integration, final reporting, and run records.
- `explorer` is read-only and maps code paths, evidence, contracts, risks, and
  candidate write boundaries.
- `docs_researcher` is read-only and checks official docs or API behavior.
- `worker` owns one frozen write boundary and must stop if the boundary expands
  or overlaps another write owner.
- `reviewer` is read-only and checks correctness, regressions, security, and
  missing tests.

Use subagents when noisy exploration, tests, logs, docs, implementation slices,
or review can run independently and return concise summaries. Keep tightly
coupled integration in the main agent. Do not reintroduce local topology labels,
task scoring totals, or local agent budget knobs as active runtime controls.

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
7. Freeze acceptance, non-goals, write sets, and checks in the structured
   state contract.
8. Use official Codex subagents when host policy, `@selfdex` permission,
   disjoint ownership, and verification independence make them useful.
9. For approved target projects, run one candidate through a target-project
   Codex session on a new branch.
10. Integrate outputs.
11. Verify.
12. Repair inside the same contract when checks fail.
13. If commit closeout is requested or project policy enables it, run the
    commit gate before leaving the task.
14. Commit only after review, verification, write-boundary, hard-approval, and
    Conventional Commit checks pass.
15. Push only when the user requested push or project policy enables it, then
    check GitHub Actions.
16. Record the run under `runs/<project_key>/` and advance the campaign queue
    only after commit/push/CI evidence is closed or the task is explicitly
    blocked.

## Campaign State

`CAMPAIGN_STATE.json` owns machine-readable long-running intent, and
`CAMPAIGN_STATE.md` mirrors it for human review:

- campaign goal
- risk appetite
- official subagent permission policy
- hard approval zones
- current locks
- latest run summary
- next candidate queue

`STATE.json` owns the current machine-readable task contract.
`STATE.md` mirrors the current task for review and continuity.

## Control Knobs

- `risk_appetite`: `medium-high` by default, bounded by hard approval zones.
- `subagent_runtime`: `official_codex_native_subagents`.
- `max_subagent_threads`: `6`, matching the project-scoped Codex config unless
  the user explicitly changes it.
- `subagent_depth`: `1`, avoiding recursive delegation unless explicitly
  requested.
- `repair_attempts`: `2`.
- `review_default`: `non_trivial_implementation_only`.
- `direction_review_default`: `recommend_and_wait_for_user_approval`.
- `explorer_default`: `on_after_selfdex_invocation`.
- `parallel_default`: `on_when_subtasks_are_independent`.

## Approval Gates

The autopilot must stop for explicit approval before:

- destructive filesystem or Git history operations
- secrets or credential access
- paid API calls
- public deploys
- database migrations or production writes
- cross-workspace changes
- commit or push closeout unless the user requested it or the active project
  policy enables it for the current task

Folder-wide approval can allow Selfdex to run Codex inside a registered target
folder, but it does not bypass the hard approval zones above.

## First App Surface

ChatGPT Apps and MCP surfaces start read-only. The first surface may expose only:

- registered projects
- next recommended task
- latest run records
- approval status

Write-capable target execution must remain hidden until explicitly approved.

## Project-Session Invocation

Selfdex may be packaged as a repo-local Codex plugin named `selfdex`. After a
separate install or enable step, a user can call it from a target project
session with `@selfdex`.

The plugin entrypoint must:

- treat the current session cwd as the selected target project by default
- treat `@selfdex` invocation as explicit permission to use official Codex
  native Subagents/MultiAgentV2 when useful
- locate the Selfdex command-center repo without editing global config
- run read-only planning before any target write
- ask for explicit approval before branch creation, target-project writes, or
  `run_target_codex.py --execute`
- record results under the Selfdex `runs/` tree

Creating or installing the plugin globally is a setup action and requires
explicit approval.

For cross-machine setup, the intended published npm command is:

```bash
npx selfdex install
```

The npm package must expose a `selfdex` binary and delegate to the bounded
bootstrap installer. Publishing, package-name verification, and npm credentials
are separate approval-gated setup steps. The installer still depends on
PowerShell, Git, and Python on the target machine.

Until the npm package is published, the one-line PowerShell bootstrap is:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/r2gul4r/selfdex/main/install.ps1)))"
```

The bootstrap clones or updates Selfdex and then runs the home-local plugin
installer. A cloned checkout may also run the plugin-only installer:

```bash
python scripts/install_selfdex_plugin.py --root . --yes --format markdown
```

The bootstrap supports `-DryRun`, `-InstallRoot`, `-RepoUrl`, and `-Branch`.
The plugin installer is dry-run by default unless `--yes` is passed. These
install paths may write only the selected Selfdex checkout, the home-local
plugin copy, and `.agents/plugins/marketplace.json`; target-project writes stay
behind normal approval.

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
self-improvement alone. The active proof point is read-only validation on the
currently registered external targets in `PROJECT_REGISTRY.md`, presently
`daboyeo` and `apex_analist`. Historical `codex_multiagent` reports remain
reference evidence only; they are no longer the active baseline for Selfdex
direction. A candidate is useful only when a human reviewer agrees it describes
a real problem, has user value, is small enough to freeze, can be verified
locally, and is low-risk to reverse.

## Run Record

Each non-trivial run should write a compact markdown note under `runs/`:

```text
runs/YYYYMMDD-HHMMSS-<slug>.md
```

Minimum fields:

- goal
- selected candidate
- official agent roles used
- subagent permission boundary
- write sets
- verification
- repair attempts
- result
- next candidate

## Commit Gate

Commit gate is the closeout stage after review and verification. It is not a
background loop and it is not unconditional auto-commit.

Before a commit, Selfdex must run:

```bash
python scripts/check_commit_gate.py --root . --commit-message "<type>: <summary>" --format json
```

The gate checks the active state contract, write boundary, reviewer result,
verification evidence, hard approval hints, and Conventional Commit message.
After push, Selfdex must use GitHub Actions status as the feedback source. A
pending or failing check keeps the task open for repair or blocked recording;
the next candidate is not selected until that evidence is closed.

Target-project execution records are grouped by project:

```text
runs/<project_key>/YYYYMMDD-HHMMSS-<slug>.md
```
