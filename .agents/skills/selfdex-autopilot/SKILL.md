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
- Treat GPT-5.5 prompt guidance as the operating discipline: clear roles, tool boundaries, success criteria, stop conditions, verification, and compact evidence before higher effort.
- Treat official Codex native Subagents/MultiAgentV2 as the Selfdex agent runtime after `@selfdex` or equivalent user permission.
- Do not treat `codex_multiagent` as the active baseline. Historical records may be reference evidence only.

## Codex Native Agents

- Use the main agent for requirements, task selection, approval boundaries, integration, final reporting, and run records.
- Use `explorer` for read-only codebase scouting and write-boundary recommendations.
- Use `docs_researcher` for read-only official docs or API behavior checks.
- Use `worker` for bounded implementation inside one frozen write boundary.
- Use `reviewer` for read-only correctness, regression, security, and missing-test review.
- Read-only subagents may run after `@selfdex` when they reduce noise or shorten independent discovery/review work.
- Write-capable worker subagents require a frozen contract and disjoint write boundary.
- Do not call GPT Pro extended mode automatically. Product direction review requires the user to ask for it or explicitly approve it.
- If `@chatgpt-apps` is available, treat it as the GPT Pro product/app direction-review surface for project purpose, improvement ideas, and additional feature opportunities.
- Keep routine code diff review on the Codex native `reviewer` subagent.

## Execution Flow

1. Restate the current task and compare it with `STATE.md`.
2. Record selected rules, selected skills, selected official agent roles, write sets, and verification target before implementation files change.
3. Freeze expected outcome, success criteria, non-goals, stop conditions, allowed side effects, and final evidence shape.
4. Prefer official Codex subagents for separable read-heavy discovery, review, docs checks, logs, tests, and disjoint worker slices; keep tightly coupled integration in the main agent.
5. Use repo tools first. Prefer existing scripts and tests over ad hoc checks.
6. Verify with the focused command first, then the broader repository checks that match the frozen contract.
7. Record run evidence under `runs/` for non-trivial work and update `CAMPAIGN_STATE.md` when the campaign queue or latest run changes.

## Skill Routing

- Load another skill only when the user names it or its description directly matches the task.
- Keep selected skills in `STATE.md` so later sessions can audit why they were used.
- For OpenAI model, prompt, or API migration work, use `openai-docs` first and prefer official OpenAI docs.
- Do not install skills, plugins, or MCP servers, and do not edit global Codex config, unless the user explicitly approves that setup work.
- Use Subagents only through the official Codex native runtime; do not route through legacy multi-agent kit assumptions or local topology labels.

## Prompt Shape

- Put stable operating rules first and dynamic task details last.
- State the expected outcome before step-by-step process.
- Include context budget, tool/skill preamble rules, write boundaries, stop conditions, verification commands, and final report fields.
- Keep status updates short and outcome-based; do not narrate routine tool calls.
