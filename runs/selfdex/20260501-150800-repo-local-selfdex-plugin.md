# Repo-Local Selfdex Plugin

- status: `completed`
- project_key: `selfdex`
- summary: `Packaging Selfdex as a repo-local Codex plugin for future @selfdex invocation from target project sessions without global install yet.`

## Scope

- Add a repo-local `selfdex` plugin manifest.
- Add a `selfdex` plugin skill that routes from the current project session to Selfdex read-only planning.
- Add a marketplace entry for repo-local discovery.
- Add deterministic plugin validation and focused tests.
- Do not install the plugin globally or edit Codex home.

## Evidence

- `scripts/check_selfdex_plugin.py --root . --format json`: pass, `finding_count=0`.
- `tests.test_selfdex_plugin`: pass, 3 tests OK after approved sandbox escalation for temporary fixture writes.
- `scripts/check_campaign_budget.py --root . --include-git-diff --format json`: pass, `violation_count=0`, `mirror_warning_count=0`.
- `scripts/check_doc_drift.py --root . --format json`: pass, `finding_count=0`.
- `git diff --check`: pass; Git reported CRLF normalization warnings for existing LF-touched files.
- `python -m unittest discover -s tests`: pass, 188 tests OK after approved sandbox escalation for temporary fixture writes.
- `skill-creator/scripts/quick_validate.py`: deferred because bundled Python lacks PyYAML; repo-local validator covered manifest, skill frontmatter, marketplace wiring, and safety phrases.

## Result

- Added `plugins/selfdex/.codex-plugin/plugin.json`.
- Added `plugins/selfdex/skills/selfdex/SKILL.md` for future `@selfdex` invocation from a target project session.
- Added `.agents/plugins/marketplace.json` as a repo-local marketplace entry.
- Added `scripts/check_selfdex_plugin.py` and focused tests.
- Updated README, autopilot policy, and final-goal docs to state that global install/enabling is a separate approval step.
- No global Codex config, Codex home, or external target project was modified.
