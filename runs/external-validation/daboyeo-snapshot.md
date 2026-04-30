# External Candidate Snapshot

- validation_mode: `read_only`
- external_value_proven: `False`
- project_count: `1`
- candidate_count: `3`
- scanner_error_count: `0`
- human_review_status: `pending`

## Selection

- mode: `package_project`
- requested_project_ids: `daboyeo`
- selected_project_ids: `daboyeo`
- missing_project_ids: `none`

## Projects

### daboyeo

- status: `scanned`
- write_policy: `read-only`
- candidate_count: `3`
- human_review_status: `pending`
- project_direction: daboyeo is the clearest documented project anchor.
- top_candidates:
  - `refactor` score=`54.05` decision=`pick` title=ingest_lotte + ingest_megabox 중복 정리
  - `refactor` score=`51.75` decision=`pick` title=showtime_payload 중복 정리
  - `refactor` score=`49.45` decision=`pick` title=scripts/ingest/collect_all_to_tidb.py 책임 분리와 경계 정리
