# Selfdex Handoff Memory

This is a repo-local handoff note for continuing Selfdex work from another
machine or another Codex session.

## Goal

Selfdex is a GPT-5.5 prompt-guided command center for approved Codex work on a
user-selected project. The target loop is:

```text
register projects -> scan -> ask -> classify -> rank -> freeze -> orchestrate -> implement -> verify -> record -> repeat
```

The old `codex_multiagent` project is legacy/reference evidence only. It is no
longer the active Selfdex baseline or registry proof target. Current runtime
positioning is lightweight `single-session` by default, with Codex native
Subagents used only when work splits into independently useful explorer,
worker, or reviewer lanes.

## Operating Rules

- Default posture is proactive implementation after the task contract is clear.
- Ordinary non-destructive commands may run automatically when they are needed
  for the active task.
- Destructive filesystem or drive operations, destructive Git, force pushes,
  installer/global Codex config edits, secret/token reads, deploys, paid API
  calls, DB writes, and production mutations remain gated.
- Non-trivial work updates `STATE.md` before implementation writes.
- Completed work is committed before moving to the next task when the user asks
  for commit/push.
- Do not edit external projects, global config, installers, secrets, deploys,
  paid APIs, or databases unless explicitly requested.
- GPT-5.5 prompt guidance is an operating principle, not permission to call GPT
  Pro extended mode automatically. Product direction review still waits for
  explicit user approval or user request.

## Recent Pushed Commits

`origin/main` was pushed through:

- `f273535 refactor: split repo metrics helpers`
- `ddc0ee8 refactor: split planner orchestration fit`
- `ff6b55c docs: broaden command autonomy policy`
- `8305b04 docs: allow ordinary mcp connection commands`
- `8a670eb chore: clean stale verification docs`

## Current State

- Selfdex has a repo-local plugin path for future `@selfdex` invocation.
- The intended public installer remains `npx selfdex install` after npm
  publication.
- The installer should complete core Selfdex setup and then run the setup
  doctor. External account-bound integrations such as GitHub remain user
  connection steps when not already available.
- npm publication is blocked until the runtime-positioning refactor is verified
  and recorded.
- Active external validation targets are recorded in `PROJECT_REGISTRY.md`.
  Historical `codex_multiagent` artifacts under `runs/external-validation/`
  should not be deleted.

## Verification Baseline

Use Windows PowerShell-friendly commands:

```powershell
python -m compileall -q scripts tests
python -m unittest discover -s tests
$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json
$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown
$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json
$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_selfdex_setup.py --root . --format json
$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_github_actions_status.py --root . --format json
git diff --check
```

When files are changed, run `scripts/check_campaign_budget.py` with each changed
path listed explicitly by repeated `--changed-path` arguments.

Use GitHub Actions as the post-push feedback path. Do not read Gmail just to
detect CI failures.

## Subagent Lesson

Use Codex native Subagents when write ownership is disjoint, read-only
exploration can run beside local work, or a reviewer can inspect an
already-formed non-trivial patch. For small, routine, or tightly coupled work,
stay in lightweight `single-session`; handoff cost is usually higher than the
parallel gain.
