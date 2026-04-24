# Run 20260424-164000-plan-orchestration-fit-split

- goal: Split orchestration-fit heuristics out of plan_next_task.py
- selected_candidate: scripts/plan_next_task.py 책임 분리와 경계 정리
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Extracted orchestration-fit dataclass and heuristics into scripts/plan_orchestration_fit.py, added focused tests, and kept planner schema stable.
- next_candidate: scripts/collect_repo_metrics.py 책임 분리와 경계 정리

## Write Sets

- scripts/plan_next_task.py
- scripts/plan_orchestration_fit.py
- tests/test_plan_orchestration_fit.py
- README.md
- CAMPAIGN_STATE.md
- STATE.md

## Verification

- python -m compileall -q scripts tests: passed
- python -m unittest discover -s tests: passed; 50 tests
- plan_next_task json/markdown: passed; next=scripts/collect_repo_metrics.py 책임 분리와 경계 정리
- check_campaign_budget: passed; violation_count=0
- check_doc_drift: passed; finding_count=0
- git diff --check: passed with LF-to-CRLF warning for scripts/plan_next_task.py
