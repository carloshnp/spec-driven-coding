---
name: spec-driven-coding
description: Use for multi-file coding needing a spec, plan, or proof.
license: MIT
compatibility: Any agent harness; subagents optional.
metadata:
  version: 0.1.0
  build: "Draft build 0.1.0. Gates, references, templates and five stdlib validation scripts."
---

# Spec-driven coding

## Purpose

Make a coding run predictable. The same gates, the same artifacts, and the same order every time, so a person can review the work at fixed points and a second agent can resume it from files alone. Each gate ends in a written artifact and an exit check. Nothing moves on until the check passes.

## When to use, and when not

- One-line fix, rename of one function, a single regex, a typo: skip the gates. Use only the increment loop in references/06-increments.md.
- Multi-file feature, a change that spans sessions, a task that needs a spec, a plan, or proof it works: use the gates below.
- Unsure which class a request falls in: load references/01-scope.md and size it before writing anything.
- Not a fit: spreadsheets, one-off data pulls with no tests, writing about specs, reviewing a single file.

## Operating rules

1. Surface assumptions. Before acting on a guess, write it down as an assumption and show it to the user.
2. Manage confusion. When the request is ambiguous, ask in rounds of at most 3 questions, each with a recommended answer. Do not pick silently.
3. Push back on conflicts. If two requirements clash, or a request breaks an earlier decision, say so and ask which wins.
4. Simplicity first. Build the smallest thing that meets the criteria. No speculative options, no extra layers.
5. Scope discipline. Touch only what the current task needs. Note unrelated problems in the report; do not fix them in passing.
6. Verify, do not assume. A completion claim needs the command output and the path of the artifact that holds it. A summary alone is not evidence.

The agent does not commit or push unless the user asks.

## Gates and exit criteria

| Gate | Work | Exit check |
|---|---|---|
| 0 Scope | Size the request, pick the gates that apply (references/01-scope.md) | Class named; fits-one-window decision recorded |
| 1 Specify | Frontier rounds, criteria, validation methods (references/02-specify.md, references/03-criteria-and-validation.md) | Frontier empty; every criterion has a False if clause and a method; spec frozen; approval line in STATE.md quoting the user, from a later turn |
| 2 Plan and tasks | Slices and task files (references/05-plan-and-tasks.md) | Task files and plan.md written as unapproved drafts; scripts/validate_tasks.py exits 0 on the drafts; frozen only after the user approves the quiz in a later turn; approval line in STATE.md |
| 3 Increments | Waves of at most 3 tasks (references/06-increments.md, references/10-subagents.md) | Each task has status and evidence; runnable after every task |
| 4 Verify | Proofs, completion gate, verifier (references/11-verification.md) | scripts/validate_verification.py exits 0 on VERIFY.md |
| 5 Compile (optional) | PROMPT.md, lint, coverage (references/04-prompt-contract.md, references/08-interfaces.md) | scripts/lint_prompt.py and scripts/check_interface_coverage.py exit 0 |

The review panel (references/12-review-panel.md) runs at gates 1 and 2 when the artifact is large.

Approval is a later user turn. The agent records it in STATE.md under Approvals as `Approved by user on ISO-DATE: "the user's own words"`. The agent never writes an approval line on its own. STATE.md sits at the project root, next to specs/ and tasks/. STATE.md sections are Position, Approvals, Commands, Decisions, Open items.

## Load table

Load the files the current gate names; skip the rest. Each line below gives its condition.

