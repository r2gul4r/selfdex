# External Project Plan

- status: `ready`
- validation_mode: `read_only`
- external_project_writes_performed: `False`
- project_id: `apex_analist`
- resolved_path: `D:\git\apex_analist`
- write_policy: `read-only`
- human_approval_required: `True`
- recorded_run_path: `D:\git\selfdex\runs\20260425-201500-external-project-plan-apex-analist.md`

## Selected Candidate

- title: docs/codex-multiagent/WORKSPACE_CONTEXT_GUIDE.md 중복 블록 정리
- source: `refactor`
- work_type: `improvement`
- priority_score: `43.7`
- risk_level: `medium`

## Why It Matters

- 공통 축 판정: goal_alignment=borderline, gap_relevance=medium, safety=safe, reversibility=strong, structural_impact=low, leverage=medium
- 리팩터링 루브릭: quality_impact=2, risk=3, maintainability=3, feature_goal_contribution=2
- 중복 신호와 변경 빈도 신호가 함께 보여 변경 안정성 개선 효과를 설명하기 쉬움

## Candidate Quality Estimate

- status: `heuristic_estimate`
- verdict: `strong`
- total: `13`
- requires_human_scoring: `True`
- real_problem: `3`
- user_value: `2`
- local_verifiability: `3`
- scope_smallness: `3`
- risk_reversibility: `2`

## Write Boundaries

- target_project_writes_allowed_now: `False`
- future_write_mode: requires explicit user approval and an isolated branch or worktree
- proposed_target_write_set:
  - `docs/codex-multiagent/WORKSPACE_CONTEXT_GUIDE.md`

## Files To Inspect

- `docs/codex-multiagent/WORKSPACE_CONTEXT_GUIDE.md`

## Verification Commands

- `python -m compileall -q scripts`
- `python scripts/plan_next_task.py --root . --format json`

## Registry Verification Notes

- read-only candidate generation
- human rubric scoring

## Codex Execution Prompt

```text
You are working in the user-selected target project:
D:\git\apex_analist

Goal:
Implement the smallest safe improvement for this candidate: docs/codex-multiagent/WORKSPACE_CONTEXT_GUIDE.md 중복 블록 정리

Start read-only:
- Inspect the files below and confirm the task is still real.
- Freeze a short task contract before the first target-project write.
- Human approval is required before modifying the target project.

Likely files to inspect:
- docs/codex-multiagent/WORKSPACE_CONTEXT_GUIDE.md

Proposed target write boundary after approval:
- docs/codex-multiagent/WORKSPACE_CONTEXT_GUIDE.md

Verification to run from the target project when execution is approved:
- python -m compileall -q scripts
- python scripts/plan_next_task.py --root . --format json

Hard approval gates:
- secrets or credential access
- paid API calls
- deploys or public runtime changes
- database or production writes
- destructive filesystem or Git operations
- writes outside the frozen target-project contract

Return a PR-ready summary with changed files, verification results, repair attempts, remaining risk, and evidence suitable for a Selfdex runs/ record.
```
