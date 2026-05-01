# Run 20260501-204846-readme-bilingual-default-korean

- project_key: selfdex
- goal: Make the public README Korean-first with English navigation.
- selected_candidate: Split README into Korean default and English mirror.
- topology: single-session
- agent_budget: 0
- repair_attempts: 0
- result: local_verified
- next_candidate: Publish to npm after 2FA/OTP is ready.

## Write Sets

- README.md, README.en.md, package.json
- STATE.md, STATE.json, CAMPAIGN_STATE.md, CAMPAIGN_STATE.json
- runs/selfdex/, ERROR_LOG.md

## Verification

- python scripts/check_doc_drift.py --root . --format json: pass
- python scripts/check_campaign_budget.py --root . --include-git-diff --format json: pass
- git diff --check: pass with line-ending warnings only
- rg language/install/doctor links in README.md README.en.md: pass
- node bin/selfdex.js --help: pass
- npm.cmd --cache C:/tmp/npm-cache-selfdex pack --dry-run --json: pass after sandbox escalation, README.en.md included
