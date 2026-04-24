# Run 20260424-150256-doc-drift-markdown-helper

- goal: Reuse shared markdown section parsing in doc drift checks without behavior changes.
- selected_candidate: extract_markdown_section 중복 정리
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: check_doc_drift.py now reuses markdown_utils.extract_markdown_section and preserves Quick Start detection.
- next_candidate: scripts/collect_repo_metrics.py 책임 분리와 경계 정리

## Write Sets

- scripts/check_doc_drift.py
- STATE.md

## Verification

- python -m compileall -q scripts tests: passed
- python -m unittest discover -s tests: passed; 43 tests
- check_doc_drift json: passed; finding_count=0
- check_campaign_budget json: passed; violation_count=0
- plan_next_task json/markdown: passed; next=scripts/collect_repo_metrics.py 책임 분리와 경계 정리
- git diff --check: passed with LF-to-CRLF warning for check_doc_drift.py
