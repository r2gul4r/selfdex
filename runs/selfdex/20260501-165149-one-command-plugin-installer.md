# One-Command Plugin Installer

- status: `completed`
- project_key: `selfdex`
- summary: `Adding a one-command installer so a cloned Selfdex checkout can install the home-local @selfdex plugin without manual Codex setup.`

## Scope

- Add a dry-run-by-default installer command.
- Copy only the Selfdex plugin package into a selected home-local plugin path when `--yes` is passed.
- Update only the selected home-local marketplace file.
- Preserve explicit approval gates for target-project writes.
- Do not run the installer against the real user home in this task.

## Evidence

- `scripts/install_selfdex_plugin.py --root . --home C:\tmp\selfdex-install-preview --dry-run --format json`: pass; planned copy, root config, and marketplace update without writes.
- `scripts/install_selfdex_plugin.py --root . --home C:\tmp\selfdex-install-smoke-20260501-170000 --yes --format json`: pass after approved sandbox escalation against fake home; wrote plugin copy, `selfdex-root.json`, and marketplace entry under `C:\tmp`.
- Installed fake-home `selfdex-root.json`: recorded `D:\git\selfdex`.
- Installed fake-home `SKILL.md`: includes `Installed Checkout` section with the cloned checkout path.
- Installed fake-home marketplace: source path `./plugins/selfdex`, authentication `ON_INSTALL`.
- `python -m unittest tests.test_install_selfdex_plugin tests.test_selfdex_plugin`: pass, 7 tests OK after approved sandbox escalation.
- `scripts/check_selfdex_plugin.py --root . --format json`: pass, `finding_count=0`.
- `scripts/check_campaign_budget.py --root . --include-git-diff --format json`: pass, `violation_count=0`, `mirror_warning_count=0`.
- `scripts/check_doc_drift.py --root . --format json`: pass, `finding_count=0`.
- `python -m compileall -q scripts tests`: pass with `PYTHONPYCACHEPREFIX` redirected to `C:\tmp`.
- `python -m unittest discover -s tests`: pass, 192 tests OK after approved sandbox escalation.
- `git diff --check`: pass; Git reported CRLF normalization warnings for existing LF-touched files.

## Result

- Added `scripts/install_selfdex_plugin.py`.
- Added `tests/test_install_selfdex_plugin.py`.
- Updated the `selfdex` plugin skill so installed copies can use `Installed Checkout` and `selfdex-root.json`.
- Updated the plugin validator to require the installer command.
- Updated README, autopilot policy, and final-goal docs with the one-command install path.
- Did not install into the real user home or modify external target projects.
