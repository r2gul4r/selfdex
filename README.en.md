# Selfdex

Language: [한국어](README.md) | [English](README.en.md)

Selfdex is a supervised command center for Codex work on a project you choose.

It reads the selected project first, decides one useful next improvement,
evolution, or feature task, asks for approval, sends only the approved bounded
work to Codex, reviews and verifies the result, optionally closes it through a
commit gate with commit, push, CI status, and records evidence.

```text
select project -> read direction -> choose next task -> ask approval
-> freeze contract -> delegate to Codex -> review -> verify -> commit gate -> record
```

Selfdex is not a background daemon, not a blind refactor bot, and not a tool
that silently rewrites your repositories. It is meant to sit between you and
Codex as the control layer that keeps the work useful, bounded, and auditable.

Selfdex is not a legacy multi-agent kit or a local topology scorecard. Its
default runtime model is a GPT-5.5 prompt-guided command center, and its agent
runtime is official Codex native Subagents/MultiAgentV2. Calling `@selfdex`
means Selfdex may use official subagents when useful.

## Install

The intended published install command is:

```bash
npx selfdex install
```

The install path clones or updates Selfdex, installs the home-local `@selfdex`
Codex plugin, then runs `selfdex doctor` automatically. Core Selfdex setup is
completed by the installer; account-bound integrations such as GitHub or
ChatGPT Apps are reported as recommended user actions when they are not already
available.

Preview the install without cloning or writing plugin files:

```bash
npx selfdex install --dry-run
```

