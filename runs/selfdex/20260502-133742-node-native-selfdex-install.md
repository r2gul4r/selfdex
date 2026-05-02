# Node-Native Selfdex Install

- time: `2026-05-02T13:37:42+09:00`
- task: `node-native-selfdex-install`
- status: `local_verified`
- runtime_basis: `official_codex_native_subagents`
- agents: `main`

## Summary

Default `selfdex install` now uses a Node-native public path. It clones or
updates the selected Selfdex checkout, installs the repo-local Codex plugin into
the selected plugin home, installs the global `selfdex` skill, updates the local
marketplace entry, writes `selfdex-root.json`, and runs the Node-native setup
doctor unless skipped.

The npm CLI no longer needs Python for the default install or doctor path.
PowerShell `install.ps1` and Python installer/checker scripts remain available
as legacy or advanced fallback tools.

## Changed Files

- `bin/selfdex.js`
- `tests/test_npm_cli.py`
- `README.md`
- `README.en.md`
- `plugins/selfdex/skills/selfdex/SKILL.md`
- `STATE.md`
- `STATE.json`
- `CAMPAIGN_STATE.md`
- `CAMPAIGN_STATE.json`

## Verification

- `python -m unittest tests.test_npm_cli`: pass, 9 tests
- `node bin/selfdex.js install --dry-run --install-root C:\tmp\selfdex-npx-dry-run`: pass
- `node bin/selfdex.js install --use-existing-checkout --install-root . --plugin-home .tmp-tests\manual-node-install --skip-doctor`: pass, copied 6 files
- `node bin/selfdex.js doctor --install-root C:\Users\Administrator\selfdex --format json`: pass, runtime `node-native`
- `python scripts/check_doc_drift.py --root . --format json`: pass
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: pass
- `git diff --check`: pass with CRLF warnings only
- `npm pack --dry-run --json`: pass, `selfdex@0.1.2`, 5 files

## Review

Local review found no blocking issue. The default npm install path no longer
invokes Python, dry-run performs no writes, actual install writes only the
selected plugin home, and install failures are reported through concise
`selfdex:` errors instead of raw Node stack traces.

## Next Candidate

Port the read-only project planning surface away from Python, or keep it as an
advanced script while documenting that the public setup path is already
Python-free.
