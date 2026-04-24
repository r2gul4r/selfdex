# Selfdex Handoff Memory

This is a repo-local handoff note for continuing Selfdex work from another
machine or another Codex session.

## Goal

Selfdex is an aggressive but bounded recursive improvement harness. The target
loop is:

```text
register projects -> scan -> ask -> classify -> rank -> freeze -> orchestrate -> implement -> verify -> record -> repeat
```

`codex_multiagent` remains the conservative safety baseline. Selfdex is the
fast-moving autopilot layer.

## Operating Rules

- Default posture is proactive implementation after the task contract is clear.
- Ordinary non-destructive commands may run automatically when they are needed
  for the active task.
- Destructive filesystem or drive operations, destructive Git, force pushes,
  installer/global Codex config edits, secret/token reads, deploys, paid API
  calls, DB writes, and production mutations remain gated.
- Non-trivial work updates `STATE.md` before implementation writes.
- Completed work is committed before moving to the next task.
- Do not edit `codex_multiagent`, global config, installers, secrets, deploys,
  paid APIs, or databases unless explicitly requested.

## Recent Pushed Commits

`origin/main` was pushed through:

- `f273535 refactor: split repo metrics helpers`
- `ddc0ee8 refactor: split planner orchestration fit`
- `ff6b55c docs: broaden command autonomy policy`
- `8305b04 docs: allow ordinary mcp connection commands`
- `8a670eb chore: clean stale verification docs`

## Current State

- Working tree should be clean after `f273535`.
- Latest completed task split file metric models and line-analysis helpers out
  of `scripts/collect_repo_metrics.py` into `scripts/repo_metrics_utils.py`.
- The reviewer sidecar found an import-boundary risk; it was fixed with
  package-aware imports and direct/module CLI tests.
- The planner's next selected candidate is:
  `scripts/extract_refactor_candidates.py 책임 분리와 경계 정리`.
- Recommended topology for that next task is currently `autopilot-mixed` with
  sidecar exploration/review after the contract is frozen.

## Verification Baseline

Use Windows PowerShell-friendly commands:

```powershell
python -m compileall -q scripts tests
python -m unittest discover -s tests
$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format json
$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown
$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format json
git diff --check
```

When files are changed, run `scripts/check_campaign_budget.py` with each changed
path listed explicitly by repeated `--changed-path` arguments.

## Subagent Lesson

Use subagents when write ownership is disjoint or when a read-only reviewer can
inspect an already-formed patch. For tightly coupled extraction work, main
should usually implement the first narrow slice, then spawn a reviewer to check
schema, import, and verification gaps.
