# Run 20260424-142451-shared-markdown-helper

- goal: Build a bounded recursive improvement harness.
- selected_candidate: clean_markdown_value 중복 정리
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: passed
- next_candidate: parse_args 중복 정리

## Write Sets

- scripts/markdown_utils.py
- scripts/plan_next_task.py
- scripts/check_campaign_budget.py
- tests/test_markdown_utils.py
- README.md
- CAMPAIGN_STATE.md
- STATE.md

## Verification

- python -m compileall -q scripts tests
- python -m unittest discover -s tests
- python .\scripts\check_doc_drift.py --root . --format json
- python .\scripts\check_campaign_budget.py --root . --changed-path scripts/markdown_utils.py --changed-path scripts/plan_next_task.py --changed-path scripts/check_campaign_budget.py --changed-path tests/test_markdown_utils.py --changed-path README.md --changed-path STATE.md --format json
- python .\scripts\plan_next_task.py --root . --format json
- git diff --check
