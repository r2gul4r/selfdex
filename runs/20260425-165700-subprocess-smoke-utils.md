# Run: subprocess-smoke-utils

- time: `2026-04-25T17:02:26+09:00`
- task: `deduplicate script/module subprocess smoke helpers`
- profile: `autopilot-single`
- score_total: `6`
- agent_budget: `0`
- actual_topology: `single local writer`

## Contract

- Add a small shared test helper for script/module subprocess smoke execution.
- Replace only duplicated subprocess command and run setup in candidate extractor and repo metrics tests.
- Preserve script/module arguments, cwd, capture behavior, encoding, and assertions.

## Changes

- Added `tests/script_smoke_utils.py` with `run_script_and_module(...)`.
- Updated `tests/test_candidate_extractors.py` to reuse the helper for refactor extractor script/module smoke coverage.
- Updated `tests/test_repo_metrics_utils.py` to reuse the helper for repo metrics script/module smoke coverage.

## Verification

- `python -m compileall -q scripts tests`: passed with bundled Python.
- `python -m unittest discover -s tests -p test_candidate_extractors.py`: sandbox Temp/root fixture write denial, then passed after approved escalation.
- `python -m unittest discover -s tests -p test_repo_metrics_utils.py`: sandbox Temp/root fixture write denial, then passed after approved escalation.
- `python scripts/extract_refactor_candidates.py --root . --format json`: passed; this duplicate is no longer selected.
- `python scripts/plan_next_task.py --root . --format json`: passed; next selected candidate is `test_extract_definitions_supports_python_shell_and_powershell` duplication.
- `python scripts/plan_next_task.py --root . --format markdown`: passed.
- `python -m unittest discover -s tests`: sandbox Temp/root fixture write denial, then passed after approved escalation; 110 tests OK.
- `python scripts/check_campaign_budget.py --root . --format json`: passed.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `git diff --check`: passed with LF-to-CRLF warnings only.

## Result

- The repeated script/module subprocess smoke setup now has one test helper.
- Runtime CLI behavior was not changed.
- Planner advanced to the next bounded refactor candidate.

## Next

- Deduplicate shell and PowerShell symbol definition test fixtures/assertions without changing parser behavior.
