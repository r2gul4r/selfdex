# Selfdex

Selfdex is a bounded, auditable local control harness for long-running Codex
work.

The final goal is a supervised improvement harness, defined in
`docs/SELFDEX_FINAL_GOAL.md`. The goal is not to replace safety or prove a
general autonomous developer. The goal is to make long-running Codex work easier
to choose, freeze, verify, audit, and resume:

```text
register projects -> scan -> ask -> classify -> rank -> freeze -> orchestrate -> implement -> verify -> record -> repeat
```

`codex_multiagent` stays the conservative safety baseline. This repository is a
local operating layer for Codex sessions: it records task contracts, write
boundaries, verification commands, evidence, and resume context while keeping
high-risk actions behind explicit approval.

## Default Behavior

- Choose a small next task from repository signals and campaign context.
- Freeze acceptance criteria, non-goals, write boundaries, and verification
  commands before implementation.
- Recommend explorer, worker, and reviewer lanes when they reduce risk or time;
  actual spawning still depends on host capability and explicit task authority.
- Keep destructive actions, secrets, deploys, paid calls, database writes,
  production changes, and cross-workspace writes behind hard approval.
- Keep each loop auditable and resumable through `CAMPAIGN_STATE.md`,
  `STATE.md`, and `runs/`.

## Validation Status

Selfdex has an internal quality loop, but it has not yet proven general
usefulness on external repositories. Before claiming broader value, it should
scan 2-3 explicitly registered external projects read-only and show that its top
candidates are real, valuable, small, locally verifiable, and low-risk according
to the candidate quality rubric and human review.

The first step toward modifying a user-selected project is read-only external
planning: Selfdex scans the target, selects one small candidate, freezes a
proposed task contract, and emits a Codex execution prompt. Target-project
writes still require explicit user approval and should happen later in an
isolated branch or worktree.

## Core Files

| Path | Role |
| :-- | :-- |
| `AGENTS.md` | Repository execution rules for bounded Codex work |
| `AUTOPILOT.md` | Long-running autopilot policy and loop design |
| `CAMPAIGN_STATE.md` | Current campaign goal, budget, locks, and guardrails |
| `STATE.md` | Current task contract and write ownership |
| `PROJECT_REGISTRY.md` | Registered projects for read-only multi-project analysis |
| `docs/CANDIDATE_QUALITY_RUBRIC.md` | Human scoring rubric for useful, small, verifiable candidates |
| `docs/SELFDEX_FINAL_GOAL.md` | Final goal, roadmap, and recursive improvement contract |
| `docs/SELFDEX_HANDOFF.md` | Cross-machine handoff memory for continuing the campaign |
| `docs/ORCHESTRATION_DECISION_PLAN.md` | Planner execution-fit model for safe multi-agent acceleration |
| `runs/` | Per-run records and evidence |
| `scripts/plan_next_task.py` | Selects the next candidate from repository signals |
| `scripts/check_campaign_budget.py` | Rejects campaign budget and write-contract violations |
| `scripts/check_doc_drift.py` | Checks README drift against generated-report scripts |
| `scripts/check_external_validation_readiness.py` | Reports whether 2-3 external read-only projects are registered for validation |
| `scripts/argparse_utils.py` | Shared argparse option helpers for local scripts |
| `scripts/candidate_scoring_utils.py` | Shared candidate scoring axes and priority grade helpers |
| `scripts/cli_output_utils.py` | Shared JSON/markdown stdout helpers for report CLIs |
| `scripts/markdown_utils.py` | Shared markdown parsing helpers for local scripts |
| `scripts/repo_area_utils.py` | Shared repository area labels and classifiers |
| `scripts/repo_scan_excludes.py` | Shared generated/dependency directory exclusions for repository scanners |
| `scripts/repo_metrics_utils.py` | Shared file metric models and line-analysis helpers |
| `scripts/repo_quality_signal_utils.py` | Shared repo metric quality-signal scoring helpers |
| `scripts/symbol_definition_utils.py` | Shared Python/shell/PowerShell symbol-definition extraction helpers |
| `scripts/tool_result_utils.py` | Shared tool-result issue and coverage parsing helpers |
| `scripts/check_coverage_signal.py` | Verifies that normalized quality-tool samples produce a coverage signal |
| `scripts/list_project_registry.py` | Lists registered projects without scanning or writing to them |
| `scripts/collect_repo_metrics.py` | Repository metric scanner |
| `scripts/feature_gap_evidence.py` | Feature-gap evidence, call-flow, test-coverage, and gap assessment helpers |
| `scripts/feature_file_records.py` | Shared file-record and symbol helpers for feature-gap candidate extraction |
| `scripts/feature_small_candidates.py` | Small-feature scoring and candidate construction helpers |
| `scripts/extract_*_candidates.py` | Feature/test/refactor candidate extractors |
| `scripts/evaluate_candidate_quality.py` | Scores candidate quality rubric payloads |
| `scripts/build_external_candidate_snapshot.py` | Builds read-only top-candidate snapshots for registered external projects |
| `scripts/plan_external_project.py` | Builds a read-only task contract and Codex execution prompt for one selected external project |
| `scripts/build_external_validation_report.py` | Builds read-only validation reports from planner and quality payloads |
| `scripts/prepare_candidate_quality_template.py` | Converts planner or external snapshot output into human scoring templates |
| `scripts/normalize_quality_signals.py` | Normalizes scan outputs into priority signals |
| `scripts/record_run.py` | Writes compact run evidence under `runs/` |
| `scripts/plan_orchestration_fit.py` | Planner task-size and orchestration-fit heuristics |
| `scripts/planner_payload_utils.py` | Shared planner JSON loading and candidate extraction helpers |
| `scripts/planner_text_utils.py` | Planner campaign text parsing and work-type classification helpers |
| `scripts/refactor_file_records.py` | Shared file-record and symbol helpers for refactor candidate extraction |
| `scripts/refactor_metrics_payload.py` | Metrics loading and filtering helpers for refactor candidate extraction |
| `examples/quality_signal_samples.json` | Sample quality-tool payload for normalizer demos |
| `examples/external_validation_planner_sample.json` | Sample planner payload for validation report demos |
| `examples/candidate_quality_sample.json` | Sample candidate quality payload for validation report demos |

## Quick Start

```bash
python scripts/plan_next_task.py --root . --format markdown
python scripts/check_campaign_budget.py --root . --format markdown
python scripts/check_doc_drift.py --root . --format markdown
python scripts/check_external_validation_readiness.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --project-id apex_analist --format markdown
python scripts/build_external_candidate_snapshot.py --root . --project-id apex_analist --project-id mqyusimeji --format markdown
python scripts/plan_external_project.py --root . --project-id apex_analist --format markdown
python scripts/plan_external_project.py --root . --project-root ../apex_analist --project-name apex_analist --format markdown
python scripts/collect_repo_metrics.py --root . --pretty
python scripts/normalize_quality_signals.py --input examples/quality_signal_samples.json --pretty
python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format markdown
python scripts/extract_test_gap_candidates.py --root . --format markdown
```

## Verification

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests
python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format json
python scripts/plan_next_task.py --root . --format json
python scripts/plan_next_task.py --root . --format markdown
python scripts/check_campaign_budget.py --root . --format json
python scripts/check_doc_drift.py --root . --format json
python scripts/check_external_validation_readiness.py --root . --format json
python scripts/build_external_candidate_snapshot.py --root . --format json
python scripts/plan_external_project.py --root . --project-id apex_analist --format json
git diff --check
```
