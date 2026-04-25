# Run Record: Coverage Signal Check

- time: `2026-04-25T17:40:12+09:00`
- task: `add coverage signal production check`
- score_total: `8`
- topology: `autopilot-mixed`
- agent_budget: `1`
- actual_topology: `main implementation plus one read-only reviewer`

## Contract

- Add a dependency-free local checker for coverage signals.
- Add a `coverage-signal` Makefile target and include it in `check`.
- Document the checker without claiming live coverage measurement.
- Keep the existing coverage parser behavior unchanged.

## Changes

- Added `scripts/check_coverage_signal.py`.
- Added `tests/test_coverage_signal.py`.
- Added `coverage-signal` to `Makefile`.
- Documented the checker in `README.md`.

## Reviewer

- reviewer: `019dc3c3-d088-7f91-9bfe-babd08f25ca3`
- result: `found one issue`
- issue: `checker only normalized raw input, so normalized quality-signal payload consumption was not explicitly covered`
- repair: `checker now consumes normalized tool_results payloads directly, keeps raw sample normalization as a producer smoke path, and reports input_payload_kind`

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_coverage_signal.py`: `passed; 6 tests`
- `python -m unittest discover -s tests -p test_normalize_quality_signals.py`: `passed; 3 tests`
- `python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format json`: `passed; status=passed, input_payload_kind=raw_tool_results, coverage_tool_count=1`
- `python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format markdown`: `passed`
- `python -m unittest discover -s tests`: `sandbox failed on Windows Temp/root fixture writes; passed with approved sandbox escalation, 116 tests`
- `python scripts/extract_test_gap_candidates.py --root . --format json`: `passed; coverage-gap-no-producer absent`
- `python scripts/plan_next_task.py --root . --format json`: `passed; next selected 자가개선 루프 통합 검증 부재`
- `python scripts/plan_next_task.py --root . --format markdown`: `passed; next selected 자가개선 루프 통합 검증 부재`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- The previous high-severity coverage signal production gap is gone from test-gap extraction.
- The next planner candidate is `자가개선 루프 통합 검증 부재`.