This npm command works after the `selfdex` package is published. Until then,
use a cloned checkout and run the bootstrap locally:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Preview the local bootstrap:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
```

Install only the `@selfdex` Codex plugin from an existing checkout:

```bash
python scripts/install_selfdex_plugin.py --root . --yes --format markdown
```

Preview the plugin install:

```bash
python scripts/install_selfdex_plugin.py --root . --dry-run --format markdown
```

Re-check setup after installation:

```bash
selfdex doctor
```

`selfdex doctor` also checks the project-scoped Codex subagent policy files:
`.codex/config.toml` and `.codex/agents/*.toml`.

Requirements for the bootstrap path:

- Node.js and npm for the `npx` entrypoint
- PowerShell for `install.ps1`
- Git for clone or update
- Python 3 for the plugin installer
- Codex with plugin discovery enabled

Publishing to npm, npm credentials, and registry ownership are separate
approval-gated setup steps. They are not performed by this repository's tests
or bootstrap verification.

## Use

After the plugin is installed or enabled, open Codex in the target project
session and call:

```text
@selfdex read this project and choose the next safe task
```

Selfdex treats the current session directory as the selected project unless you
name another path.

Calling `@selfdex` also means:

- Selfdex should run command-center mode for the current project.
- Selfdex may use official Codex native Subagents/MultiAgentV2 when useful.
- The main agent owns requirements, approval boundaries, integration, and
  records.
- Read-only subagents such as `explorer`, `docs_researcher`, and `reviewer` may
  handle exploration, docs/API checks, logs, and review.
- A `worker` subagent may edit files only after the contract is frozen and the
  write boundary is disjoint.
- Commit, push, publish, deploy, secrets, databases, production writes, and
  destructive operations still require separate approval.

The first response should be a read-only plan:

- selected task
- why it matters
- proposed write boundary
- non-goals
- verification commands
- risk level
- approval requirement
- Codex handoff prompt

If you approve the target-project write, Selfdex may run the bounded execution
path. If you do not approve it, the loop stops at the plan.

## What It Does

Selfdex separates direction, coordination, and implementation:

- GPT / Pro extended mode is used only when the user asks for high-level
  product, milestone, roadmap, priority, improvement, or feature direction.
  When `@chatgpt-apps` is available in the session, Selfdex treats it as this
  direction-review path.
- Selfdex reads, ranks, freezes, asks approval, records, and prevents
  uncontrolled autonomy.
- Codex implements, verifies, debugs, reviews diffs, and repairs inside the
  approved contract. Code review belongs to the Codex native `reviewer`
  subagent.

Selfdex looks for several kinds of next work:

- `repair`: restore broken behavior
- `hardening`: make existing behavior harder to break
- `improvement`: improve maintainability or clarity
- `capability`: add a missing system ability
- `automation`: automate repeated coordination work
- `direction`: move the project toward a better product or technical path

The preferred candidate is not just "something is wrong." It is:

```text
This project would be better if it moved in this direction,
and this is the smallest safe first step.
```

## Runtime Model

Selfdex uses official Codex native Subagents/MultiAgentV2 concepts:

- `main agent`: requirements, task choice, approval boundaries, integration,
  final reporting, and run records
- `explorer`: `gpt-5.5` low, read-only codebase exploration and evidence
  gathering
- `docs_researcher`: `gpt-5.5` medium, read-only official docs and API
  behavior checks
- `worker`: `gpt-5.5` high, implementation inside one frozen write boundary
- `reviewer`: `gpt-5.5` xhigh, read-only correctness, regression, security,
  and missing-test review

`explorer` and `worker` match Codex built-in agent names. `reviewer` and
`docs_researcher` are project-scoped custom roles that follow Codex custom-agent
patterns. Selfdex keeps names stable because the `name` field is the runtime
source of truth.

Small tightly coupled work can stay in the main agent. Exploration, docs
checks, log analysis, review, and disjoint implementation slices should use
official subagents when they can run independently. The old local control
logic is no longer the active runtime.

GPT-5.5 prompt guidance is an operating principle, not an automatic GPT call.
Product, milestone, roadmap, priority, improvement, or feature review still
requires the user to ask for GPT / Pro extended mode or explicitly approve it.
Use `@chatgpt-apps` for that product/app direction review when available; use
the Codex native `reviewer` subagent for ordinary code diff review.

## Safety Model

Selfdex starts read-only for external projects.

Target-project writes require explicit approval in the current thread. Even
folder-wide approval does not bypass hard approval zones.

Hard approval is always required for:

- destructive filesystem or Git history operations
- secrets, credentials, private keys, or token access
- paid API calls
- public deploys
- database migrations or production writes
- cross-workspace changes outside the approved boundary
- global Codex config, installer, plugin, or MCP setup changes

ChatGPT Apps and MCP surfaces are read-only first. The initial app surface may
show registered projects, the next recommended task, recent run records, and
approval status. It must not expose target-project write execution until that
surface is explicitly approved.

## Current Capabilities

Installed and tested surfaces:

- `package.json` and `bin/selfdex.js` define the npm-style `selfdex` CLI.
- `install.ps1` bootstraps Selfdex and installs the home-local plugin.
- `plugins/selfdex/` contains the Codex plugin used for `@selfdex` invocation.
- `.codex/config.toml` and `.codex/agents/*.toml` define the official Codex
  native Subagents/MultiAgentV2 roles, `gpt-5.5` model selection, and
  role-specific reasoning effort.
- `.agents/plugins/marketplace.json` advertises the repo-local plugin package.
- `scripts/install_selfdex_plugin.py` installs the plugin into a selected home.
- `scripts/check_selfdex_setup.py` verifies core setup, local fallbacks, and
  recommended Codex integrations after install.
- `scripts/check_commit_gate.py` checks whether reviewed and verified work is
  ready to commit.
- `scripts/plan_external_project.py` reads a target project and emits a frozen
  task contract without editing the target.
- `scripts/run_target_codex.py` can run the approved target-project execution
  path with branch and run-record metadata.
- `scripts/build_control_surface_snapshot.py` builds the read-only control
  surface payload.
- `scripts/control_surface_mcp_server.py` exposes the read-only payload through
  a dependency-free local `/mcp` JSON-RPC scaffold.
- `scripts/check_selfdex_plugin.py`, `scripts/check_campaign_budget.py`, and
  `scripts/check_doc_drift.py` validate plugin wiring, contract boundaries, and
  README drift.
- `scripts/*.py` contains the remaining scanners, planners, recorders,
  extractors, and checkers.

Still intentionally bounded:

- no background polling loop
- no automatic multi-candidate execution
- no unapproved target-project writes
- no automatic GPT direction review
- no legacy `codex_multiagent` baseline
- no old Selfdex topology scorecard as the active runtime
- no npm publish step
- no claim that read-only validation replaces implementation evidence
- no automatic commit or push before review and verification

## Quick Start

Inspect this repository:

```bash
python scripts/build_project_direction.py --root . --format markdown
python scripts/plan_next_task.py --root . --format markdown
```

Inspect registered external projects read-only:

```bash
python scripts/check_external_validation_readiness.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --project-id daboyeo --format markdown
```

Create a target-project contract without editing the target:

```bash
python scripts/plan_external_project.py --root . --project-root ../daboyeo --project-name daboyeo --format markdown
```

Run the target-project orchestrator in dry-run mode:

```bash
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --format markdown
```

Run approved target execution only after explicit approval:

```bash
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --execute --format markdown
```

Build the read-only control surface:

```bash
python scripts/build_control_surface_snapshot.py --root . --format markdown
python scripts/control_surface_mcp_server.py --root . --describe-tools
```

Maintenance checks:

```bash
python scripts/check_campaign_budget.py --root . --format markdown
python scripts/check_doc_drift.py --root . --format markdown
python scripts/collect_repo_metrics.py --root . --pretty
python scripts/extract_test_gap_candidates.py --root . --format markdown
```

## Records

Selfdex records work centrally under `runs/`.

Target-project records use:

```text
runs/<project_key>/<YYYYMMDD-HHMMSS>-<task-slug>.md
```

Each non-trivial run should include:

- project id and project root
- selected candidate
- frozen contract
- approval status
- changed files
- verification commands and results
- repair attempts
- final status: `completed`, `failed`, `blocked`, or `stopped`
- next candidate or stop reason

## Repository Map

Core control files:

- `README.en.md` is the English README mirror.
- `AGENTS.md` defines repository execution rules.
- `AUTOPILOT.md` defines the supervised loop policy.
- `CAMPAIGN_STATE.json` is the machine-readable campaign contract.
- `CAMPAIGN_STATE.md` mirrors campaign intent for humans.
- `STATE.json` is the machine-readable active task contract.
- `STATE.md` mirrors the active task and write boundary for humans.
- `project_registry.json` is the tool-readable project registry.
- `PROJECT_REGISTRY.md` mirrors the registry and read-only boundary.
- `docs/SELFDEX_FINAL_GOAL.md` is the north-star contract.
- `docs/CANDIDATE_QUALITY_RUBRIC.md` defines candidate usefulness scoring.
- `docs/SELFDEX_HANDOFF.md` keeps cross-machine continuity notes.
- `docs/ORCHESTRATION_DECISION_PLAN.md` describes orchestration decisions.
- `runs/` stores run evidence.
- `examples/quality_signal_samples.json`,
  `examples/external_validation_planner_sample.json`, and
  `examples/candidate_quality_sample.json` are validation fixtures.

Active external validation targets are listed in `PROJECT_REGISTRY.md`.
Historical `codex_multiagent` reports remain under `runs/external-validation/`
as legacy/reference evidence, but that project is no longer the active Selfdex
baseline or registry proof target.

Installer and plugin files:

- `package.json` defines the npm package metadata and executable.
- `bin/selfdex.js` is the npm CLI wrapper for `install.ps1` and setup doctor.
- `install.ps1` clones or updates Selfdex, invokes the plugin installer, then
  runs the setup doctor unless explicitly skipped.
- `plugins/selfdex/` contains the repo-local Codex plugin package.
- `.agents/plugins/marketplace.json` advertises the plugin for Codex.

## Verification

Use narrow checks for documentation and contract edits:

```bash
python scripts/check_doc_drift.py --root . --format json
python scripts/check_campaign_budget.py --root . --include-git-diff --format json
git diff --check
```

Use full checks after code, installer, plugin, or workflow changes:

```bash
node bin/selfdex.js --help
node bin/selfdex.js install --dry-run --install-root C:/tmp/selfdex-npx-dry-run
node bin/selfdex.js doctor --help
npm pack --dry-run
python -m compileall -q scripts tests
python -m unittest discover -s tests
python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format json
python scripts/build_project_direction.py --root . --format json
python scripts/build_external_candidate_snapshot.py --root . --format json
python scripts/build_external_validation_package.py --root . --format json
python scripts/plan_external_project.py --root . --project-id daboyeo --format json
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --format json
```

After an approved commit and push, use GitHub as the CI feedback source:

```bash
python scripts/check_commit_gate.py --root . --commit-message "docs: verify commit gate" --format json
python scripts/check_github_actions_status.py --root . --format json
```

CI runs the baseline through `.github/workflows/check.yml` with:

```bash
make check
```

## Current Direction

Selfdex is currently ready as a supervised local command center foundation:

- project-session invocation exists through `@selfdex`
- install is prepared for `npx selfdex install` after npm publication
- read-only planning exists for selected external projects
- target execution remains approval-gated
- commit gate runs only after review and verification
- run evidence and state contracts are recorded
- verification protects the current safety model

The next product step is not broader autonomy. It is making the approved
project-session flow smoother while keeping read-only planning, explicit
approval, local verification, official Codex native Subagents/MultiAgentV2, and
run records intact.
