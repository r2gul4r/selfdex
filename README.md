# Selfdex

Selfdex is an aggressive autonomous Codex operating harness.

The final goal is a bounded recursive improvement harness, defined in
`docs/SELFDEX_FINAL_GOAL.md`. The goal is not to replace safety. The goal is to
make the default loop more proactive:

```text
register projects -> scan -> ask -> classify -> rank -> freeze -> orchestrate -> implement -> verify -> record -> repeat
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
| `PROJECT_REGISTRY.md` | Registered projects for read-only multi-project analysis |
| `docs/SELFDEX_FINAL_GOAL.md` | Final goal, roadmap, and recursive improvement contract |
| `docs/SELFDEX_HANDOFF.md` | Cross-machine handoff memory for continuing the campaign |
| `docs/ORCHESTRATION_DECISION_PLAN.md` | Planner execution-fit model for safe multi-agent acceleration |
| `runs/` | Per-run records and evidence |
| `scripts/plan_next_task.py` | Selects the next candidate from repository signals |
| `scripts/check_campaign_budget.py` | Rejects campaign budget and write-contract violations |
| `scripts/check_doc_drift.py` | Checks README drift against generated-report scripts |
| `scripts/argparse_utils.py` | Shared argparse option helpers for local scripts |
| `scripts/markdown_utils.py` | Shared markdown parsing helpers for local scripts |
| `scripts/repo_area_utils.py` | Shared repository area labels and classifiers |
| `scripts/repo_metrics_utils.py` | Shared file metric models and line-analysis helpers |
| `scripts/repo_quality_signal_utils.py` | Shared repo metric quality-signal scoring helpers |
| `scripts/tool_result_utils.py` | Shared tool-result issue and coverage parsing helpers |
| `scripts/list_project_registry.py` | Lists registered projects without scanning or writing to them |
| `scripts/collect_repo_metrics.py` | Repository metric scanner |
| `scripts/extract_*_candidates.py` | Feature/test/refactor candidate extractors |
| `scripts/normalize_quality_signals.py` | Normalizes scan outputs into priority signals |
| `scripts/record_run.py` | Writes compact run evidence under `runs/` |
| `scripts/plan_orchestration_fit.py` | Planner task-size and orchestration-fit heuristics |
| `examples/quality_signal_samples.json` | Sample quality-tool payload for normalizer demos |

## Quick Start

```bash
python scripts/plan_next_task.py --root . --format markdown
python scripts/check_campaign_budget.py --root . --format markdown
python scripts/check_doc_drift.py --root . --format markdown
python scripts/collect_repo_metrics.py --root . --pretty
python scripts/normalize_quality_signals.py --input examples/quality_signal_samples.json --pretty
python scripts/extract_test_gap_candidates.py --root . --format markdown
```

## Verification

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests
python scripts/plan_next_task.py --root . --format json
python scripts/plan_next_task.py --root . --format markdown
python scripts/check_campaign_budget.py --root . --format json
python scripts/check_doc_drift.py --root . --format json
git diff --check
```
