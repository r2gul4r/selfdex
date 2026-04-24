# Run 20260424-140032-campaign-budget-checker

- goal: Build a bounded recursive improvement harness.
- selected_candidate: Add a campaign budget checker that rejects out-of-contract work.
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: passed
- next_candidate: Add generated report drift checks for Selfdex docs.

## Write Sets

- scripts/check_campaign_budget.py
- tests/test_campaign_budget.py
- README.md
- CAMPAIGN_STATE.md
- STATE.md

## Verification

- python -m compileall -q scripts tests
- python -m unittest discover -s tests
- python .\scripts\check_campaign_budget.py --root . --changed-path scripts/check_campaign_budget.py --changed-path tests/test_campaign_budget.py --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path STATE.md --format json
- python .\scripts\plan_next_task.py --root . --format json
- git diff --check
