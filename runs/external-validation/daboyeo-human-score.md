# External Validation Human Score

- project_id: `daboyeo`
- scoring_mode: `operator_scored_from_read_only_evidence`
- candidate_count: `3`

## Rubric

- `real_problem`: 0-3
- `user_value`: 0-3
- `local_verifiability`: 0-3
- `scope_smallness`: 0-3
- `risk_reversibility`: 0-3

## Scores

### showtime_payload 중복 정리

- verdict: `strong`
- total: `14`
- real_problem: `3`
- user_value: `2`
- local_verifiability: `3`
- scope_smallness: `3`
- risk_reversibility: `3`
- evidence: 공통 축 판정: goal_alignment=pass, gap_relevance=medium, safety=safe, reversibility=strong, structural_impact=low, leverage=high
- suggested_verification: `python -m compileall -q scripts`

### scripts/ingest/collect_all_to_tidb.py 책임 분리와 경계 정리

- verdict: `strong`
- total: `13`
- real_problem: `3`
- user_value: `2`
- local_verifiability: `3`
- scope_smallness: `2`
- risk_reversibility: `3`
- evidence: 공통 축 판정: goal_alignment=pass, gap_relevance=high, safety=guarded, reversibility=strong, structural_impact=medium, leverage=high
- suggested_verification: `python -m compileall -q scripts`

### ingest_lotte + ingest_megabox 중복 정리

- verdict: `strong`
- total: `14`
- real_problem: `3`
- user_value: `2`
- local_verifiability: `3`
- scope_smallness: `3`
- risk_reversibility: `3`
- evidence: 공통 축 판정: goal_alignment=pass, gap_relevance=high, safety=safe, reversibility=strong, structural_impact=low, leverage=high
- suggested_verification: `python -m compileall -q scripts`
