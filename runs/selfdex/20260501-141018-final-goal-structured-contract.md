# Final Goal Structured Contract

- status: `completed`
- project_key: `selfdex`
- topology: `autopilot-serial`
- agent_budget_used: `1`
- reviewer_model: `gpt-5.5`
- reviewer_mode: `pro_extended_xhigh`

## Goal

Fix Selfdex's final goal as the command center that reads a user-selected
project, chooses the next improvement, evolution, or feature task, asks for
approval, then safely delegates the approved work to Codex and records the
result.

## Selected Candidate

Accept GPT-5.5 reviewer feedback that markdown-parsed safety contracts were
the main architecture risk. Move campaign budget checking toward structured
`STATE.json` and `CAMPAIGN_STATE.json` contracts while keeping markdown files
as human-readable mirrors.

## Write Sets

- `README.md`
- `AUTOPILOT.md`
- `docs/SELFDEX_FINAL_GOAL.md`
- `CAMPAIGN_STATE.md`
- `CAMPAIGN_STATE.json`
- `STATE.md`
- `STATE.json`
- `scripts/check_campaign_budget.py`
- `scripts/check_doc_drift.py`
- `tests/test_campaign_budget.py`
- `ERROR_LOG.md`
- `runs/selfdex/20260501-141018-final-goal-structured-contract.md`

## Result

- Locked the final goal around a user-selected-project command center.
- Added `STATE.json` and `CAMPAIGN_STATE.json` as machine-readable contracts.
- Updated `check_campaign_budget.py` to prefer JSON contracts and fall back to
  markdown when JSON is absent.
- Added `mirror_warnings` so stale markdown mirrors are visible without
  blocking the canonical JSON path.
- Kept target-project execution approval-gated and did not expose write-capable
  execution through a ChatGPT Apps or MCP surface.

## Verification

- `python -m unittest tests.test_campaign_budget`: passed after sandbox
  escalation; ran 10 tests.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`:
  passed; `contract_sources=STATE.json/CAMPAIGN_STATE.json`,
  `mirror_warning_count=0`.
- `python scripts/check_doc_drift.py --root . --format json`: passed;
  `finding_count=0`.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests`: passed after sandbox escalation; ran
  173 tests.
- `git diff --check`: passed with LF-to-CRLF working-copy warnings only.

## Review

First GPT-5.5 Pro extended review returned `accept_with_minor_followup` and
requested JSON/markdown mirror drift visibility. The repair added
`mirror_warnings` and a focused regression test.

Second GPT-5.5 Pro extended review returned `accept` with no actionable P0/P1/P2
findings.

## Next Candidate

Build the read-only ChatGPT Apps/MCP control surface for:

- registered project list
- next recommended task
- latest run summary

Do not expose `run_target_codex.py --execute` or any write-capable target
execution surface in that slice.
