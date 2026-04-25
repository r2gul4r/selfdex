# Project Registry

Selfdex uses this registry as the boundary for multi-project analysis.

Registered projects are read-only by default. Any cross-project write needs a
separate explicit approval for that target project and task.

## Registered Projects

| project_id | path | role | write_policy | verification |
| :-- | :-- | :-- | :-- | :-- |
| selfdex | . | recursive improvement harness | selfdex-local writes only | python -m compileall -q scripts tests; python -m unittest discover -s tests |
| apex_analist | ../apex_analist | external validation target | read-only | read-only candidate generation; human rubric scoring |
| mqyubot | ../mqyubot | external validation target | read-only | read-only candidate generation; human rubric scoring |
| mqyusimeji | ../mqyusimeji | external validation target | read-only | read-only candidate generation; human rubric scoring |
