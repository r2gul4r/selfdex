# STATE

## Current Task

- task: `add project direction intelligence to target candidate planning`
- phase: `verified`
- scope: `teach Selfdex to infer project purpose and strategic opportunities, then feed direction-aware candidates into target project planning before routine bugfix/refactor hygiene`
- verification_target: `focused project direction tests, external snapshot/plan tests, campaign budget, and repository smoke checks`

## Orchestration Profile

- score_total: `7`
- score_breakdown:
  - `candidate_policy_change`: 2
  - `project_understanding_layer`: 2
  - `external_snapshot_integration`: 1
  - `target_prompt_contract_change`: 1
  - `tests_and_docs_update`: 1
- hard_triggers:
  - `workflow_policy_change`
  - `ambiguous_acceptance_criteria`
  - `project_direction_inference`
- selected_rules:
  - `state_before_writes`
  - `single_write_lane`
  - `direction_before_hygiene`
  - `evidence_backed_opportunities`
  - `verification_required`
- selected_skills:
  - `selfdex-autopilot`
- execution_topology: `autopilot-single`
- orchestration_value: `low`
- agent_budget: `0`
- efficiency_basis: `The candidate extraction, scoring, prompt, and tests form one coupled policy path; host policy does not grant subagent spawning for this turn.`
- spawn_decision: `no_spawn_host_policy_and_coupled_policy_surface`
- selection_reason: `The user clarified that Selfdex should understand project direction and propose growth opportunities, not merely perform code review, small bugfixes, and hygiene work.`

## Evaluation Plan

- evaluation_need: `full`
- project_invariants:
  - `Do not modify external project files during this implementation.`
  - `Do not call paid or external LLM APIs to infer direction.`
  - `Do not touch secrets, deploys, paid APIs, databases, production systems, installers, or global Codex config.`
  - `Preserve existing GPT-5.5 prompt and repo skill changes already in the working tree.`
  - `Strategic opportunities must remain evidence-backed and bounded to a small first step.`
- task_acceptance:
  - `Selfdex can generate a project direction snapshot with purpose, audience, product signals, technical signals, constraints, and strategic opportunities.`
  - `Direction opportunities become candidate source entries in external target snapshots.`
  - `Direction candidates are scored on strategic fit, user value, novelty, feasibility, verifiability, reversibility, and evidence strength.`
  - `Target Codex contracts include project direction context and explicitly frame the work as project evolution, not only cleanup.`
  - `Existing hygiene candidates remain available as baseline work.`
- non_goals:
  - `Do not implement a daemon, polling loop, or background optimizer.`
  - `Do not use an external model call for direction inference in tests or normal local scans.`
  - `Do not remove bugfix, refactor, or test-gap candidate sources.`
  - `Do not run real target-project Codex execution as part of verification.`
- hard_checks:
  - `python -m unittest discover -s tests -p test_build_project_direction.py`
  - `python -m unittest discover -s tests -p test_build_external_candidate_snapshot.py`
  - `python -m unittest discover -s tests -p test_plan_external_project.py`
  - `python -m unittest discover -s tests -p test_campaign_budget.py`
  - `python -m compileall -q scripts tests`
  - `python -m unittest discover -s tests`
  - `python scripts/check_doc_drift.py --root . --format json`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`
  - `git diff --check`
- llm_review_rubric:
  - `Check strategic candidates are grounded in repository evidence, not vague product advice.`
  - `Check the selected candidate prompt still freezes a small first step.`
  - `Check routine hygiene sources remain available and are not silently discarded.`
- evidence_required:
  - `project direction extractor tests`
  - `external snapshot integration tests`
  - `target plan prompt tests`
  - `campaign budget acceptance`

## Writer Slot

- writer_slot: `main`
- write_set: `project direction intelligence and candidate planning`
- write_sets:
  - `main`:
    - `STATE.md`
    - `CAMPAIGN_STATE.md`
    - `README.md`
    - `AUTOPILOT.md`
    - `docs/SELFDEX_FINAL_GOAL.md`
    - `scripts/build_project_direction.py`
    - `scripts/build_external_candidate_snapshot.py`
    - `scripts/plan_external_project.py`
    - `scripts/planner_text_utils.py`
    - `scripts/check_campaign_budget.py`
    - `tests/test_build_project_direction.py`
    - `tests/test_external_candidate_snapshot.py`
    - `tests/test_plan_external_project.py`
    - `tests/test_campaign_budget.py`
    - `runs/selfdex/20260430-114700-project-direction-intelligence.md`
    - `runs/selfdex/20260430-111200-target-codex-orchestrator.md`
    - `AGENTS.md`
    - `ERROR_LOG.md`
    - `.agents/skills/selfdex-autopilot/SKILL.md`
    - `runs/20260430-104000-gpt55-codex-skill-update.md`
- shared_assets_owner: `main`

## Contract Freeze

- Implement a local, deterministic project direction snapshot builder that infers purpose, audience, product signals, technical signals, constraints, and direction opportunities from repository evidence.
- Integrate direction opportunities as first-class external candidate source entries alongside test/refactor/feature hygiene candidates.
- Extend target project planning contracts and generated Codex prompts with project direction context.
- Keep opportunities bounded to one small first step with suggested checks and evidence paths.
- Update docs, campaign state, tests, and run evidence to reflect the goal shift from hygiene-only work to project evolution.
- Preserve previous uncommitted GPT-5.5 prompt and skill-routing changes.

## Reviewer

- reviewer: `not_selected`
- reviewer_target: `none`
- reviewer_focus: `focused tests plus full suite cover direction extraction, candidate integration, and target prompt context`
- reviewer_result: `not run`

## Last Update

- timestamp: `2026-04-30T11:53:13+09:00`
- phase: `verified`
- status: `project direction intelligence implemented and verified.`
- verification_result:
  - `python -m compileall -q scripts tests`: `passed`
  - `python -m unittest discover -s tests -p test_build_project_direction.py`: `passed; ran 3 tests`
  - `python -m unittest discover -s tests -p test_external_candidate_snapshot.py`: `passed; ran 6 tests`
  - `python -m unittest discover -s tests -p test_plan_external_project.py`: `passed; ran 5 tests`
  - `python -m unittest discover -s tests -p test_planner_text_utils.py`: `passed; ran 3 tests`
  - `python -m unittest discover -s tests`: `passed; ran 150 tests`
  - `python scripts/check_doc_drift.py --root . --format json`: `passed; status=pass`
  - `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: `passed; status=pass, violation_count=0`
  - `git diff --check`: `passed; exit 0 with LF-to-CRLF working-copy warnings for touched Python files`

## Retrospective

- task: `add project direction intelligence to target candidate planning`
- score_total: `7`
- evaluation_fit: `full checks fit because the change moved candidate policy, prompt context, docs, and snapshot outputs`
- orchestration_fit: `autopilot-single fit because the policy path was tightly coupled and subagent spawning was not authorized`
- predicted_topology: `autopilot-single`
- actual_topology: `autopilot-single`
- spawn_count: `0`
- rework_or_reclassification: `none after contract freeze`
- reviewer_findings: `not run; focused and full tests covered direction extraction and integration`
- verification_outcome: `passed`
- next_gate_adjustment: `future target runs should treat project_direction candidates as first-class product evolution work, not just hygiene`
