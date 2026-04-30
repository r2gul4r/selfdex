# Selfdex

[![check](https://github.com/r2gul4r/selfdex/actions/workflows/check.yml/badge.svg)](https://github.com/r2gul4r/selfdex/actions/workflows/check.yml)

Selfdex is a local AI project lead for Codex work.

Given a target folder, Selfdex reads the project, infers its product and
technical direction, proposes better next moves the user may not have named,
chooses one small safe first step, runs Codex in the target project only after
approval, verifies the result, and records what happened.

It is not just a bugfix finder or code-review helper. Those are baseline
hygiene. The real goal is to help a project keep moving in a better direction
when the user is busy, uncertain, or boxed in by the current shape of the code.

```text
target folder -> understand direction -> find opportunities -> choose one task
-> freeze contract -> run Codex on a branch -> verify -> record -> repeat
```

## North Star

Selfdex should become the control layer between a human and long-running Codex
work:

- understand what the project is trying to become
- notice useful product, workflow, data, or architecture opportunities
- keep normal bugfix, refactor, and test-gap work as baseline hygiene
- select exactly one bounded candidate per loop
- execute only inside an approved target project boundary
- keep high-risk work behind explicit approval
- leave enough evidence that the run can be reviewed, resumed, or reverted

The strongest Selfdex candidate is not merely "a small issue exists." It is:

```text
This project would be better if we moved in this direction,
and this is the smallest safe first step.
```

## Operating Model

Selfdex is user-invoked. It is not a background daemon and it does not silently
rewrite projects.

The normal loop is:

1. Pick or receive a target folder.
2. Infer the project direction: purpose, audience, product signals, technical
   signals, constraints, and strategic opportunities.
3. Scan repository hygiene signals: test gaps, refactor opportunities, feature
   gaps, TODOs, stubs, and placeholders.
4. Rank direction opportunities before routine hygiene when the evidence is
   strong enough.
5. Freeze one task contract: outcome, write boundary, non-goals, checks, and
   stop conditions.
6. Create an isolated branch in the target repository when execution is
   approved.
7. Start a target-project Codex session from that target `cwd`.
8. Run verification or record exactly why verification was skipped.
9. Record result, changed files, checks, repair attempts, and stop/failure
   reason under Selfdex `runs/<project_key>/`.

## Safety Contract

Selfdex can be aggressive about finding better work, but conservative about
side effects.

Hard approval is still required for:

- destructive filesystem or Git history operations
- secrets, credentials, private keys, or token access
- paid API calls
- public deploys
- database migrations or production writes
- cross-workspace changes outside the approved target boundary
- global Codex config, installer, plugin, or MCP setup changes

Folder approval can let Selfdex work inside a target repository, but it does
not bypass those hard zones.

## Current Capabilities

Implemented pieces:

- `scripts/build_project_direction.py` infers a project direction snapshot from
  local repository evidence.
- `scripts/build_external_candidate_snapshot.py` combines direction
  opportunities with test-gap, refactor, and feature-gap candidates, then adds
  cluster and run-history metadata.
- `scripts/plan_external_project.py` freezes one target-project task contract
  and generates a Codex execution prompt while separating evidence-only files
  from proposed write files.
- `scripts/run_target_codex.py` can plan one candidate, create a target branch
  in execution mode, call a Codex app-server adapter, and write a project-scoped
  run artifact with bounded timeout and branch metadata.
- `scripts/build_external_validation_package.py` writes read-only external
  validation snapshots, scores, reports, and summary artifacts under
  `runs/external-validation/`.
- `scripts/check_campaign_budget.py` checks that the current work stays inside
  the frozen Selfdex contract.
- `scripts/check_doc_drift.py` keeps this README aligned with repo tools.

Still intentionally bounded:

- no background polling loop
- no autonomous multi-candidate execution
- no unapproved writes to target projects
- no automatic bypass for secrets, deploys, paid APIs, databases, or destructive
  commands
- no claim that read-only validation replaces target-project implementation
  evidence

## Quick Start

Inspect Selfdex itself:

```bash
python scripts/build_project_direction.py --root . --format markdown
python scripts/plan_next_task.py --root . --format markdown
```

Inspect registered external projects read-only:

```bash
python scripts/check_external_validation_readiness.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --project-id daboyeo --format markdown
```

Reproduce the external validation proof package:

```bash
python scripts/build_external_validation_package.py --root . --format markdown
```

The package writes:

```text
runs/external-validation/<project_id>-snapshot.md
runs/external-validation/<project_id>-human-score.md
runs/external-validation/<project_id>-report.md
runs/external-validation/summary.md
```

Build a target-project contract without editing the target:

```bash
python scripts/plan_external_project.py --root . --project-root ../daboyeo --project-name daboyeo --format markdown
```

Run the target-project orchestrator in dry-run mode:

```bash
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --format markdown
```

When target execution is explicitly approved, add `--execute`:

```bash
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --execute --format markdown
```

Maintenance checks:

```bash
python scripts/check_campaign_budget.py --root . --format markdown
python scripts/check_doc_drift.py --root . --format markdown
python scripts/collect_repo_metrics.py --root . --pretty
python scripts/extract_test_gap_candidates.py --root . --format markdown
```

## Records

Selfdex records target-project runs centrally, not inside the target project by
default.

```text
runs/<project_key>/<YYYYMMDD-HHMMSS>-<task-slug>.md
```

Each run artifact should include:

- project id, project root, and branch
- selected candidate
- frozen task contract
- Codex thread or session id when available
- changed files
- verification commands and results
- repair attempts
- final status: `completed`, `failed`, `blocked`, or `stopped`
- failure or stop reason

## Repository Map

Core control files:

- `AGENTS.md` defines repository execution rules.
- `AUTOPILOT.md` defines the long-running supervised loop.
- `CAMPAIGN_STATE.md` tracks campaign-level intent, budget, locks, and latest
  run.
- `STATE.md` tracks the active task contract and write ownership.
- `project_registry.json` is the tool-readable project registry source of
  truth.
- `PROJECT_REGISTRY.md` mirrors the registry for humans and records the
  read-only boundary.
- `docs/SELFDEX_FINAL_GOAL.md` is the north-star contract.
- `docs/CANDIDATE_QUALITY_RUBRIC.md` defines human scoring for candidate
  usefulness.
- `docs/SELFDEX_HANDOFF.md` keeps cross-machine continuity notes.
- `docs/ORCHESTRATION_DECISION_PLAN.md` describes orchestration-fit decisions.
- `runs/` stores run evidence.

Tooling:

- `scripts/*.py` contains the local scanners, planners, recorders, checkers,
  and target Codex runner.
- `examples/quality_signal_samples.json`,
  `examples/external_validation_planner_sample.json`, and
  `examples/candidate_quality_sample.json` are sample payloads for validation
  and reporting tools.

## Verification

Use the narrow checks for README and contract changes:

```bash
python scripts/check_doc_drift.py --root . --format json
python scripts/check_campaign_budget.py --root . --include-git-diff --format json
git diff --check
```

Use the full repo checks after code or workflow changes:

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests
python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format json
python scripts/build_project_direction.py --root . --format json
python scripts/build_external_candidate_snapshot.py --root . --format json
python scripts/build_external_validation_package.py --root . --format json
python scripts/plan_external_project.py --root . --project-id daboyeo --format json
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --format json
```

CI runs the same baseline through `.github/workflows/check.yml` with
`make check`.

## Design Bias

Selfdex should be willing to challenge the current project shape, but only in
reviewable increments.

The project should prefer:

- direction before hygiene
- evidence before edits
- one candidate before loops
- branch isolation before target writes
- local verification before confidence
- recorded outcomes before memory
- small reversible progress before broad autonomy
