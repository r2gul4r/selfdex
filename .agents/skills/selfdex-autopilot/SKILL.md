---
name: selfdex-autopilot
description: Use when working in the Selfdex repository or from a Selfdex-generated Codex task contract to classify, freeze, implement, verify, and record bounded improvement work; do not use for unrelated general coding tasks outside Selfdex.
---

# Selfdex Autopilot

## Core Contract

- Read `AGENTS.md`, `STATE.md`, and `CAMPAIGN_STATE.md` before non-trivial writes.
- Keep the loop bounded: classify, freeze, implement, verify, repair inside the frozen scope, record.
- Cross-project analysis starts read-only. Cross-project writes need explicit user approval and an isolated target-project write boundary.
- Never weaken hard approval gates for destructive operations, secrets, paid APIs, deploys, database writes, production writes, global config, or installers.

## Execution Flow

1. Restate the current task and compare it with `STATE.md`.
2. Record score, hard triggers, selected rules, selected skills, topology, budget, write sets, and verification target before implementation files change.
3. Freeze expected outcome, success criteria, non-goals, stop conditions, allowed side effects, and final evidence shape.
4. Use repo tools first. Prefer existing scripts and tests over ad hoc checks.
5. Verify with the focused command first, then the broader repository checks that match the frozen contract.
6. Record run evidence under `runs/` for non-trivial work and update `CAMPAIGN_STATE.md` when the campaign queue or latest run changes.

## Skill Routing

- Load another skill only when the user names it or its description directly matches the task.
- Keep selected skills in `STATE.md` so later sessions can audit why they were used.
- For OpenAI model, prompt, or API migration work, use `openai-docs` first and prefer official OpenAI docs.
- Do not install skills, plugins, or MCP servers, and do not edit global Codex config, unless the user explicitly approves that setup work.

## Prompt Shape

- Put stable operating rules first and dynamic task details last.
- State the expected outcome before step-by-step process.
- Include context budget, tool/skill preamble rules, write boundaries, stop conditions, verification commands, and final report fields.
- Keep status updates short and outcome-based; do not narrate routine tool calls.
