# Project Registry

Selfdex uses this registry as the boundary for multi-project analysis.

`project_registry.json` is the tool-readable source of truth. This Markdown
file is the human-readable mirror and policy note.

Registered external projects are read-only by default. Any cross-project write
needs separate explicit approval for that target project and task.

The active external validation set is currently `daboyeo` and `apex_analist`.
Historical `codex_multiagent` validation artifacts remain under
`runs/external-validation/`, but that project is no longer an active Selfdex
baseline or registry target.

## Registered Projects

| project_id | path | role | write_policy | verification |
| :-- | :-- | :-- | :-- | :-- |
| selfdex | . | recursive improvement harness | selfdex-local writes only | python -m compileall -q scripts tests; python -m unittest discover -s tests |
| daboyeo | ../daboyeo | movie showtime and recommendation validation target | read-only | read-only candidate generation; human rubric scoring |
| apex_analist | ../apex_analist | analytics frontend validation target | read-only | read-only candidate generation; human rubric scoring |
