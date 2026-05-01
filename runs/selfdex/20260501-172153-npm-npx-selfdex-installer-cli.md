# npm npx Selfdex Installer CLI

- status: `completed`
- project_key: `selfdex`
- summary: `Added npm package metadata and a selfdex CLI so the intended post-publish command can be npx selfdex install.`

## Scope

- Add `package.json` with package name `selfdex`.
- Add `bin/selfdex.js` as the npm executable.
- Support `selfdex install` and dry-run verification.
- Do not publish to npm or require npm credentials in this task.

## Evidence

- `package.json` declares package name `selfdex` and bin `selfdex`.
- `bin/selfdex.js` supports `install`, `--dry-run`, `--install-root`, `--repo-url`, `--branch`, `--skip-plugin-install`, `--python`, `--help`, and `--version`.
- `node bin/selfdex.js --help`: pass.
- `node bin/selfdex.js install --dry-run --install-root C:/tmp/selfdex-npx-dry-run`: pass.
- `python -m unittest tests.test_npm_cli`: pass.
- `npm pack --dry-run --json`: pass; package includes `package.json`, `bin/selfdex.js`, `install.ps1`, and `README.md`.
- `npm view selfdex name version --json`: registry returned E404 after approved network escalation; package name appears unclaimed or inaccessible at verification time.
- `PowerShell parser check for install.ps1`: pass.
- `python -m unittest tests.test_bootstrap_installer tests.test_install_selfdex_plugin tests.test_doc_drift`: pass after sandbox escalation for temp fixture cleanup.
- `python scripts/install_selfdex_plugin.py --root . --home ./.tmp-tests/plugin-home-dry-run --dry-run --format json`: pass.
- `python scripts/check_selfdex_plugin.py --root . --format json`: pass.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: pass.
- `python scripts/check_doc_drift.py --root . --format json`: pass.
- `python -m compileall -q scripts tests`: pass after sandbox escalation.
- `python -m unittest discover -s tests`: pass, 200 tests after sandbox escalation.
- `python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format json`: pass.
- `python scripts/plan_next_task.py --root . --format json`: pass.
- `git diff --check`: pass with line-ending warnings only.

## Boundaries

- No `npm publish` was run.
- No npm credential or token was read.
- No real home install was run.
- No target-project write or target-project Codex execution was run.
- The public `npx selfdex install` command still requires an explicit npm publish step.
