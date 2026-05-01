# Selfdex

Language: [한국어](README.md) | [English](README.en.md)

Selfdex is a supervised command center for Codex work on a project you choose.

It reads the selected project first, decides one useful next improvement,
evolution, or feature task, asks for approval, sends only the approved bounded
work to Codex, verifies the result, and records evidence.

```text
select project -> read direction -> choose next task -> ask approval
-> freeze contract -> delegate to Codex -> verify -> record
```

Selfdex is not a background daemon, not a blind refactor bot, and not a tool
that silently rewrites your repositories. It is meant to sit between you and
Codex as the control layer that keeps the work useful, bounded, and auditable.

Selfdex is not a multi-agent kit. Its default runtime model is a GPT-5.5
prompt-guided command center: clear roles, bounded tool use, explicit stop
conditions, local verification, and compact run evidence. Codex native
Subagents are an optional backend only when work splits cleanly.

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
  product, milestone, roadmap, or priority direction.
- Selfdex reads, ranks, freezes, asks approval, records, and prevents
  uncontrolled autonomy.
- Codex implements, verifies, debugs, reviews diffs, and repairs inside the
  approved contract.

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

Selfdex uses the lightest safe execution lane:

- lightweight `single-session` for small documentation, tests, local policy, or
  narrow implementation changes
- frozen-contract `single-session` for non-trivial but tightly coupled work
- Codex native Subagents/MultiAgentV2 only when explorer, worker, or reviewer
  lanes are independently useful and independently verifiable

GPT-5.5 prompt guidance is an operating principle, not an automatic GPT call.
Product, milestone, roadmap, or priority review still requires the user to ask
for GPT / Pro extended mode or explicitly approve it.

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
- `.agents/plugins/marketplace.json` advertises the repo-local plugin package.
- `scripts/install_selfdex_plugin.py` installs the plugin into a selected home.
- `scripts/check_selfdex_setup.py` verifies core setup, local fallbacks, and
  recommended Codex integrations after install.
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
- no npm publish step
- no claim that read-only validation replaces implementation evidence

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
- run evidence and state contracts are recorded
- verification protects the current safety model

The next product step is not broader autonomy. It is making the approved
project-session flow smoother while keeping read-only planning, explicit
approval, local verification, lightweight default execution, optional native
Subagents, and run records intact.
