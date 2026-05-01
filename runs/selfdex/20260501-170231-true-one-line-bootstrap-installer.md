# True One-Line Bootstrap Installer

- status: `completed`
- project_key: `selfdex`
- summary: `Adding a true one-line bootstrap command that clones or updates Selfdex and installs the @selfdex plugin.`

## Scope

- Add a root `install.ps1` bootstrap script.
- Document a one-line PowerShell install command.
- Bootstrap must clone or update Selfdex, then install the home-local plugin.
- Verification must use dry-run/static checks and avoid real-home installs or network clones.

## Evidence

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun -InstallRoot C:\tmp\selfdex-bootstrap-dry-run`: pass; no clone or plugin install ran.
- PowerShell parser check for `install.ps1`: pass after correcting manual command quoting.
- `python -m unittest tests.test_bootstrap_installer`: pass, 3 tests OK.
- `python -m unittest tests.test_bootstrap_installer tests.test_install_selfdex_plugin tests.test_selfdex_plugin`: pass, 10 tests OK after approved sandbox escalation.
- `scripts/install_selfdex_plugin.py --root . --home C:\tmp\selfdex-install-preview --dry-run --format json`: pass.
- `scripts/check_selfdex_plugin.py --root . --format json`: pass, `finding_count=0`.
- `scripts/check_campaign_budget.py --root . --include-git-diff --format json`: pass, `violation_count=0`, `mirror_warning_count=0`.
- `scripts/check_doc_drift.py --root . --format json`: pass, `finding_count=0`.
- `python -m compileall -q scripts tests`: pass with `PYTHONPYCACHEPREFIX` redirected to `C:\tmp`.
- `python -m unittest discover -s tests`: pass, 195 tests OK after approved sandbox escalation.
- `git diff --check`: pass; Git reported CRLF normalization warnings for existing LF-touched files.

## Result

- Added root `install.ps1` as the true bootstrap entrypoint.
- The documented one-liner downloads/runs `install.ps1`.
- The bootstrap clones Selfdex when missing, updates it when present, then runs `scripts/install_selfdex_plugin.py --yes --force`.
- Added `tests/test_bootstrap_installer.py`.
- Updated README, autopilot policy, and final-goal docs to distinguish true one-line bootstrap from clone-first plugin install.
- Did not run a network clone or install into the real user home during verification.
