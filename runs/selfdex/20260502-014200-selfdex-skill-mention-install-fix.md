# Selfdex Run: selfdex-skill-mention-install-fix

- status: local_verified
- project_key: selfdex
- task: Make `@selfdex` appear through the Codex skill mention surface instead of falling back to file search results.
- reason: The Codex UI showed repo skills and file matches for `@self`, but no usable `Selfdex` command-center entry. Local plugin files existed, but the global `skills/selfdex` entry was missing.

## Changes

- `scripts/install_selfdex_plugin.py` now installs both:
  - plugin package: `<CODEX_HOME>/plugins/selfdex`
  - global skill: `<CODEX_HOME>/skills/selfdex`
- `scripts/check_selfdex_setup.py` now fails if the global `skills/selfdex/SKILL.md` entry is missing.
- README Korean/English docs now explain that Codex may expose Selfdex as a skill in the `@` mention menu.
- `package.json` is prepared as `0.1.2` because `0.1.1` is already published.

## Local Repair

- Installed the global skill to `C:\Users\Administrator\.codex\skills\selfdex`.
- Doctor now reports `selfdex-global-skill: pass`.
- The already-open Codex session still does not show it via `tool_search selfdex`; refresh or restart plugin/skill discovery before checking the UI.

## Verification

- `python -m unittest tests.test_install_selfdex_plugin tests.test_selfdex_setup`: pass, 15 tests after sandbox-escalated rerun for Windows temp fixture writes.
- `node bin/selfdex.js install --dry-run`: pass.
- `node bin/selfdex.js doctor --install-root . --format markdown`: pass.
- `python scripts/check_doc_drift.py --root . --format json`: pass.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: pass.
- `npm.cmd pack --dry-run --json`: pass for `selfdex@0.1.2`.
- `git diff --check`: pass with CRLF warnings only.

## Next

- Restart or refresh Codex discovery and check that `@selfdex` appears under Skills.
- If this fix should ship to other machines, commit/push, wait for CI, then publish `selfdex@0.1.2`.
