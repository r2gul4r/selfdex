# Run Record: External Snapshot Validation Report

- time: `2026-04-25T19:25:00+09:00`
- task: `mark unscored external validation reports incomplete`
- score_total: `4`
- topology: `autopilot-single`
- agent_budget: `0`

## Contract

- Allow external validation reports to consume external candidate snapshot payloads.
- Keep missing candidate quality scoring explicit.
- Do not let unscored candidates report `pass`.
- Do not write external repositories.

## Changes

- Extended `scripts/planner_payload_utils.py` so shared candidate extraction can flatten `selfdex_external_candidate_snapshot` payloads.
- Reused that shared path from `scripts/prepare_candidate_quality_template.py`.
- Added snapshot coverage to `tests/test_planner_payload_utils.py`, `tests/test_candidate_quality_template.py`, and `tests/test_external_validation_report.py`.
- Updated `scripts/build_external_validation_report.py` so missing candidate quality scores return `status=needs_scoring` instead of `pass`.

## Evidence

- External snapshot to template smoke produced `snapshot_candidates=10` and `template_candidates=10`.
- External snapshot to validation report smoke for `mqyusimeji` produced `snapshot_candidates=5`, `report_candidates=5`, `status=needs_scoring`, and `candidate-quality-missing`.

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_planner_payload_utils.py`: `passed after sandbox escalation; ran 5 tests`
- `python -m unittest discover -s tests -p test_external_validation_report.py`: `passed after sandbox escalation; ran 5 tests`
- `python -m unittest discover -s tests -p test_candidate_quality_template.py`: `passed; ran 4 tests`
- `python -m unittest discover -s tests`: `passed after sandbox escalation; ran 133 tests`
- `python scripts/check_external_validation_readiness.py --root . --format json`: `passed; status=ready, external_project_count=3`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- External snapshot candidates can now flow into both quality templates and validation reports.
- Reports remain conservative: generated candidates are not treated as proven useful until candidate-quality scoring is supplied.
