# Plan and tasks

Read this when gate 1 is approved and you are turning the frozen spec into task files, when you are drafting task files before approval (SKILL.md gate 2 allows unapproved drafts), or when you are checking a plan before the quiz.

## Contents

- Task file contract
- Slices that demo
- Prefactor first
- Blocking edges and the frontier
- Numbering and files
- No paths, no code
- The Interface field
- Sizing rule
- Checkpoints
- The quiz gate
- The index file
- Exit criteria for gate 2

## Task file contract

One task is one file: `tasks/NN-slug.md`. The fields are fixed and a script reads them. Use `templates/task.md` as the skeleton.

```
# NN: <title>
Status: todo | running | done | blocked
Blocked by: None | NN, NN
Demo: <one question a person answers by watching the result>
What it delivers: <user-visible behavior, not a layer list>
Interface: None | <comma-separated public names from Expected Interface>
Validation method: tests | cli transcript | computer use
## Criteria
- <criterion>. False if: <the observation that would make it false>.
## Evidence required
- <evidence item>
```

Every criterion carries a "False if:" clause. A criterion with no observation that could falsify it is not a criterion yet. Copy the criteria from the spec as it stands (references/03-criteria-and-validation.md), check the copied criteria against the spec again at freeze, and narrow them to this task. Do not invent new requirements here.

## Slices that demo

Cut tasks as tracer-bullet slices. A slice is a narrow path that is complete through every layer it touches (storage, logic, interface, tests) and works on its own. The opposite is a layer task such as "build the data model", which nobody can watch.

The Demo field is the test. Write one question that a person answers by watching the result, for example "Does `tool add milk` print the new item and does `tool list` show it?" If you cannot write the question, the task is a horizontal layer. Merge it into the slice that uses it.

Order slices so the first one is the thinnest end-to-end path. Later slices widen it.

## Prefactor first

If the existing code makes the feature hard to add, put a prefactor task first. Make the change easy, then make the easy change. The prefactor delivers no new behavior. Its criterion says so: "All existing checks give the same results as before. False if: any check that passed at the base commit fails, or any output differs." Keep it bounded to the code the next slice touches. Do not fold it into a feature task, because then a failure cannot be traced to the refactor or the feature.

## Blocking edges and the frontier

`Blocked by` lists the tasks that must be done before this one can start. Add an edge only when the later task cannot start or cannot be checked without the earlier one. Taste, tidiness, and "it reads better in this order" are not edges. Extra edges remove parallel work.

The frontier is the set of tasks with Status todo whose blockers are all done. Only frontier tasks may start. `python3 scripts/validate_tasks.py tasks --frontier` prints it and changes nothing. A task with `Blocked by: None` is on the frontier at the start.

Rule: a blocker number is strictly lower than the task's own number. This makes cycles impossible by construction.

## Numbering and files

- Two digits from 01, contiguous, no gaps, no duplicates.
- Number order is dependency order: blockers first.
- The slug is lowercase letters, digits, and hyphens.
- One task per file. Never one combined file.

## No paths, no code

Task files carry no file paths and no code. Paths and snippets go stale, and the worker can find the right files by reading the repository. Paths touched by a task are derived from git after the task and recorded in VERIFY.md (references/11-verification.md).

One exception: a fenced block whose info string is `prototype`. Use it only when a prototype already settled a decision that prose states badly, such as a state machine, a schema, or a type shape. Trim it to the decision-bearing lines and say in the surrounding text what it settles. `scripts/validate_tasks.py` ignores path-like text inside a `prototype` block and flags it anywhere else.

## The Interface field

Interface lists the public names from the spec's Expected Interface that this task creates or changes, separated by commas. It lists names only: no paths, no signatures, no private helpers. Write `None` when the task adds no public name, for example a prefactor.

Two uses: the implementer knows which public names it owns, and the orchestrator can refuse to run two tasks that share a name in the same wave (references/10-subagents.md). Private functions, classes, and modules are the implementer's design and never appear here (references/08-interfaces.md).

## Sizing rule

A task fits in one context window: one worker can read what it needs, change it, run the checks, and report without compaction. Two proxies catch most violations:

- Three or fewer bullets under Criteria.
- No "and" joining two actions in the title.

A task that fails a proxy is split by behavior, not by layer. A task so small that it has no honest Demo question is merged into its neighbor.

## Checkpoints

A checkpoint is an ordinary task whose Blocked by lists the tasks it checks. Its criteria re-run the integrated result: the full test command, the launch command, and a walk through the demos so far. Place one after each group of slices that must work together, and one at the end.

## The quiz gate

Before the plan is frozen, show the user the plan as a numbered list. Each item shows three things: Title, Blocked by, What it delivers. Then ask exactly three questions:

1. Granularity: is any task too coarse (more than one context window) or too fine (no demo of its own)?
2. Edges: does each Blocked by entry name a task that really gates this one, and nothing else?
3. Merge or split: should any two tasks be merged, or any one split?

Order of work: write the task files and plan.md as unapproved drafts, run `python3 scripts/validate_tasks.py tasks` on them, then show the quiz list in the same turn as the validated drafts. Revise the drafts and ask again until the user approves. The approval must arrive in a later turn than the list. Freeze only after the user replies with approval. Only after that approval are the drafts frozen, and no task or plan.md edit is made without a new approval. Record the approval in STATE.md under Approvals, in the form given in references/02-specify.md.

## The index file

`tasks/plan.md` is a title line, then one line per task and nothing else:

```
# Plan: <feature>
- 01-first-slice.md: todo
- 02-second-slice.md: todo
```

Every task file appears once. When a task's Status changes, change the same value in plan.md in the same step. `scripts/validate_tasks.py` fails on a missing or duplicate entry. It does not compare plan.md statuses with the task files, so check that yourself.

## Exit criteria for gate 2

- Every task passes `python3 scripts/validate_tasks.py tasks`.
- Every acceptance criterion in the spec maps to at least one task criterion.
- The user approved the quiz list in a later turn, and the approval line is in STATE.md under Approvals.
- The drafts were validated before the quiz and frozen only after the approval.
- For a large plan, the review panel has run (references/12-review-panel.md).
