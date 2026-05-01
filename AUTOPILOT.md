# Autopilot Policy

Selfdex runs as a supervised, bounded, and auditable local improvement loop for
Codex work.

## Final Goal Contract

`docs/SELFDEX_FINAL_GOAL.md` is the north-star contract. It defines Selfdex as
a user-invoked command center for supervised Codex work on a selected project:

```text
select project -> understand direction -> choose next work -> ask approval -> freeze -> delegate to Codex -> verify -> record -> repeat
```

The loop may analyze explicitly registered projects read-only, but
cross-project writes stay approval-gated. External read-only validation is
required before treating Selfdex as generally useful beyond this repository.

Selfdex is not based on the old `codex_multiagent` kit. Historical
`codex_multiagent` validation records remain useful as legacy evidence, but the
active runtime model is GPT-5.5 prompt-guided coordination with Codex native
Subagents available only as an optional execution backend.

## Role Split And Model Use

- GPT / Pro extended mode decides what is worth doing only at the product,
  milestone, roadmap, and priority level. Selfdex may recommend this review,
  but the user must explicitly approve or call it.
- Selfdex coordinates the loop: read-only discovery, candidate extraction,
  one-task selection, contract freeze, approval management, run records, and
  autonomy limits.
- Codex decides how to implement safely: file edits, tests, debugging, diff
  review, and bounded repairs.

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

## Runtime Lanes

Use the lightest lane that can finish the approved task safely:

- `lightweight-single`: small documentation, test, local policy, or narrow code
  changes. Use one Codex lane, focused checks, and no GPT direction review.
- `bounded-single`: non-trivial but tightly coupled implementation. Freeze the
  contract, keep one writer, verify locally, and record evidence.
- `native-subagents`: use Codex native Subagents only when explorer, worker, or
  reviewer lanes can run independently with disjoint ownership or read-only
  scope, and the expected parallel or review gain is higher than handoff cost.

Do not use Subagents just because the task score is high. High score means
evaluate risk and evidence depth; it does not make multi-agent execution the
default.

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
8. Recommend or use explorer, worker, and reviewer lanes only when host policy,
   authorization, budget, disjoint ownership, and verification independence make
   them useful.
9. For approved target projects, run one candidate through a target-project
   Codex session on a new branch.
10. Integrate outputs.
11. Verify.
12. Repair inside the same contract when checks fail.
13. Record the run under `runs/<project_key>/` and advance the campaign queue.

## Campaign State

`CAMPAIGN_STATE.json` owns machine-readable long-running intent, and
`CAMPAIGN_STATE.md` mirrors it for human review:

- campaign goal
- risk appetite
- agent budget policy
- hard approval zones
- current locks
- latest run summary
- next candidate queue

`STATE.json` owns the current machine-readable task contract.
`STATE.md` mirrors the current task for review and continuity.

## Control Knobs

- `risk_appetite`: `medium-high` by default, bounded by hard approval zones.
- `default_agent_budget`: `2` as an allowance for separable work, not a default
  spawn requirement.
- `max_agent_budget`: `4`.
- `repair_attempts`: `2`.
- `review_default`: `non_trivial_implementation_only`.
- `direction_review_default`: `recommend_and_wait_for_user_approval`.
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
