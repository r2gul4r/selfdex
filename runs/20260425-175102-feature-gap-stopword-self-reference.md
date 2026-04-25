# Run Record: Feature-Gap Stopword Self-Reference

- time: `2026-04-25T17:55:18+09:00`
- task: `suppress feature-gap detector stopword self-references`
- score_total: `4`
- topology: `autopilot-single`
- agent_budget: `0`

## Contract

- Stop feature-gap extraction from treating detector STOPWORDS signal literals as unfinished feature candidates.
- Preserve real TODO/stub/placeholder detection outside detector self-reference lines.
- Do not change feature-gap output schema, scoring, or planner ranking.

## Changes

- Added `DETECTOR_SIGNAL_LITERAL_WORDS` and literal-line suppression in `scripts/feature_gap_evidence.py`.
- Extended `tests/test_feature_gap_evidence.py` to prove detector literals are skipped while a real TODO remains detected.
- Updated `STATE.md`, `CAMPAIGN_STATE.md`, and this run record.

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_feature_gap_evidence.py`: `passed; 6 tests`
- `python scripts/extract_feature_gap_candidates.py --root . --format json`: `passed; candidate_count=0, small_feature_candidate_count=0`
- `python scripts/plan_next_task.py --root . --format json`: `passed; candidate_count=0, selected=null`
- `python scripts/plan_next_task.py --root . --format markdown`: `passed; selected none`
- `python -m unittest discover -s tests`: `passed with approved sandbox escalation, 118 tests`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- The guarded `feature_gap_evidence` false-positive candidate is gone.
- `plan_next_task.py` currently reports no local improvement candidates.
