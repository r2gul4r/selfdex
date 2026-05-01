# Read-Only Control Surface

- status: `completed`
- project_key: `selfdex`
- topology: `autopilot-serial`
- agent_budget_used: `1`
- reviewer_model: `gpt-5.5`
- reviewer_mode: `pro_extended_xhigh`

## Goal

Create the first read-only control surface payload for future ChatGPT Apps/MCP
integration without exposing target-project execution.

## Result

- Added `scripts/build_control_surface_snapshot.py`.
- Added focused tests in `tests/test_control_surface_snapshot.py`.
- Documented the command in `README.md`.
- Kept `mutating_tools_exposed=false` and did not expose branch creation,
  target-project writes, or `run_target_codex.py --execute`.

## Repair

GPT-5.5 Pro extended review blocked the first pass because `recent_runs`
included non-timestamped report files such as `summary.md` and because this run
artifact did not exist yet.

The repair now limits recent runs to `YYYYMMDD-HHMMSS-*.md` artifacts and adds
this run record.

## Verification

- `python -m unittest tests.test_control_surface_snapshot`: passed after
  sandbox escalation; ran 3 tests.
- `python scripts/build_control_surface_snapshot.py --root . --format json`:
  passed; `surface_kind=read_only`, `mutating_tools_exposed=false`,
  `errors=[]`.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`:
  passed; `violation_count=0`, `mirror_warning_count=0`.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests`: passed after sandbox escalation; ran
  176 tests.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings only.

## Review

Second GPT-5.5 Pro extended review accepted the timestamped run filtering repair
and found no remaining P0/P1/P2 issues.

## Next Candidate

After acceptance, the next slice can wrap this read-only payload as an MCP tool
surface for ChatGPT Apps, still without exposing write-capable execution.
