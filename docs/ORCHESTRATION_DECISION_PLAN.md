# Orchestration Decision Plan

Selfdex should not treat `priority_score` or `score_total` as an automatic
subagent trigger. Scores rank urgency and risk. Orchestration needs a separate
fit check that asks whether delegation is actually faster and safer.

## Problem

The first autonomous loop can execute several tasks sequentially, but parallel
work is blocked when every worker would touch the same shared files:

- `STATE.md`
- `CAMPAIGN_STATE.md`
- `runs/`

Those files should stay main-owned. Workers need disjoint write sets and, for
true concurrent mode, their own slice-local state files.

## Decision Model

`scripts/plan_next_task.py` now reports an `orchestration_fit` block:

| Field | Meaning |
| :-- | :-- |
| `task_size_class` | `tiny`, `small`, `medium`, or `large` task estimate |
| `estimated_write_set_count` | likely number of independently owned write sets |
| `shared_file_collision_risk` | risk that agents fight over the same files |
| `handoff_cost` | cost of explaining, waiting, merging, and reviewing |
| `parallel_gain` | expected speedup from independent work |
| `verification_independence` | whether slices can be checked separately |
| `orchestration_value` | final delegation value: `low`, `medium`, or `high` |

## Execution Rules

| Fit | Default Action |
| :-- | :-- |
| tiny/small + high handoff cost | `autopilot-single` |
| large + high collision risk | `autopilot-mixed` with explorer/reviewer sidecars |
| large + disjoint write sets + independent checks | `autopilot-parallel` |
| unclear contract | `autopilot-serial` until frozen |

## Concurrent State Pattern

Use concurrent state only after the contract proves independent write sets:

```text
STATE.md
  state_mode: concurrent_registry
  active_threads:
    - id: metrics-summary
      state_file: states/STATE.metrics-summary.md
      write_set:
        - scripts/metrics_summary_utils.py
        - tests/test_metrics_summary_utils.py
  workspace_locks:
    - STATE.md: main
    - CAMPAIGN_STATE.md: main
    - runs/: main
```

Workers update only their slice state and slice write set. Main owns the root
state, campaign state, run records, integration, verification, and commits.

## Safety Rule

The useful gate is:

```text
priority/risk says what matters
orchestration_fit says how to execute it
```

High priority alone does not spawn agents. Subagents are worth using only when
parallel gain beats handoff cost and collision risk is controlled.
