# Selfdex

Selfdex is an aggressive autonomous Codex operating harness.

The goal is not to replace safety. The goal is to make the default loop more
proactive:

```text
scan -> rank -> plan -> delegate -> implement -> verify -> repair -> record
```

`codex_multiagent` stays the conservative safety baseline. This repository is
the fast-moving autopilot layer that uses those ideas with a higher default
appetite for exploration, parallel work, and bounded repair.

## Default Behavior

- Prefer action after a task contract is clear enough.
- Spawn explorer, worker, and reviewer lanes aggressively when host policy and
  task authorization allow it.
- Keep destructive actions, secrets, deploys, paid calls, and database changes
  behind hard approval.
- Keep every loop recoverable through `CAMPAIGN_STATE.md`, `STATE.md`, and
  `runs/`.

## Core Files

| Path | Role |
| :-- | :-- |
| `AGENTS.md` | Repository execution rules for aggressive autonomy |
| `AUTOPILOT.md` | Long-running autopilot policy and loop design |
| `CAMPAIGN_STATE.md` | Current campaign goal, budget, locks, and guardrails |
| `STATE.md` | Current task contract and write ownership |
| `runs/` | Per-run records and evidence |
| `scripts/plan_next_task.py` | Selects the next candidate from repository signals |
| `scripts/collect_repo_metrics.py` | Repository metric scanner |
| `scripts/extract_*_candidates.py` | Feature/test/refactor candidate extractors |
| `scripts/normalize_quality_signals.py` | Normalizes scan outputs into priority signals |

## Quick Start

```bash
python scripts/plan_next_task.py --root . --format markdown
python scripts/collect_repo_metrics.py --root . --pretty
python scripts/extract_test_gap_candidates.py --root . --format markdown
```

## Verification

```bash
python -m compileall -q scripts
python scripts/plan_next_task.py --root . --format json
```
