# Subagents

Read this when you are about to fan work out to subagents, when you act as a worker, or when delegation is not available and you must run the roles yourself.

## Contents
- Detect delegation
- Roles
- Tiers
- Isolation and no commits
- Waves and batching
- Handoff report
- Judging completion
- Dispatch log and DEGRADED mode
- Nesting

## Detect delegation

Before gate 3, find out whether the harness can start subagents. Try a harmless read-only dispatch, or read the tool list. Record the answer in STATE.md as a decision.

- If delegation exists, use the roles below.
- If it does not, run the same roles one after another in fresh sessions, and label every result DEGRADED (see the last sections).

## Roles

| Role | Access | Owns | Returns |
|---|---|---|---|
| Explorer | read-only | nothing | facts with file locations |
| Implementer | write | the named public names from the task's Interface field, or one separate working copy | changed code and evidence |
| Test-writer | write to tests | tests that import public names only | tests and a first run result |
| Verifier | read-only plus running checks, fresh context | nothing | the Verifier table and findings |
| Reviewer | read-only on the artifacts and named files | nothing, no session history | findings about the artifact |

Rules per role:
- Explorer: answers a stated question about the existing code. Does not edit. Does not propose design.
- Implementer: works on one task or one batch. Touches only what the task needs. Private helpers are its own design choice. It does not change tests to pass.
- Test-writer: reads the criteria and the Expected Interface, never the implementation. Imports public names only. See references/07-testing.md.
- Verifier: starts with no memory of how the work was done. It receives the spec, the criteria, and the repository. See references/11-verification.md.
- Reviewer: sees the artifact text and the files named in the brief. It never sees the author's session. See references/12-review-panel.md.

## Tiers

Pick a tier by role, not by vendor name. Use these role names.

- Fast tier: explorers, mechanical edits, and reviewer passes on small artifacts.
- Standard tier: implementers, test-writers, verifiers, and most reviewers.
- Reasoning tier: the orchestrator's hard calls, contested review findings, and tasks with design risk.

When a fast-tier worker fails twice on a task, move the task up one tier before trying a third time.

## Isolation and no commits

Decision: no task commits. No worker, and no orchestrator step inside a task, runs `git commit`. Task status and evidence live in the task files, and the changed paths come from git afterward. The person who owns the repository decides when and what to commit.

How isolation works without commits:
- One writer per path. Two workers never edit the same file in the same wave.
- When a worker needs more than a named set of public names, give it a separate working copy of the repository: a copy of the folder, or a git worktree that is never committed in. The worker edits there and leaves its files in place.
- The orchestrator reads the diff of that copy against its base. It then brings the changes into the main working copy by applying the diff or copying the files. It does not merge by committing.
- Remove a working copy only after its handoff file exists. The copy is the only record of the work until the handoff is written.
- Branch names carry the work unit as task-NN-slug, matching the task file (for example task-03-export-csv).
- A worker that sees a conflict with another worker's files stops and reports. It does not resolve the conflict by editing the other files.

The changed paths of a task are derived from git (`git status` and `git diff --name-only`) after the task. They go into the handoff report and later into VERIFY.md. Task files do not list paths.

## Waves and batching

- A wave has at most 3 workers running at the same time.
- Only frontier tasks go into a wave: status todo, every blocker done. Use `python3 scripts/validate_tasks.py tasks --frontier`.
- No two tasks in one wave share a public name in their Interface fields. If they do, run them in separate waves.
- Related small tasks may go to one worker as a batch of up to about 7 tasks. The tasks must touch the same area and have no blockers among them outside the batch. The worker reports per task.
- After each wave: read the reports, check the files on disk, update task statuses, then plan the next wave.

## Handoff report

Every worker ends with a report in this shape:

- Task: the task number and title.
- Changed paths: taken from git, not from memory.
- Evidence: the command run and a short quoted excerpt of its output.
- Status: done, blocked, or failed, with one line of reason when not done.
- Pointer: where the full output or the working copy lives.

The brief you send gives the worker the task file, the sections of the spec it needs, the rules above, and this report shape. It does not give the worker your whole session.

## Judging completion

Judge completion by the files on disk and a check you run yourself, never by the worker's summary. A summary that says done is a claim. Look at the changed paths, run the criteria's checks, and compare the output with the quoted evidence. A worker that reports done without evidence has not finished.

## Dispatch log and DEGRADED mode

Before each send, write one line in the conversation: "Dispatched: <role>, <task numbers>, <tier>, <wave number>". This makes the fan-out visible and lets a resumed session see what was sent.

DEGRADED mode applies when delegation is missing:
- Run the roles in order in separate fresh sessions or clean contexts: explorer, implementer, test-writer, verifier.
- The verifier step must start from a fresh context, even if that means a new session.
- Label every report, VERIFY.md note, and review verdict produced this way as DEGRADED, so the user knows the independence was reduced.

## Nesting

Nested delegation is off. A worker does not start its own workers. If a task is too large for one worker, it goes back to the orchestrator to be split into tasks.
