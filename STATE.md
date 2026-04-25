# STATE

## Current Task

- task: `extract refactor candidate file-record helpers`
- phase: `closeout`
- scope: `split file reading, symbol extraction, file record construction, enclosing-symbol lookup, and symbol span helpers out of scripts/extract_refactor_candidates.py without changing report schema or candidate ranking`
- verification_target: `candidate extractor tests, full unittest suite, refactor extractor smoke, plan_next_task smoke, campaign budget, doc drift, git diff --check, bounded baseline repair`

## Orchestration Profile

- score_total: `8`
- score_breakdown:
  - `large_hotspot_refactor`: 2
  - `shared_candidate_contract`: 1
  - `verification_sensitive_output_schema`: 1
  - `separable_read_only_exploration`: 1
  - `reviewer_value_after_patch`: 1
  - `user_standing_subagent_authorization`: 1
  - `baseline_repair_blocker`: 1
- hard_triggers:
  - `large_hotspot_refactor`
  - `verification_sensitive_output_schema`
  - `verification_failure_observed`
- selected_rules:
  - `freeze_before_implementation`
  - `bounded_helper_extraction`
  - `schema_preservation`
  - `standing_subagent_authorization_applies`
  - `bounded_repair_loop`
  - `verification_required`
- selected_skills:
  - `none`
- execution_topology: `autopilot-mixed`
- orchestration_value: `medium`
- agent_budget: `2`
- efficiency_basis: `read-only boundary scouting can run beside main preparation, and a reviewer can check schema/import risks after the patch`
- spawn_decision: `spawn one explorer for read-only boundary recommendation; reserve one reviewer after implementation`
- selection_reason: `The prior handoff task is complete. The latest run and planner candidate point to scripts/extract_refactor_candidates.py as a large refactor hotspot, and the user granted standing authorization for useful subagent delegation.`

## Evaluation Plan

- evaluation_need: `medium`
- project_invariants:
  - `Do not change candidate schema, ranking, Korean markdown report text, or default CLI behavior.`
  - `If full-suite verification exposes a baseline blocker, repair only the minimal blocker needed to restore the suite.`
  - `Do not start the broader scripts/plan_next_task.py or extract_feature_gap_candidates.py split in this task.`
  - `Keep shared state and run records under main ownership.`
- task_acceptance:
  - `Move SymbolLocation, FileRecord, regex patterns, read_text_lines, extract_definitions, build_file_records, find_enclosing_symbol, and symbol_spans out of scripts/extract_refactor_candidates.py into a focused helper module.`
  - `Keep scripts/extract_refactor_candidates.py public behavior equivalent for existing tests and smoke output.`
  - `Add focused tests for the extracted helper behavior or update existing candidate extractor tests to cover the helper boundary.`
  - `Repair the reverted Windows path baseline issue in scripts/repo_metrics_utils.py if needed for full-suite verification.`
  - `Record the run and update campaign latest run.`
- non_goals:
  - `Do not refactor scoring, candidate payload construction, markdown rendering, or planner logic.`
  - `Do not modify global Codex config, installers, secrets, deploys, paid APIs, databases, or cross-workspace files.`
  - `Do not commit unless separately requested.`
