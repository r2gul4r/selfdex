# Daboyeo Selfdex Planning Timeout Repair

- status: `completed`
- project_key: `selfdex`
- task: `daboyeo-selfdex-planning-timeout-repair`
- final_status: `completed`

## Root Cause

- `python scripts\plan_external_project.py --root . --project-root C:\lsh\git\daboyeo --project-name daboyeo --format json` timed out after 120 seconds before the patch.
- Focused timings showed `collect_repo_metrics.py` was the dominant blocker: it exceeded 45 seconds while project direction, test-gap, and feature-gap scanners completed.
- Two concrete causes were found:
  - scanners used `Path.rglob("*")`, so excluded/generated directories were filtered after recursive descent instead of pruned before descent;
  - external refactor planning ran per-file git history and duplicate-block analysis over daboyeo's mirrored static assets and large data files.

## Frozen Task Contract

- Keep `C:\lsh\git\daboyeo` read-only.
- Fix Selfdex scanners to prune excluded directories before descent and tolerate inaccessible directories.
- Add generated/local artifact excludes seen in daboyeo: `.local`, `.playwright-cli`, `test-results`, and `tmp`.
- Make external refactor planning use bounded metrics by skipping per-file git history and duplicate-block analysis.
- Update the installed `@selfdex` plugin pointer only after the local repair passes.

## Changed Files

- `STATE.md`
- `STATE.json`
- `scripts/repo_scan_excludes.py`
- `scripts/collect_repo_metrics.py`
- `scripts/refactor_metrics_payload.py`
- `scripts/feature_file_records.py`
- `scripts/extract_test_gap_candidates.py`
- `scripts/project_direction_evidence.py`
- `tests/test_repo_scan_excludes.py`
- `runs/selfdex/20260504-132846-daboyeo-selfdex-planning-timeout-repair.md`
- `CAMPAIGN_STATE.md`
- `ERROR_LOG.md`

## Verification

- `python -m unittest discover -s tests -p test_repo_scan_excludes.py`: passed after approved sandbox escalation, 5 tests.
- `python -m unittest discover -s tests -p test_repo_metrics_utils.py`: passed after approved sandbox escalation, 5 tests.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: passed after approved sandbox escalation, 5 tests.
- `python -m compileall -q scripts tests`: passed.
- `python scripts\collect_repo_metrics.py --root C:\lsh\git\daboyeo --pretty --skip-git-history --skip-duplication`: passed in about 1.54 seconds.
- `python scripts\extract_refactor_candidates.py --root C:\lsh\git\daboyeo --format json`: passed in about 1.69 seconds.
- `python scripts\plan_external_project.py --root . --project-root C:\lsh\git\daboyeo --project-name daboyeo --format json`: passed in about 6.04 seconds.
- `node bin\selfdex.js doctor --install-root C:\lsh\git\selfdex --home C:\Users\pc07-00\.codex --codex-home C:\Users\pc07-00\.codex --format json`: passed, readiness `ready_with_recommended_actions`.
- `git diff --check`: passed with CRLF warnings only.

## Install Pointer Update

- Ran `node bin\selfdex.js install --use-existing-checkout --install-root C:\lsh\git\selfdex --plugin-home C:\Users\pc07-00\.codex` after approval.
- Installed global skill now records `C:\lsh\git\selfdex` under `Installed Checkout`.
- Installed plugin root config now matches `C:\lsh\git\selfdex`.

## Repair Attempts

- `1`
- Initial focused unittest commands failed under the workspace sandbox because Python `TemporaryDirectory()` created directories that were not writable by the sandboxed process. The same focused suites passed after approved sandbox escalation.

## Final Outcome

- Daboyeo Selfdex read-only planning no longer times out in the reproduced path.
- Actual `@selfdex` project-session invocation now resolves to the repaired checkout.
- No daboyeo project files were modified.

## Stop Or Failure Reason

- none
