# Run 20260424-140456-doc-drift-checker

- goal: Build a bounded recursive improvement harness.
- selected_candidate: Add generated report drift checks for Selfdex docs.
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 1
- result: passed
- next_candidate: fallback to scan-based candidate

## Write Sets

- scripts/check_doc_drift.py
- tests/test_doc_drift.py
- README.md
- CAMPAIGN_STATE.md
- STATE.md

## Verification

- python -m compileall -q scripts tests
- python -m unittest discover -s tests
- python .\scripts\check_doc_drift.py --root . --format json
- python .\scripts\check_campaign_budget.py --root . --changed-path scripts/check_doc_drift.py --changed-path tests/test_doc_drift.py --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json
- python .\scripts\plan_next_task.py --root . --format json
- git diff --check
