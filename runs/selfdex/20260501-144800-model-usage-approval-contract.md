# Model Usage And Approval Contract

- status: `completed`
- project_key: `selfdex`
- summary: `Model usage and approval contract implemented, verified, accepted by Codex gpt-5.5 xhigh review, and loop closed.`

## Scope

- Encode GPT / Selfdex / Codex role boundaries.
- Make GPT direction review user-approved and strategic-only.
- Preserve Codex `gpt-5.5` xhigh review for non-trivial implementation review.
- Add approval status to the read-only control surface.
- Keep target-project writes, branch creation, and target Codex execution out of Apps/MCP surfaces.

## Evidence

- `python -m unittest tests.test_campaign_budget tests.test_doc_drift tests.test_control_surface_snapshot tests.test_control_surface_mcp_server`: passed after approved Temp sandbox escalation, 27 tests.
- `python scripts/control_surface_mcp_server.py --root . --describe-tools`: passed.
- `python scripts/build_control_surface_snapshot.py --root . --format json`: passed with `approval_status`, `gpt_direction_review_auto_call=false`, and `write_capable_apps_mcp_tools_exposed=false`.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed with `violation_count=0` and `mirror_warning_count=0`.
- `python scripts/check_doc_drift.py --root . --format json`: passed with `missing_core_paths=[]`.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests`: passed after approved Temp sandbox escalation, 185 tests.
- `git diff --check`: passed with LF-to-CRLF warnings only.
- `Codex gpt-5.5 xhigh review`: first pass blocked on two P2 findings; both repaired; second pass accepted with no P0/P1/P2 findings.

## Repairs

- Enforced `CAMPAIGN_STATE.json` and `STATE.json` as required source-of-truth files in the campaign budget check.
- Added doc drift detection for missing core paths, including JSON state contracts.
- Added direct regression coverage for `first_app_surface` markdown mirror drift.

## Residual Gaps

- `build_control_surface_snapshot.py` still defaults missing JSON payloads to empty values, but budget and doc drift checks now block missing required JSON contracts.
- One-missing-JSON cases could be split into separate tests later; current coverage proves missing required JSON core paths fail.
