---
name: selfdex-commit-gate
description: Use when Selfdex work has passed implementation review and local verification and the user or project policy wants Codex to close the task with a safe commit, optional push, GitHub Actions status check, run record update, and next-candidate handoff.
---

# Selfdex Commit Gate

Use this skill after a Selfdex task has already been planned, implemented,
reviewed, and verified. The goal is to close the current loop before selecting
the next candidate.

Commit gate is not a background loop and not unconditional auto-commit. It runs
only when the user explicitly asks for it or the active project policy enables
it.

## Gate Order

1. Confirm the active task in `STATE.json` and `STATE.md`.
2. Inspect `git status --short` and `git diff --stat`.
3. Run `scripts/check_commit_gate.py` with the proposed Conventional Commit
   message.
4. Stop if the checker reports review, verification, hard-approval, or
   out-of-contract findings.
5. Stage only files inside the frozen write set.
6. Commit with the approved Conventional Commit message.
7. Push only when the user requested push or the project policy explicitly
   enables push for this task.
8. Check GitHub Actions with `scripts/check_github_actions_status.py`.
9. If CI fails, keep the loop in repair or blocked state; do not select the
   next candidate.
10. If CI passes, update run evidence and allow Selfdex to choose the next
    candidate.

## Required Checks

Run this before committing:

```powershell
python <SELFDEX_ROOT>\scripts\check_commit_gate.py --root <SELFDEX_ROOT> --commit-message "<type>: <summary>" --format json
```

The checker must pass these conditions:

- `STATE.json` phase is ready, such as `local_verified`, `reviewed`, or
  `commit_ready`.
- Reviewer result is not pending, blocked, failed, P0, or P1.
- Verification evidence exists and has no blocking failure.
- All changed paths are inside the frozen write set.
- Hard approval path hints are absent unless explicitly approved.
- Commit message uses Conventional Commits.

After push, run the GitHub status check and treat failure or pending status as
not done:

```powershell
python <SELFDEX_ROOT>\scripts\check_github_actions_status.py --repo <owner>/<repo> --sha <sha> --format json
```

## Stop Conditions

Stop instead of committing when:

- the task contract is missing or stale
- files outside the write set changed
- a hard approval zone is touched
- verification is missing or failed
- review is pending or has P0/P1 findings
- the commit message is not Conventional Commits
- push authority is unclear
- Do not select the next candidate while GitHub Actions is pending or failed

## Output

Keep the final report short:

- commit SHA, when a commit was created
- pushed branch, when a push happened
- GitHub Actions URL and result
- run artifact path
- whether the next candidate may be selected
