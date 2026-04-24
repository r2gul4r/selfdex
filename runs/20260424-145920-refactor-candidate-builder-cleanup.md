# Run 20260424-145920-refactor-candidate-builder-cleanup

- goal: Share refactor candidate scoring and payload assembly without changing candidate schemas.
- selected_candidate: build_duplicate_candidate + build_hotspot_candidate 중복 정리
- topology: autopilot-single
- agent_budget: 0
- repair_attempts: 0
- result: Shared refactor candidate scoring and payload assembly; duplicate and hotspot builders keep candidate-specific source signals.
- next_candidate: extract_markdown_section 중복 정리

## Write Sets

- scripts/extract_refactor_candidates.py
- tests/test_candidate_extractors.py
- STATE.md

## Verification

- python -m compileall -q scripts tests: passed
- python -m unittest discover -s tests: passed; 43 tests
- extract_refactor_candidates json/markdown: passed
- check_campaign_budget json: passed; violation_count=0
- plan_next_task json/markdown: passed; next=extract_markdown_section 중복 정리
- git diff --check: passed with LF-to-CRLF warnings for extract_refactor_candidates.py and test_candidate_extractors.py