- Read references/01-scope.md when a request arrives and you must decide how much process it needs.
- Read references/01-scope.md, references/02-specify.md, references/03-criteria-and-validation.md and references/08-interfaces.md when you start gate 1, Specify.
- Read references/02-specify.md when a new spec starts, the request is ambiguous, or terms need defining.
- Read references/03-criteria-and-validation.md when you write or check acceptance criteria and how each is validated.
- Read references/04-prompt-contract.md when the user wants a PROMPT.md or a benchmark-style brief.
- Read references/05-plan-and-tasks.md when a frozen spec must become slices and task files.
- Read references/06-increments.md when you implement a task, or make a wide change across many files.
- Read references/07-testing.md when you write tests, change tests, or judge test quality.
- Read references/08-interfaces.md when you define or change a public surface, or write Expected Interface entries.
- Read references/09-context-and-resume.md when a session is long, is about to compact, or resumes earlier work.
- Read references/10-subagents.md when you consider delegating, or have to run roles without delegation.
- Read references/11-verification.md when work is done and you must prove it at gate 4.
- Read references/12-review-panel.md when a spec or plan is large and needs independent review.
- Read references/13-stack-and-env.md when you need the build, test, or run commands, or a stack choice.
- Read references/14-pitfalls.md when something feels off, or before closing any gate.
- Read references/15-benchmark-task-authoring.md only when the task is graded in Docker.
- Read references/16-sources.md when the user asks where the ideas came from.
- Read references/17-web-ui-builds.md when the deliverable is a browser UI, an SPA, or a clone of an existing product's interface.
- Use templates/spec.md when you start the spec file.
- Use templates/glossary.md when a term is resolved and the user approves a glossary file.
- Use templates/decision-record.md when a decision passes all three tests and the user approves the file.
- Use templates/task.md when you write a task file.
- Use templates/state.md when you open STATE.md (Position, Approvals, Commands, Decisions, Open items) for a multi-session run.
- Use templates/proofs.md when you write only the proofs table.
- Use templates/verification.md when you start VERIFY.md at gate 4.
- Use templates/review-report.md when you record a review panel result.
- Use templates/prompt.md when you compile a PROMPT.md.
- Use templates/interface-entry.md when you add one public name to an Expected Interface.
- Use templates/rubric.md when a PROMPT.md carries a rubric.

## Subagent mode

1. Detect whether the harness can delegate work to other agents. If it cannot, say so once and use the fallback.
2. If it can, read references/10-subagents.md before the first fan-out. Waves hold at most 3 workers. Judge a worker by the files on disk, not by its summary.
3. Fallback: run the same roles one after another, each in a fresh session that reads only the files it needs. Label every result produced this way DEGRADED, in the report and in the verdict line.
4. Workers do not spawn workers.

## Interface rule

- The Expected Interface section lists public names only, each with the behavior it must have. Private items are the agent's free design and are never listed.
- Expected Interface is the specification. Tests target public names. Private code may be tested directly, but a test that imports a name outside Expected Interface gets a WARN from the coverage script, not an error.
- Details: references/08-interfaces.md and references/04-prompt-contract.md.

## Windows note

Where `python3` is not available, run the scripts with `python` or `py -3`. Shell steps assume Git Bash. Keep LF line endings in repository files.

## Gotchas

Each line has its check. Full table in references/14-pitfalls.md.

1. A spec that grows past what one session can hold. Check: count criteria bullets; split above the limit in references/01-scope.md.
2. Questions asked before earlier answers exist. Check: each round holds only questions with no open dependency.
3. Criteria that cannot fail. Check: every criterion has a False if clause and fails at the base commit.
4. Approval written by the agent. Check: the Approvals line in STATE.md quotes the user and carries an ISO date from a later turn.
5. Tests that import names outside the public list. Check: run scripts/check_interface_coverage.py and read each WARN.
6. Tasks sliced by layer. Check: each task has a Demo question a person answers by watching.
7. Done claimed without evidence. Check: VERIFY.md has quoted output and passes scripts/validate_verification.py.
8. A test edited to make it pass. Check: the diff shows no changed assertion without a finding.
9. A layout criterion proven by a jsdom assertion. Check: jsdom computes no layout, so geometry, side-by-side panes, and theme contrast need a screenshot with the AC it proves named (references/17-web-ui-builds.md).
10. A requirement that enumerates N items and a criterion that checks M < N. Check: count members in the requirement, count them in the criterion, compare before freezing (references/03-criteria-and-validation.md).
11. A revision written to clear findings introduces new contradictions. Check: before re-panelling, list every requirement that names a state, view, count, key or verb, and confirm no two requirements and no criterion disagree about it (references/14-pitfalls.md).
12. An action described as both a toggle and idempotent. Check: read each action's verb; a toggle restores on a repeat, only set-style actions are idempotent.
