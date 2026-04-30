# Run: Run History Penalty Dedup

- project_id: `selfdex`
- project_root: `C:\lsh\git\selfdex`
- branch: `current workspace`
- final_status: `completed`
- outcome_class: `success`
- task: `Deduplicate run history penalty helpers.`

## Selected Candidate

- title: `apply_run_history_penalty 중복 정리`
- source: `refactor`
- rationale: `The same failed-run detection and candidate demotion logic existed in local and external planner paths.`

## Frozen Contract

- Add one shared helper for failed run title extraction and repeated-candidate demotion.
- Keep the penalty value at `8.0`.
- Keep local planner history scoped to `runs/selfdex/`.
- Keep external planner history scoped to `runs/<project_id>/`.
- Preserve existing dirty roadmap artifacts without rewriting or reverting them.

## Codex Session

- session_id: `local-codex-desktop`
- target_project_writes_performed: `false`

## Changed Files

- `STATE.md`
- `CAMPAIGN_STATE.md`
- `scripts/run_history_penalty.py`
- `scripts/plan_next_task.py`
- `scripts/build_external_candidate_snapshot.py`
- `tests/test_run_history_penalty.py`
- `runs/selfdex/20260430-131306-run-history-penalty-dedup.md`

## Verification

| command | result |
| :-- | :-- |
| `python -m unittest tests.test_run_history_penalty tests.test_plan_next_task tests.test_external_candidate_snapshot` | `pass`, 22 tests |
| `python -m compileall -q scripts tests` | `pass` |
| `python scripts/plan_next_task.py --root . --format json` | `pass` |
| `python scripts/build_external_candidate_snapshot.py --root . --project-id fs --limit 2 --format json` | `pass` |
| `python -m unittest discover -s tests` | `pass`, 165 tests |
| `git diff --check` | `pass`, line-ending warnings only |
| `python scripts/check_campaign_budget.py --root . --include-git-diff --format json` | `pass` |

## Repair Attempts

- none

## Failure Or Stop Reason

- none
