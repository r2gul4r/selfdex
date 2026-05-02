---
name: selfdex
description: Use when the user invokes @selfdex or asks Selfdex to read the current project, choose the next useful task, freeze an approval-gated contract, or hand off approved work to Codex from a project session.
---

# Selfdex

Use this skill from a target project session. Treat the current working directory
as the user-selected target project unless the user names another path.

Selfdex is a GPT-5.5 prompt-guided command center that uses official Codex
native Subagents/MultiAgentV2 as its agent runtime. Runtime phrase:
`Codex native Subagents/MultiAgentV2`. It is not based on the old
Selfdex local topology labels or scoring/budget control logic.

Calling `@selfdex` is explicit permission for Selfdex to recommend and use
Codex native subagents when they are useful. Keep the main agent focused on
requirements, task selection, approvals, integration, final reporting, and run
records. Use subagents for noisy or specialized work such as read-only
exploration, CI/log analysis, documentation/API checks, review, summarization,
or bounded implementation.

## Locate Selfdex

Find the Selfdex command-center repository in this order:

1. `SELFDEX_ROOT` environment variable.
2. The `Installed Checkout` section in this skill, when present.
3. `selfdex-root.json` in the installed plugin root, when present.
4. A sibling checkout at `../selfdex`.
5. The known local checkout `D:\git\selfdex`.

The chosen root must contain `scripts/plan_external_project.py` and
`CAMPAIGN_STATE.json`. If none is found, stop and ask the user to install or
configure Selfdex; do not edit global Codex config yourself.

Use `npx selfdex install` for the default one-command setup, or
`node bin/selfdex.js install --use-existing-checkout --install-root .` from a
cloned checkout. The Node-native installer records the checkout path so this
skill can find the right Selfdex root on another machine. The Python installer
script remains a legacy fallback, not the default public install path.

## Default Flow

1. Run read-only planning against the target project.
2. Summarize the selected candidate, rationale, risk, likely write boundary,
   verification commands, and approval requirement.
3. Ask for explicit approval before any target-project write or `--execute`
   run.
4. If approval is missing, stop after the plan.
5. If approval is explicit, keep execution inside the frozen target boundary
   and preserve hard approval gates.
6. Choose official Codex agent roles directly. Project-scoped Selfdex
   subagents use `gpt-5.5` with role-specific reasoning effort:
   - `explorer`: low, read-only codebase and evidence mapping.
   - `docs_researcher`: medium, read-only official docs or API behavior checks.
   - `worker`: high, bounded implementation inside one declared write boundary.
   - `reviewer`: xhigh, read-only correctness, regression, security, and test review.
7. Read-only subagents may run after `@selfdex` when they reduce noise, shorten
   wall-clock time, or keep main-thread context clean.
8. Write-capable worker subagents require a frozen contract and disjoint write
   boundary. If write boundaries overlap, keep integration in the main agent.
9. After implementation, run review and verification before any commit stage.
10. Use the Selfdex commit gate only when the user explicitly asks for it or the
    active project policy enables it.
11. Do not select the next candidate until commit/push/GitHub-check evidence is
    recorded, or the run is explicitly blocked.

Do not route through legacy Selfdex topology terms. Decide whether the main
agent can handle the task or whether official Codex subagents should own
explorer, docs, worker, or reviewer lanes.

Use this read-only planning command shape:

```powershell
python <SELFDEX_ROOT>\scripts\plan_external_project.py --root <SELFDEX_ROOT> --project-root <TARGET_ROOT> --project-name <TARGET_NAME> --format markdown
```

Only after explicit approval for target-project writes, use this execution
shape:

```powershell
python <SELFDEX_ROOT>\scripts\run_target_codex.py --root <SELFDEX_ROOT> --project-root <TARGET_ROOT> --project-name <TARGET_NAME> --execute --format markdown
```

This is the same command path as `scripts/run_target_codex.py`; never run it
with `--execute` until the user explicitly approves target-project writes.

After review and local verification, use this pre-commit gate before committing:

```powershell
python <SELFDEX_ROOT>\scripts\check_commit_gate.py --root <SELFDEX_ROOT> --commit-message "<type>: <summary>" --format json
```

If commit and push are approved, check GitHub Actions after the push:

```powershell
python <SELFDEX_ROOT>\scripts\check_github_actions_status.py --repo <owner>/<repo> --sha <sha> --format json
```

GitHub failure or pending status keeps the current loop open for repair or
blocked recording. It must not advance to the next task automatically.

## Safety Rules

- External projects are read-only by default.
- Do not run target-project writes, branch creation, or Codex execution without
  explicit approval in the current thread.
- Do not bypass hard approval zones: destructive Git/filesystem operations,
  secrets, credentials, paid APIs, deploys, databases, production writes,
  installers, or global config.
- Do not install this plugin, edit Codex home, or change global config unless
  the user explicitly approves that setup step.
- Do not commit or push unless the user explicitly asks for the commit gate or
  the active project policy enables it for this task.
- Do not continue to the next candidate while GitHub Actions is pending or
  failing.
- If the task becomes product direction or milestone strategy, recommend GPT
  Pro extended direction review and wait for the user's approval. If
  `@chatgpt-apps` is available, treat it as the product/app direction-review
  surface for project purpose, improvement ideas, and additional feature
  opportunities.
- Do not call GPT Pro extended mode automatically. GPT-5.5 prompt guidance is an
  operating principle for clear instructions, not a standing model invocation.
- Do not use GPT Pro / ChatGPT Apps direction review as routine code review.
  Use the Codex native `reviewer` subagent for non-trivial implementation
  review.

## Output

Keep the response short:

- selected task
- why it matters
- proposed write boundary
- verification commands
- approval needed or not
- exact next command or Codex handoff prompt
- commit/push/GitHub status when the commit gate was used
