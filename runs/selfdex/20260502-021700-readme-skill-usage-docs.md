# Selfdex Run: selfdex-readme-skill-usage-docs

- status: local_verified
- project_key: selfdex
- task: Document Selfdex skill usage in the public README and English mirror.
- reason: The installed Codex `@` menu now shows `Selfdex` as a skill, so the README should tell users which entry to select and how it differs from helper skills and file-search results.

## Changes

- `README.md` now explains the Codex `@` menu entries:
  - `Selfdex` as the global command-center skill.
  - `Selfdex Autopilot` as the repo/task-contract helper skill.
  - `Selfdex Commit Gate` as the commit, push, and CI close-out helper.
  - file-search entries as non-command results.
- `README.en.md` mirrors the same usage guidance.
- State and campaign mirrors were updated for this documentation run.

## Verification

- `python scripts/check_doc_drift.py --root . --format json`: pass.
- `python scripts/check_campaign_budget.py --root . --include-git-diff --format json`: pass.
- `git diff --check`: pass with CRLF warnings only.
- `python scripts/check_commit_gate.py --root . --commit-message "docs: document selfdex skill usage" --format json`: pass.

## Next

- Commit with `docs: document selfdex skill usage`.
- Push `main`.
- Check GitHub Actions for the pushed commit.