- hard_checks:
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format json`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path STATE.md --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path ERROR_LOG.md --changed-path .gitignore --changed-path runs/20260425-132016-refactor-candidate-file-record-helpers.md --changed-path scripts/extract_refactor_candidates.py --changed-path scripts/refactor_file_records.py --changed-path tests/test_refactor_file_records.py --changed-path tests/test_candidate_extractors.py --changed-path scripts/repo_metrics_utils.py --format markdown`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format markdown`
  - `git diff --check`
- llm_review_rubric:
  - `Check whether moved helpers preserve line numbers and symbol names for python, shell, and powershell files.`
  - `Check whether direct script and module-style imports remain safe.`
  - `Check whether the refactor extractor schema and top candidate still match expectations.`
- evidence_required:
  - `explorer boundary note`
  - `reviewer result`
  - `full unittest result`
  - `refactor extractor smoke result`
  - `budget and doc drift result`

## Writer Slot

- writer_slot: `main`
- write_set: `refactor candidate file-record helper extraction`
- write_sets:
  - `main`:
    - `STATE.md`
    - `README.md`
    - `CAMPAIGN_STATE.md`
    - `ERROR_LOG.md`
    - `./.gitignore`
    - `runs/20260425-132016-refactor-candidate-file-record-helpers.md`
    - `scripts/extract_refactor_candidates.py`
    - `scripts/refactor_file_records.py`
    - `tests/test_refactor_file_records.py`
    - `tests/test_candidate_extractors.py`
    - `scripts/repo_metrics_utils.py`
  - `explorer`:
    - `read-only: scripts/extract_refactor_candidates.py, tests/test_candidate_extractors.py, related helper modules`
  - `reviewer`:
    - `read-only: final diff, schema/import/test risk`
- shared_assets_owner: `main`

## Contract Freeze

- Extract only file-record and symbol-location helpers from `scripts/extract_refactor_candidates.py`.
- New helper path is `scripts/refactor_file_records.py`.
- Main owns all writes; explorer and reviewer are read-only.
- Preserve CLI output shape and existing candidate ordering.
- Restore only the one-line `repo_metrics_utils.py` path normalization repair if full-suite verification is blocked by the reverted Windows temp path bug.
- Ignore root-scoped sandbox temp directories only if failed sandbox test runs leave inaccessible scratch directories.
- Use bundled Python executable when `python` is not on PATH.

## Reviewer

- reviewer: `reserved`
- reviewer_target: `final diff after implementation`
- reviewer_focus: `schema drift, import boundary, missing tests`

## Last Update

- timestamp: `2026-04-25T13:26:37+09:00`
- phase: `closeout`
- status: `file-record helper extraction completed, reviewer import-boundary finding fixed, and verification passed.`
- verification_result:
  - `explorer`: `completed; recommended same file-record/symbol-helper boundary`
  - `python -m unittest discover -s tests -p test_refactor_file_records.py`: `passed; ran 3 tests through sandbox escalation`
  - `python -m unittest discover -s tests -p test_candidate_extractors.py`: `passed; ran 4 tests through sandbox escalation`
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests`: `failed; reverted scripts/repo_metrics_utils.py Windows path canonicalization bug`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format markdown`: `failed; README.md must document scripts/refactor_file_records.py`
  - `reviewer`: `found missing module-style import coverage for scripts.extract_refactor_candidates fallback path; adding script/module CLI fixture test`
  - `python -m unittest discover -s tests -p test_candidate_extractors.py`: `passed after reviewer fix; ran 5 tests through sandbox escalation`
  - `python -m unittest discover -s tests`: `passed; ran 59 tests through sandbox escalation`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\extract_refactor_candidates.py --root . --format json`: `passed; schema_version=1, refactor_candidate_count=5`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\plan_next_task.py --root . --format markdown`: `passed; next candidate remains scripts/extract_refactor_candidates.py responsibility split`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_doc_drift.py --root . --format markdown`: `passed; finding_count=0`
  - `$env:PYTHONIOENCODING='utf-8'; python .\scripts\check_campaign_budget.py --root . --changed-path STATE.md --changed-path README.md --changed-path CAMPAIGN_STATE.md --changed-path ERROR_LOG.md --changed-path .gitignore --changed-path runs/20260425-132016-refactor-candidate-file-record-helpers.md --changed-path scripts/extract_refactor_candidates.py --changed-path scripts/refactor_file_records.py --changed-path tests/test_refactor_file_records.py --changed-path tests/test_candidate_extractors.py --changed-path scripts/repo_metrics_utils.py --format markdown`: `passed; violation_count=0`
  - `git diff --check`: `passed; exit 0 with LF-to-CRLF working-copy warnings`

## Retrospective

- task: `extract refactor candidate file-record helpers`
- score_total: `8`
- selected_profile: `autopilot-mixed`
- actual_topology: `autopilot-mixed; explorer and reviewer sidecars used`
- verification_outcome: `passed`
- collisions_or_reclassifications: `reclassified from completed handoff task to next refactor candidate`
- next_rule_change: `none`
