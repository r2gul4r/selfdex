# Target Codex Bounded Timeout

- status: `completed`
- project_key: `selfdex`
- task: `make target Codex execution truly bounded`
- final_status: `completed`

## Selected Candidate

- P0 bounded execution reliability for `scripts/run_target_codex.py`
- Fix the app-server read loop so `--timeout-seconds` is an actual process bound, not just a parameter.

## Frozen Task Contract

- Replace direct `stdout.readline()` waits with reader-thread queues governed by one monotonic deadline.
- Drain stderr in a side thread and retain a bounded stderr tail in run payloads.
- Normalize timeout, malformed JSON, stdout closure, startup failure, and runner failure into auditable blocked results.
- Add `outcome_class`, timeout, process return code, branch before/after, and restore metadata to payloads and markdown.
- Make dry-run blocked return exit code `0`, execute-mode blocked return `2`, and completed return `0`.
- Restore the original target branch only when Selfdex created a branch, the run did not complete, the original branch is known, and the target worktree is clean.

## Changed Files

- `STATE.md`
- `CAMPAIGN_STATE.md`
- `scripts/run_target_codex.py`
- `tests/test_run_target_codex.py`
- `runs/selfdex/20260430-122133-target-codex-bounded-timeout.md`

Pre-existing pending files from the previous verified README task remain in the worktree:

- `README.md`
- `runs/selfdex/20260430-115900-readme-rewrite.md`

## Verification

- `python -m unittest discover -s tests -p test_run_target_codex.py`: passed, 12 tests.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests`: passed outside sandbox, 158 tests. The first sandboxed run failed because Windows Temp writes were blocked by the host sandbox.
- `python scripts/check_doc_drift.py --root . --format json`: passed, status `pass`, finding_count `0`.
- `git diff --check`: passed; Git emitted CRLF normalization warnings for touched Python files.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed, status `pass`, violation_count `0`.

## Repair Attempts

- `1`
- Focused tests first failed because `tempfile.TemporaryDirectory()` could not write under sandboxed Windows Temp. The focused test fixture now uses an ignored workspace-local scratch root.
- Full suite first failed for the same host sandbox Temp restriction in unrelated tests, then passed when rerun outside the sandbox.

## Final Outcome

- `run_target_codex.py` no longer blocks indefinitely on app-server stdout reads.
- Target Codex runtime failures are distinguishable from dry-run policy blocks.
- Execute-mode blocked runs now return a failing automation exit code.
- Target branch state and non-destructive restore decisions are recorded.

## Stop Or Failure Reason

- none
