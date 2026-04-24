# Run 20260424-143948-shared-extractor-helpers

- goal: Share extractor argparse and area classification helpers without changing CLI outputs.
- selected_candidate: parse_args 중복 정리
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Shared argparse and repository area helpers added; extractor scripts now use common helpers and planner advances to the next refactor candidate.
- next_candidate: scripts/normalize_quality_signals.py 책임 분리와 경계 정리

## Write Sets

- scripts/argparse_utils.py
- scripts/repo_area_utils.py
- scripts/extract_feature_gap_candidates.py
- scripts/extract_refactor_candidates.py
- tests/test_argparse_utils.py
- tests/test_repo_area_utils.py
- README.md
- STATE.md

## Verification

- python -m compileall -q scripts tests: passed
- python -m unittest discover -s tests: passed; 37 tests
- check_doc_drift json: passed; finding_count=0
- extract_feature_gap_candidates json: passed
- extract_refactor_candidates json: passed
- plan_next_task json/markdown: passed; next=scripts/normalize_quality_signals.py 책임 분리와 경계 정리
- git diff --check: passed with LF-to-CRLF warnings for two extractor files
