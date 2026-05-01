# Read-Only MCP Tool Wrapper

- status: `completed`
- project_key: `selfdex`
- summary: `Read-only MCP tool wrapper implemented, verified, accepted by GPT-5.5 Pro extended review, and loop stopped per user request.`

## Scope

- Add a local `/mcp` JSON-RPC scaffold with one read-only tool.
- Keep target-project execution, branch creation, and writes out of the tool surface.
- Keep the implementation dependency-free and honest about being a local scaffold, not hosted ChatGPT Developer Mode validation.

## Evidence

- `python -m unittest tests.test_control_surface_mcp_server`: passed after approved Temp sandbox escalation, 5 tests.
- `python scripts/control_surface_mcp_server.py --root . --describe-tools`: passed.
- `python scripts/build_control_surface_snapshot.py --root . --format json`: passed with `mutating_tools_exposed=false` and `errors=[]`.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: passed with `violation_count=0` and `mirror_warning_count=0`.
- `python scripts/check_doc_drift.py --root . --format json`: passed.
- `python -m compileall -q scripts tests`: passed.
- `python -m unittest discover -s tests`: passed after approved Temp sandbox escalation, 181 tests.
- `git diff --check`: passed with LF-to-CRLF warnings only.
- `GPT-5.5 Pro extended reviewer`: accepted; no P0/P1/P2 findings.

## Residual Gaps

- Malformed `Content-Length` and batch JSON-RPC payload tests are not included.
- Real MCP client or ChatGPT Apps runtime E2E compatibility is deferred.

## Loop Status

- Stopped after this current work per user request.
