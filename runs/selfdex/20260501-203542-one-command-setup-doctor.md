# Run 20260501-203542-one-command-setup-doctor

- project_key: selfdex
- goal: Make npx selfdex install complete the default Selfdex setup check.
- selected_candidate: Add setup doctor to installer and CLI.
- topology: single-session
- agent_budget: 0
- repair_attempts: 0
- result: local_verified
- next_candidate: Publish to npm after 2FA/OTP is ready.

## Write Sets

- README.md, install.ps1, bin/selfdex.js
- scripts/check_selfdex_setup.py, tests/test_selfdex_setup.py
- tests/test_npm_cli.py, tests/test_bootstrap_installer.py
- STATE.md, STATE.json, CAMPAIGN_STATE.md, CAMPAIGN_STATE.json, ERROR_LOG.md

## Verification

- python -m unittest discover -s tests -p test_selfdex_setup.py: pass
- python -m unittest discover -s tests -p test_npm_cli.py: pass
- python -m unittest discover -s tests -p test_bootstrap_installer.py: pass
- python -m unittest discover -s tests: pass, 211 tests after sandbox escalation
- python -m compileall -q scripts tests: pass
- node bin/selfdex.js --help: pass
- node bin/selfdex.js install --dry-run: pass
- node bin/selfdex.js doctor --help: pass
- python scripts/check_doc_drift.py --root . --format json: pass
- python scripts/check_campaign_budget.py --root . --include-git-diff --format json: pass
- git diff --check: pass with line-ending warnings only
- npm.cmd pack --dry-run --json: pass after sandbox escalation
- npm.cmd publish --access public --dry-run: pass after sandbox escalation
