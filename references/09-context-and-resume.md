# Context and resume

Read this when a session is long, the context is filling up, a session restarts mid-project, or you need to log a decision in STATE.md.

## Contents
- Load by condition
- The environment is the source of truth
- STATE.md and the decisions log
- What to log
- Resume procedure
- Checkpoint before compaction
- Protecting the orchestrator context

## Load by condition

Load a reference only when its condition holds. SKILL.md carries the load table. Do not read all references at the start of a session. A reference that is not needed costs context and adds nothing.

Keep the working set small:
- The current task file, not the whole tasks folder.
- The frozen spec sections the task touches, not the full history of the questions that produced them.
- Command output as a short excerpt, not the full log. Save the full log to a file and keep the path.

## The environment is the source of truth

The conversation is not the record. The record is the files on disk and the git history. Anything that must survive a restart goes into a file: the spec, the task files, STATE.md, VERIFY.md.

Rules:
- Never rely on remembering what a task status was. Read the task file.
- Never trust a summary of work as proof that work happened. Check the files and run the check.
- When the conversation and a file disagree, the file wins until you have checked git. Then fix whichever one is wrong.

## STATE.md and the decisions log

STATE.md holds the current position and the decisions made on the way. Use templates/state.md as the skeleton. STATE.md sits at the project root, next to specs/ and tasks/. It has five sections: Position (gate, last finished task, next task, last update), Approvals (one line per user approval, kept only here), Commands (test, build, run), Decisions, Open items.

Each decision is an entry with an ID of the form AD-NNN (three digits, from 001, never reused):

- Status: active or superseded.
- Date.
- Decision: one or two sentences.
- Rationale: why, in one or two sentences.
- Supersedes: the earlier ID, or None.

When a later decision replaces an earlier one, write a new entry that names the old ID in Supersedes. Then change the old entry's status to superseded; in templates/state.md, AD-001 shows status superseded once AD-002 supersedes it. Do not delete or rewrite the old entry's text. The history stays readable.

Section-scoped writes: edit only the section you mean to change. Add an entry under Decisions without touching Position. Update Position without touching Decisions or Approvals. This keeps two sessions from overwriting each other's work and keeps diffs small.

## What to log

Apply the project-only test before writing an entry: would a person who knows only this project, and not the general domain, need this fact to continue the work? If yes, log it. If the fact is general programming knowledge, do not log it.

Log:
- A choice between two real options for this project, with the reason.
- A constraint discovered while working, such as a toolchain limit.
- A change to the plan, such as a task split or an edge removed.
- An answer the user gave that is not already a frozen requirement row.

Do not log:
- Progress notes. Task status lives in task files.
- Things already in the spec or in a decision record.
- Guesses. Write an assumption in the spec's Assumptions section instead.

A decision that is hard to reverse, surprising without context, and a real trade-off becomes a decision record instead (see references/02-specify.md). The STATE.md entry then points to the record.

## Resume procedure

Run this when a session starts and work already exists.

1. Read SKILL.md, STATE.md (Position and Commands first), tasks/plan.md, and the task files. Read nothing else yet. Do not reread the whole spec unless a task needs it.
2. Reconcile with git. Run `git status` and `git log` on the branch. Compare the list of changed paths with the tasks marked done or running.
3. Spot-check the evidence of tasks marked done. Pick at least one done task, and every task whose evidence looks thin. Re-run its check and compare the output with the recorded excerpt. If it fails, set the task back to todo and add an entry to STATE.md.
4. Handle running tasks. A task marked running with no live worker is unreachable. Check its working copy or the files on disk. If the work is complete and its check passes, mark it done. If not, set it to todo and re-delegate it with a fresh handoff. Do not assume the previous worker finished.
5. Run `python3 scripts/validate_tasks.py tasks --frontier` to get the next tasks. On Windows use `python` or `py -3`.
6. State in one short message where the project stands and which task comes next, then continue.

If STATE.md is missing from the project root but task files exist, rebuild Position from the task files and git, and say so.

## Checkpoint before compaction

When the context is about to be compacted, or when you end a session, write a checkpoint first:

- Update Position in STATE.md: the current gate, the last finished task, the next task, the last update.
- Add any decision not yet logged.
- Make sure each task file has its true status and evidence.
- List open questions for the user under Open items.

A checkpoint is good when a new session that reads only STATE.md, the task files, and git can continue without asking what happened.

## Protecting the orchestrator context

The orchestrator is the session that talks to the user and holds the plan. Keep it light.

- Delegate reading and searching to explorers and let them return a short report. See references/10-subagents.md.
- Ask every worker for a compact report with a fixed shape. Do not paste worker transcripts into your context.
- Keep state on disk, not in the conversation.
- Do not open large files in full. Search first, then read the lines you need.
- When a command prints more than a screen, save the output to a file and read the tail or the matching lines.
- When the context still grows, checkpoint, then continue in a fresh session with the resume procedure.
