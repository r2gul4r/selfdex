# Run: Project Direction Responsibility Split

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: `current workspace`
- final_status: `completed`
- outcome_class: `success`
- task: `Split build_project_direction responsibilities.`

## Selected Candidate

- title: `scripts/build_project_direction.py 책임 분리와 경계 정리`
- source: `refactor`
- rationale: `The project-direction planner mixed repository evidence scanning, signal inference, opportunity construction, CLI, and rendering in one module.`

## Frozen Contract

- Move repository file scanning, text reading, path matching, quote extraction, and evidence object creation into `scripts/project_direction_evidence.py`.
- Move opportunity scoring and construction into `scripts/project_direction_opportunities.py`.
- Keep `scripts/build_project_direction.py` as the CLI, signal inference orchestration, payload assembly, and markdown rendering layer.
- Preserve payload fields and current strategic opportunity behavior.
- Do not edit external target repositories.

## Codex Session

- session_id: `local-codex-desktop`
- target_project_writes_performed: `false`

## Changed Files

- `STATE.md`
- `CAMPAIGN_STATE.md`
- `scripts/build_project_direction.py`
- `scripts/project_direction_evidence.py`
- `scripts/project_direction_opportunities.py`
- `tests/test_project_direction_evidence.py`
- `tests/test_project_direction_opportunities.py`
- `runs/selfdex/20260430-131838-project-direction-responsibility-split.md`

## Verification

| command | result |
| :-- | :-- |
| `python -m unittest tests.test_project_direction_evidence tests.test_project_direction_opportunities tests.test_build_project_direction tests.test_external_candidate_snapshot` | `pass`, 13 tests |
| `python -m compileall -q scripts tests` | `pass` |
| `python scripts/build_project_direction.py --root . --format json` | `pass` |
| `python scripts/build_external_candidate_snapshot.py --root . --project-id fs --limit 2 --format json` | `pass` |
| `python scripts/plan_next_task.py --root . --format json` | `pass` |
| `python -m unittest discover -s tests` | `pass`, 168 tests |
| `python scripts/check_doc_drift.py --root . --format json` | `pass` |
| `git diff --check` | `pass`, line-ending warnings only |
| `python scripts/check_campaign_budget.py --root . --include-git-diff --format json` | `pass` |

## Repair Attempts

- none

## Failure Or Stop Reason

- none
