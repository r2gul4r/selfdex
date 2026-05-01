# Selfdex Run: codex-home-plugin-install-fix

- status: local_verified
- project_key: selfdex
- task: Fix `npx selfdex install` so the plugin installs into the Codex discovery home instead of only the OS home.
- reason: Published `0.1.0` installed `@selfdex` under `C:\Users\Administrator\plugins` and `C:\Users\Administrator\.agents`, but the active Codex app discovery home is `C:\Users\Administrator\.codex`.

## Changes

- `install.ps1` now resolves plugin home from `-PluginHome`, `CODEX_HOME`, or `$HOME/.codex`.
- `bin/selfdex.js` exposes `--plugin-home` for installer override.
- `scripts/install_selfdex_plugin.py` defaults to `CODEX_HOME` or `$HOME/.codex`.
- `scripts/check_selfdex_setup.py` checks the same Codex plugin home by default.
- README Korean/English install docs now describe Codex discovery home.
- `package.json` version was bumped to `0.1.1` for the npm repair release.

## Local Repair

- Installed `@selfdex` to `C:\Users\Administrator\.codex\plugins\selfdex`.
- Wrote marketplace entry to `C:\Users\Administrator\.codex\.agents\plugins\marketplace.json`.
- `tool_search selfdex` still returns no result in the already-open session, which is expected for stale session metadata. Restart or refresh Codex plugin discovery before checking UI.

## Verification

- `python -m unittest tests.test_install_selfdex_plugin tests.test_selfdex_setup`: pass, 13 tests.
- `node bin/selfdex.js install --dry-run`: pass; reports plugin home `C:\Users\Administrator\.codex`.
- `python scripts/check_selfdex_setup.py --root . --home C:\Users\Administrator\.codex --codex-home C:\Users\Administrator\.codex --format json`: pass.
- `npm.cmd pack --dry-run --json`: pass.
- `npm.cmd publish --access public --dry-run`: pass for `selfdex@0.1.1`.
- `git diff --check`: pass with CRLF warnings only.

## Next

- Restart or refresh Codex plugin discovery, then check whether `@selfdex` appears.
- To fix future `npx selfdex install` users, commit this patch, bump package version to `0.1.1`, push, wait for CI, then publish `selfdex@0.1.1`.
