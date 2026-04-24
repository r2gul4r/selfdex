# Run 20260424-142036-normalize-coverage-parser

- goal: Build a bounded recursive improvement harness.
- selected_candidate: normalize_quality_signals coverage parser helper extraction
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: passed
- next_candidate: continue normalize_quality_signals.py hotspot split

## Write Sets

- scripts/normalize_quality_signals.py
- tests/test_normalize_quality_signals.py
- CAMPAIGN_STATE.md
- STATE.md

## Verification

- python -m compileall -q scripts tests
- python -m unittest discover -s tests
- python .\scripts\collect_repo_metrics.py --root . | python .\scripts\normalize_quality_signals.py
- python .\scripts\check_campaign_budget.py --root . --changed-path scripts/normalize_quality_signals.py --changed-path tests/test_normalize_quality_signals.py --changed-path STATE.md --format json
- git diff --check
