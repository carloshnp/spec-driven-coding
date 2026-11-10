# Increments

Read this when gate 3 starts and you are about to implement tasks, including a one-line fix, which uses only this loop.

## Contents

- The cycle
- Rules 0 to 5
- Coding principles
- Waves
- Wide changes (unverified)
- Integration-branch fallback

## The cycle

Work one task at a time from the frontier (references/05-plan-and-tasks.md).

1. Take a frontier task. Set its Status to running in the task file and in plan.md.
2. Write the checks for its criteria first. Each check must fail before the work, for the reason the criterion names. A check that passes on untouched code proves nothing.
3. Implement the smallest change that makes the checks pass.
4. Run the checks, then the repository test command (references/13-stack-and-env.md).
5. Verify: read each criterion's "False if" observation and look for it in the output.
6. Record: set Status to done, and keep the evidence the task asks for (command and quoted output). Derive the touched paths from git and keep them for VERIFY.md.
7. Take the next frontier task. If none is left, go to gate 4.

If a check fails and the fix is not clear after one honest attempt, stop guessing. Set Status to blocked, write the observation, and ask. Do not loosen the criterion to match the result.

A one-line fix uses steps 2 to 6 only, with no task file.

## Rules 0 to 5

0. Simplicity first. Write the plainest code that meets the criteria. No abstraction for a second use that does not exist yet.
1. Scope discipline. Touch only what the task needs. Note other problems in the report instead of fixing them.
2. One thing at a time. A task is one behavior. Do not start the next while this one is red.
3. Keep it runnable. After every step the project builds and the earlier checks still pass. Break nothing "for now".
4. Safe defaults. New behavior is off, inert, or conservative until the task turns it on. Errors fail loudly with a clear message, not silently.
5. Rollback friendly. Each task's change can be removed alone. Prefer additions over edits, and keep data changes reversible.

## Coding principles

- State assumptions before coding. If one matters, say it in the report. If it changes the outcome, ask.
- Make surgical changes. Match the existing style. Do not tidy neighboring code, reformat files, or rename things that are not part of the task. Remove only what your own change made unused. Mention other dead code and leave it.
- After each change, do a senior check: would a careful reviewer ask why this line exists? Cut anything that traces to no criterion.
- Never edit a test to make it pass (references/07-testing.md).
- Private design is yours: helpers, classes, modules, and layout need no approval. Only public names are fixed by the spec (references/08-interfaces.md).

## Waves

Run at most 3 tasks at once, all from the frontier, none sharing a public name. With subagents, read references/10-subagents.md first. Without them, run the same tasks one by one. After each wave, run the full test command on the integrated result before starting the next wave.

## Wide changes (unverified)

Status: unverified. The sources describe this pattern in prose and report no run showing it works. Treat it as a starting plan and watch the first batch closely.

A wide change is one mechanical edit whose reach covers much of the codebase, such as renaming a shared symbol or retyping a field. No single slice can land and stay green. Split it into three kinds of task:

1. Expand: add the new form beside the old. Both work. All earlier checks still pass.
2. Migrate: move callers to the new form in batches. Size each batch by blast radius (per package or per directory) so that it fits one context window. Each migrate task is blocked by the expand task, and the migrate tasks can run in the same wave if they touch different callers.
3. Contract: remove the old form once no caller remains. This task is blocked by every migrate task. Its criterion searches for remaining uses and expects none.

Open points the sources leave unanswered: how to measure blast radius, how many batches to cut, and how to keep the expand step small. Decide these in the plan, ask the user at the quiz gate, and record what you learn in STATE.md under Decisions.

## Integration-branch fallback

Use this only when migrate batches cannot stay green alone. All batches share one integration branch, and a final integrate-and-verify task is blocked by all of them. Green is promised only at that task. Rules:

- Run the batches serially, not in parallel.
- Give each concurrent writer a separate working copy. Never share one checkout.
- One writer per path at any time.
- The agent never runs git commit unless the user asks.
