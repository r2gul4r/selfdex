---
name: selfdex
description: Use when the user invokes @selfdex or asks Selfdex to read the current project, choose the next useful task, freeze an approval-gated contract, or hand off approved work to Codex from a project session.
---

# Selfdex

Use this skill from a target project session. Treat the current working directory
as the user-selected target project unless the user names another path.

Selfdex is a GPT-5.5 prompt-guided command center, not a legacy multi-agent kit.
Use clear task contracts, write boundaries, stop conditions, and verification
commands as the default control surface. Codex native Subagents/MultiAgentV2 are
optional only when read-only exploration, implementation, or review can be split
cleanly and verified independently.

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

Use `scripts/install_selfdex_plugin.py --yes` from a cloned Selfdex checkout to
create a home-local plugin install. The installer records the checkout path so
this skill can find the right Selfdex root on another machine.

## Default Flow

1. Run read-only planning against the target project.
2. Summarize the selected candidate, rationale, risk, likely write boundary,
   verification commands, and approval requirement.
3. Ask for explicit approval before any target-project write or `--execute`
   run.
4. If approval is missing, stop after the plan.
5. If approval is explicit, keep execution inside the frozen target boundary
   and preserve hard approval gates.

Use lightweight `single-session` by default. Recommend Subagents only when a
specific explorer, worker, or reviewer lane would reduce risk or wall-clock time
more than the handoff cost.

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

## Safety Rules

- External projects are read-only by default.
- Do not run target-project writes, branch creation, or Codex execution without
  explicit approval in the current thread.
- Do not bypass hard approval zones: destructive Git/filesystem operations,
  secrets, credentials, paid APIs, deploys, databases, production writes,
  installers, or global config.
- Do not install this plugin, edit Codex home, or change global config unless
  the user explicitly approves that setup step.
- If the task becomes product direction or milestone strategy, recommend GPT
  Pro extended direction review and wait for the user's approval.
- Do not call GPT Pro extended mode automatically. GPT-5.5 prompt guidance is an
  operating principle for clear instructions, not a standing model invocation.

## Output

Keep the response short:

- selected task
- why it matters
- proposed write boundary
- verification commands
- approval needed or not
- exact next command or Codex handoff prompt
