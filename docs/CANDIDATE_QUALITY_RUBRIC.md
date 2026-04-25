# Candidate Quality Rubric

This rubric scores whether a Selfdex planner candidate is likely to be useful
work for a human-supervised Codex session.

It is a product-quality check, not a replacement for static repository signals.
Large files, duplicated code, missing tests, and recent churn can surface
candidates, but they do not prove the candidate is the best next task. A good
candidate should describe a real problem, create user value, stay locally
verifiable, remain small enough to review, and be reversible if the guess is
wrong.

The current planner does not automatically enforce this rubric. Use it for
manual review, external read-only validation, and future evaluator design.
For local JSON payloads, `scripts/evaluate_candidate_quality.py` can calculate
the documented totals and verdicts without changing planner behavior.

## Score Dimensions

Score each dimension from 0 to 3.

| Dimension | Question | 0 | 1 | 2 | 3 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `real_problem` | Is there evidence that the issue or opportunity is real? | No evidence or mostly speculative | Weak signal, unclear impact | Clear local evidence | Repeated evidence or direct user/workflow pain |
| `user_value` | Would solving it make the project more useful or easier to operate? | Cosmetic or irrelevant | Indirect maintenance value only | Clear workflow, reliability, or comprehension value | Strong value tied to campaign goal or user need |
| `local_verifiability` | Can success be checked locally without external risk? | No practical local check | Manual inspection only | Existing command or focused review can verify | Fast, repeatable command plus clear evidence artifact |
| `scope_smallness` | Is the smallest useful version reviewable and bounded? | Too broad or undefined | Needs major decomposition | One bounded file/flow or clear doc slice | Tiny, isolated, and easy to revert |
| `risk_reversibility` | Can the change be undone safely if wrong? | High-risk or hard to revert | Moderate blast radius | Low-risk and mostly local | Read-only, docs-only, or trivially reversible |

## Interpreting Scores

- Maximum score: `15`.
- Strong candidate: total `12-15`, with no dimension below `2`.
- Usable candidate: total `9-11`, with `real_problem`, `local_verifiability`,
  and `risk_reversibility` all at least `2`.
- Defer or split: total below `9`, or any dimension scored `0`.

High scores do not authorize unsafe work. Hard approval zones still apply:
destructive actions, secrets, deploys, paid calls, database or production
writes, cross-workspace writes, and any target project write outside the frozen
contract.

## External Read-Only Validation Protocol

Use this flow before claiming Selfdex is generally useful outside this repo:

1. Register 2-3 external projects in read-only mode.
2. Generate the top 5 planner candidates for each project.
3. For each candidate, record the source evidence and suggested verification.
4. Score each candidate with the five dimensions above.
5. Ask a human reviewer whether the top candidates are real, valuable, small,
   locally verifiable, and low-risk.
6. Treat agreement on those criteria as the external value proof point.

Do not write to external projects during this validation. The output should be a
scored candidate list and notes about which candidates would be worth freezing
as future task contracts.

## Candidate Review Template

```text
candidate:
source_project:
source_signal:
evidence:
suggested_verification:

scores:
  real_problem: 0
  user_value: 0
  local_verifiability: 0
  scope_smallness: 0
  risk_reversibility: 0
  total: 0

verdict: strong | usable | defer | split
human_notes:
```
