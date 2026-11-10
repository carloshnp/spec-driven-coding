# Criteria and validation

Read this when you write or check acceptance criteria, pick how each criterion is validated, or confirm the work can be run at all.

## EARS patterns

Write each requirement as one sentence in one of five patterns. Use the keyword SHALL. One requirement per sentence.

| Pattern | Form | Example |
|---|---|---|
| Ubiquitous | The <system> SHALL <response>. | The exporter SHALL write UTF-8 output. |
| Event-driven | WHEN <event>, the <system> SHALL <response>. | WHEN the file is missing, the loader SHALL exit with code 2 and name the path. |
| State-driven | WHILE <state>, the <system> SHALL <response>. | WHILE a sync is running, the status command SHALL print "syncing". |
| Unwanted behavior | IF <condition>, THEN the <system> SHALL <response>. | IF the token is expired, THEN the client SHALL refresh it once and retry. |
| Optional feature | WHERE <feature is present>, the <system> SHALL <response>. | WHERE a config file exists, the tool SHALL read defaults from it. |

If a sentence needs "and" between two results, split it into two criteria.

## Criteria rules

A criterion is good when a stranger can run it and get a clear yes or no.

- Observable signal. Name what is seen: an output line, an exit code, a returned value, a file, a screen element. "Works well" is not a signal.
- Unhappy paths. For every main behavior, write at least one criterion for bad input or a failure.
- Must-not-change. State what has to stay the same: existing output, existing callers, data already on disk. A regression criterion is a real criterion.
- Pinned interfaces. When a criterion touches a public name, use the exact name from the Expected Interface (references/08-interfaces.md). The Expected Interface is the specification. Do not name private items in criteria.
- No how. Say what is observed, not how the code does it.

## False if

Each criterion carries the observation that would prove it false:

`- WHEN the file is missing, the loader SHALL exit with code 2. False if: the exit code is 0 or 1, or the message omits the path.`

A criterion with no False if clause cannot be checked, so it does not pass the gate. Write the clause as a result a person could see, not as a restatement.

## Validate before you build

Gate 1 for a change to existing code: each criterion must fail at the base commit, before any work, for the right reason. Run its check on the untouched code and record the output.

Gate 1 for a new feature (no base commit exists): write each criterion's test and run it before any implementation. It must fail. A missing-name error, such as an import error for a public name not yet defined, counts as a failure. The red output goes into the task's Evidence required section at gate 3.

- If it passes already, the criterion is empty or the feature exists. Rewrite it or drop it.
- If it fails for the wrong reason, such as an import error or a missing file in the test itself, fix the check until it fails on the behavior.
- A check that cannot run yet because the code it imports does not exist counts as failing. Note it, and write the minimal public stub first only when the stack needs one. When the whole module tree is absent the runner reports a collection error with zero collected tests (`Test Files N failed`, `Tests no tests`) and a non-zero exit: that is the red proof for those criteria, so record the file-level lines instead of rejecting the run as "no tests ran".
- Tests target public names. Private code may be tested directly when that is the clearest check, but the Expected Interface stays the specification: a test that imports a name outside it gets a WARN from scripts/check_interface_coverage.py, so either add the name to the Expected Interface or move the check to a public name.

## Validation method per criterion

Pick one method for each criterion and write it in the task file's Validation method line.

| Method | Use when | Evidence |
|---|---|---|
| tests | The behavior is reachable through public names in code | A test name and its run output |
| cli transcript | The behavior is a command with output and an exit code | The command, the output, and the exit code, quoted |
| computer use | The behavior is on a screen, and the harness can drive one | Screenshots or a step log |

Choose computer use only when the harness offers it. If it does not, move the criterion to a cli transcript, or ask the user how to validate it. Prefer tests when both work, because tests repeat.

## Feasibility discovery

Before freezing, confirm the criteria can be run in this environment.

1. Program type. Library, command line tool, service, web page, script. This fixes the method.
2. Toolchain. Run the install or build command and the test command once on the base commit. Record the exact commands in the stack file (references/13-stack-and-env.md).
3. Launch command. For a tool or service, find the command that starts it and run it once.
4. If any step fails, tell the user now. A spec that cannot be run is not frozen.

## Exit criteria before decomposition

Write the exit criteria of the whole change before you split it into tasks: the list of criteria that, all passing, mean the work is done. Tasks later take slices of this list. A task criterion that is not part of the whole list is scope creep; a whole-list criterion no task takes is a gap.

## Sweep for the defects a panel always finds

Run this before freezing. Each line is a defect class that survives a first draft and costs a panel iteration.

- Enumerated surfaces. When a requirement names a list (search operators, accepted formats, actions, shortcuts, views), every member needs its own criterion, or one criterion that names each member and its expected result. Count the members, count the criteria, compare. A requirement listing seven operators with a criterion covering two passes a careless reading and fails review.
- Interface completeness. Every type named in a public signature (options, queries, state shapes, document formats) gets an Expected Interface entry, and a discriminated union lists its members. A reducer or handler whose accepted actions are unnamed cannot be implemented to spec.
- Assumption traceability. Every Assumption ends by naming the criterion that checks it, and that criterion must exist and actually assert it. "Checked by the compose tests" with no compose criterion is worse than an unstated assumption, because it claims coverage.
- Aggregate versus per-item semantics. When a flag lives on children but requirements speak about the parent (a starred conversation, a read thread, a completed batch), state the derivation and whether an action applies to all children or only one. Reviewers read the child flags and the parent wording as a contradiction otherwise.
- Persistence boundaries. Every write has a stated failure result and a user-visible outcome: quota or permission failure, a stored document that no longer parses, a second writer, a schema version change. Decide whether a rejected document is preserved or destroyed, and name the key or path it is preserved under.
- Guards at the transition, not only at the form. When a public function or reducer can reach the same operation as a UI form, put validation on the shared path. A guard that lives only in the widget is a blockable finding, because the public entry bypasses it.
- Sanitizing and normalizing at every entry and at render. A transform applied only when data is written leaves stored, imported or hand-edited data unguarded on the read path.

## Checks before leaving this step

- Every criterion is one EARS sentence with SHALL.
- Every criterion has a False if clause and a method.
- Every criterion was run and failed for the right reason: at the base commit for existing code, before implementation for a new feature (a missing-name error counts), or is noted as waiting on a stub.
- At least one unhappy path and one must-not-change criterion exist.
- The toolchain, test, and launch commands ran once and are recorded.
