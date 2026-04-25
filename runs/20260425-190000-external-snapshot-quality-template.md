# Run Record: External Snapshot Quality Template

- time: `2026-04-25T19:06:00+09:00`
- task: `support external snapshot quality templates`
- score_total: `4`
- topology: `autopilot-single`
- agent_budget: `0`

## Contract

- Let the existing candidate quality template tool accept external candidate snapshot payloads.
- Preserve per-candidate source project ids.
- Do not fabricate rubric scores; all dimensions remain `null` until human scoring.
- Do not write external repositories.

## Changes

- Updated `scripts/prepare_candidate_quality_template.py` to flatten `selfdex_external_candidate_snapshot` payloads.
- Added focused coverage in `tests/test_candidate_quality_template.py`.
- Updated `README.md` to describe planner or external snapshot input.

## Evidence

- External snapshot to template smoke produced `snapshot_candidates=10` and `template_candidates=10`.
- Source projects were preserved for the projects that produced candidates: `apex_analist` and `mqyusimeji`.
- `mqyubot` stayed visible in the snapshot workflow but produced no candidates, so no template rows were fabricated for it.

## Verification

- `python -m compileall -q scripts tests`: `passed`
- `python -m unittest discover -s tests -p test_candidate_quality_template.py`: `passed; ran 4 tests`
- `external snapshot to template smoke`: `passed; snapshot_candidates=10, template_candidates=10`
- `python -m unittest discover -s tests`: `passed after sandbox escalation; ran 131 tests`
- `python scripts/build_external_candidate_snapshot.py --root . --format json`: `passed; project_count=3, candidate_count=10, scanner_error_count=0`
- `python scripts/check_external_validation_readiness.py --root . --format json`: `passed; status=ready, external_project_count=3`
- `python scripts/check_campaign_budget.py --root . --format json`: `passed; status=pass, violation_count=0`
- `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass, finding_count=0`
- `git diff --check`: `passed; exit 0 with LF-to-CRLF warnings`

## Outcome

- External candidates now have a direct path into the candidate quality rubric workflow.
- The remaining risk is candidate usefulness: humans still need to score whether the generated candidates are real, valuable, small, verifiable, and low-risk.
