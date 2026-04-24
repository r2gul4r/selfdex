# Run 20260424-145351-normalizer-helper-extraction

- goal: Split normalizer scoring and parsing helpers without changing output schemas.
- selected_candidate: scripts/normalize_quality_signals.py 책임 분리와 경계 정리
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 1
- result: Split repo quality scoring and tool-result parsing into focused helpers; normalize_quality_signals.py dropped below hotspot thresholds and planner advanced.
- next_candidate: build_duplicate_candidate + build_hotspot_candidate 중복 정리

## Write Sets

- scripts/repo_quality_signal_utils.py
- scripts/tool_result_utils.py
- scripts/normalize_quality_signals.py
- tests/test_repo_quality_signal_utils.py
- tests/test_tool_result_utils.py
- tests/test_normalize_quality_signals.py
- README.md
- STATE.md

## Verification

- python -m compileall -q scripts tests: passed
- python -m unittest discover -s tests: passed; 42 tests
- check_doc_drift json: passed; finding_count=0
- collect_repo_metrics | normalize_quality_signals: passed
- check_campaign_budget json: passed; violation_count=0
- plan_next_task json/markdown: passed; next=build_duplicate_candidate + build_hotspot_candidate 중복 정리
- git diff --check: passed with LF-to-CRLF warning for normalize_quality_signals.py
