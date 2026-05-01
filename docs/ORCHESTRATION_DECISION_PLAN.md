# Native Subagent Decision Plan

Selfdex no longer uses its old local topology scorecard as the active runtime
model. Planning now asks one direct question:

```text
Would official Codex native subagents make this task safer, cleaner, or faster?
```

## Official Roles

| Role | Purpose |
| :-- | :-- |
| `main` | Own requirements, task choice, approval boundaries, integration, final report, and run records. |
| `explorer` | Read-only codebase scouting, evidence collection, and write-boundary recommendation. |
| `docs_researcher` | Read-only official docs or API behavior checks. |
| `worker` | Implementation inside one frozen and disjoint write boundary. |
| `reviewer` | Read-only correctness, regression, security, and missing-test review. |

## Decision Model

`scripts/plan_next_task.py` now reports a `recommended_agents` block with a
`subagent_fit` payload:

| Field | Meaning |
| :-- | :-- |
| `agent_runtime` | Always `codex_native_subagents` for the active Selfdex runtime. |
| `subagent_use` | Whether the task stays main-owned or uses official subagents. |
| `selected_agents` | Official Codex agent roles recommended for the task. |
| `estimated_write_boundary_count` | Likely number of independently owned write boundaries. |
| `write_collision_risk` | Risk that multiple workers would touch the same files. |
| `coordination_cost` | Cost of explaining, waiting, merging, and reviewing. |
| `parallel_or_specialist_gain` | Expected value from parallel or specialized agent work. |
| `verification_independence` | Whether slices can be checked separately. |
| `subagent_value` | Final recommendation: `main_only`, `use_readonly_subagents_first`, or `use_subagents`. |

## Execution Rules

| Fit | Default Action |
| :-- | :-- |
| Small or tightly coupled work | Main agent owns the task. |
| Broad read-only discovery | Use `explorer`; add `docs_researcher` when official docs matter. |
| Large work with write collision risk | Use read-only `explorer` and `reviewer` first; delay workers until boundaries are clear. |
| Large work with disjoint write boundaries | Use `explorer`, one or more bounded `worker` subagents, and `reviewer`. |
| Unclear contract | Main agent freezes the contract before assigning write-capable workers. |

## Safety Rule

`@selfdex` gives explicit permission to use official Codex native subagents when
useful. It does not grant permission for hard approval zones.

Worker subagents need frozen write boundaries. Commit, push, publish, deploy,
secret access, database or production writes, destructive Git, and destructive
filesystem operations still require separate approval.
