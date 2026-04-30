# Project Registry

Selfdex uses this registry as the boundary for multi-project analysis.

`project_registry.json` is the tool-readable source of truth. This Markdown
file is the human-readable mirror and policy note.

Registered external projects are read-only by default. Any cross-project write
needs separate explicit approval for that target project and task.

## Registered Projects

| project_id | path | role | write_policy | verification |
| :-- | :-- | :-- | :-- | :-- |
| selfdex | . | recursive improvement harness | selfdex-local writes only | python -m compileall -q scripts tests; python -m unittest discover -s tests |
| daboyeo | ../daboyeo | movie showtime and recommendation validation target | read-only | read-only candidate generation; human rubric scoring |
| codex_multiagent | ../codex_multiagent | multi-agent policy kit validation target | read-only | read-only candidate generation; human rubric scoring |
| fs | ../fs | small static project validation target | read-only | read-only candidate generation; human rubric scoring |
