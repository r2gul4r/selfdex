# Run 20260424-171000-collect-metrics-utils-split

- goal: Split file metric models and line analysis out of collect_repo_metrics.py
- selected_candidate: scripts/collect_repo_metrics.py 책임 분리와 경계 정리
- topology: autopilot-single-plus-reviewer
- agent_budget: 1
- repair_attempts: 1
- result: Extracted file metric models and line-analysis helpers into scripts/repo_metrics_utils.py, added focused helper and CLI bootstrap tests, and preserved collector schema.
- next_candidate: scripts/extract_refactor_candidates.py 책임 분리와 경계 정리

## Write Sets

- scripts/collect_repo_metrics.py
- scripts/repo_metrics_utils.py
- tests/test_repo_metrics_utils.py
- README.md
- CAMPAIGN_STATE.md
- STATE.md

## Verification

- python -m compileall -q scripts tests: passed
- python -m unittest discover -s tests: passed; 55 tests
- collect_repo_metrics direct smoke: passed
- collect_repo_metrics module smoke: passed
- plan_next_task json/markdown: passed; next=scripts/extract_refactor_candidates.py 책임 분리와 경계 정리
- check_campaign_budget: passed; violation_count=0
- check_doc_drift: passed; finding_count=0
- git diff --check: passed with LF-to-CRLF warning for scripts/collect_repo_metrics.py
- reviewer Boole: found import-boundary/test gap; fixed
