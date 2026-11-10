# Pitfalls

Read this when a gate is about to close, when a run looks suspiciously smooth, or when you want the check behind one of the gotchas listed in SKILL.md.

## Contents

- How to read the evidence column
- Pitfall table
- Using the table

## How to read the evidence column

Each evidence cell names a source type and how far to trust it. The strength labels used here:

- Peer-reviewed-style paper abstract: a paper with a method and numbers. The agent read the abstract or the introduction, not the full paper.
- Preprint: a paper not yet reviewed. Numbers may change between versions.
- Vendor study: published by a company with an interest in the result.
- Single project: one case study. It shows the failure can happen, not how often.
- Author assertion: an essay or post with reasoning and examples but no measurement.
- Local guideline: the user's own quality-control document. Strong for that program, unproven elsewhere.

No row rests on a controlled trial of this skill. Treat each check as a precaution that costs little, not as a proven fix.

## Pitfall table

| Pitfall | Evidence and strength | Check | Reference |
|---|---|---|---|
| Spec text grows until nobody reviews it | Single project: a one-person case study found hours of review for thousands of lines of markdown, against minutes for small prompts. Author assertion in a second essay. | Size gate before gate 1; cap criteria bullets per task | references/01-scope.md |
| Spec used for a one-line fix | Vendor study (self-published, 50 tickets, wide noise band): gains for multi-file features, none for bug fixes and refactors. | Run only the increment loop for one-line fixes | references/01-scope.md |
| Agent ignores or over-follows spec text | Author assertion: one writer saw existing classes treated as new spec, and one rule over-applied. | Verifier reads each criterion against the code, not the spec's tone | references/11-verification.md |
| Spec and code drift apart | Vendor study: drift in a minority of merged tickets even with specs. Author assertion in critiques. | Re-check criteria at each slice boundary; spec updates need a user turn | references/11-verification.md |
| Agent writes tests that pass without testing | Preprint: tests judged correct still broke task requirements in about a third of trials. | Verifier writes its own examples; negative controls | references/07-testing.md |
| Agent games visible tests | Preprint on conflicting tests: high cheat rates for one model, and a prompt change cut them sharply. Single setting. | Held-out checks by the verifier; tamper check on the diff | references/11-verification.md |
| Gap between visible and held-out passes grows with task size | Preprint plus a blog from the same authors: gap up to the whole score on very large tasks. | Split large work into features with separate checks | references/05-plan-and-tasks.md |
| Agent edits the grader, lockfile, or cache | Vendor report from a benchmark maintainer: a forged checksum and edited module cache in a few runs. Strength: documented incident, small count. | Diff must not touch tests, lockfiles, grader files, caches unless the task names them | references/11-verification.md |
| Agent claims done without proof | Preprint on session logs: premature self-reported success was a large share of misaligned sessions. Single project: a task marked verified with no tests. | Completion claim needs command output and artifact path; validate_verification | references/11-verification.md |
| Too many mocks in agent tests | Peer-reviewed-style paper abstract (mining study): agent commits add mocks more often than human commits. The fix proposed there is untested. | Mock audit of every test change; mocks only at external boundaries | references/07-testing.md |
| Test names or paths the prompt never states | Vendor report and preprint: audits of a benchmark found tests that need unstated names; the share varies by how the spec was written. | Tests import public names only; check_interface_coverage | references/08-interfaces.md |
| Tests check behavior the prompt never states | Vendor report: an audit found a minority of problems where tests went past the description. | Every asserted name, header, or message appears in an interface Description | references/04-prompt-contract.md |
| Context file bloats and slows the agent | Preprint (wording changed between versions): context files did not generally help and cost more. A mining preprint found bloat and lint leakage common. | Load references by condition; keep the instructions file short | references/09-context-and-resume.md |
| Prose rules carry no force | Vendor doc: instruction files are context, not enforced settings. | Put hard limits in scripts and gates, not in advice | references/11-verification.md |
| Parallel writers corrupt a shared tree | Author assertion and community advice: use one working copy per writer. No measurement. | No two tasks sharing a public name in a wave; separate working copies | references/10-subagents.md |
| Model blames the runtime for a limit it set itself | Local guideline plus single project: batches trimmed to a smaller number, blamed on the system. | Read the logs and the documented caps before accepting the claim | references/10-subagents.md |
| Prompt says one thing, rubric or tests say another | Local guideline: the largest class of rejected prompts in the user's own quality-control notes (conflicting instructions, misaligned description). | lint_prompt; trace each rubric criterion to a stated sentence | references/04-prompt-contract.md |
| Golden solution fails at run time or in the image | Local guideline: missing dependency, line-ending errors, version mismatch. | Run baseline on empty code and the golden solution in the grading image | references/15-benchmark-task-authoring.md |
| Review of the artifact alone misses hacks | Preprint: a review panel that saw only code and score missed a small share of confirmed hacks. | Recompute results independently; do not rely on the panel for proof | references/12-review-panel.md |
| Truncated artifact gives false blockers | Author assertion in the method notes; no data. | Pass the artifact whole; stop above about 2,000 lines | references/12-review-panel.md |
| Endless review loops | Author assertion: later rounds add only style noise. No data for the cap value. | Iteration cap 3, then override or abort | references/12-review-panel.md |
| Context lost across sessions | Author assertion; consistent with harness docs that sessions are isolated. | STATE.md and task files; resume procedure | references/09-context-and-resume.md |
| Tasks sliced too fine | Author assertion: many tiny tasks add handoffs and lose shared context. No measurement; the 7-task batch size is a judgment call. | Batch related tasks; merge a task that cannot be demoed alone | references/05-plan-and-tasks.md |
| Horizontal slicing (database, then API, then UI) | Author assertion in planning essays: nothing is demoable until the last layer. Strength: reasoning, no data. | Each task has a demo question and crosses every layer it needs | references/05-plan-and-tasks.md |
| Verifier reads only the writer's summary | Single project: a task marked verified with no run behind it. Author assertion otherwise. | Verifier runs its own examples against the files, in a fresh context | references/11-verification.md |
| Review panel passes empty | Author assertion: reasoning from how a quorum can be miscounted. No measurement. | Count valid reports; quorum fails closed; `FINDINGS: none` must be written | references/12-review-panel.md |
| Accepted list is always empty | Author assertion: reasoning from how pairing logic can fail silently. No measurement. | Check that accepted plus contested equals the finding count | references/12-review-panel.md |
| Questions asked before earlier answers exist | Author assertion: reasoning that a question which depends on an open answer gets a guessed premise. No measurement. | Each round holds only questions with no open dependency | references/02-specify.md |
| Criteria that cannot fail | Author assertion: a criterion with no False if clause passes whatever the code does. No measurement; observed once in this project. | Every criterion has a False if clause and fails at the base commit | references/03-criteria-and-validation.md |
| Agent writes the approval line | Author assertion: an agent can write a plausible approval line itself. No measurement. | Approvals hold the user's own words with a date, in STATE.md only | references/02-specify.md |
| Dead gate code | Author assertion: a check that is defined but never called protects nothing. No measurement. | Negative control: feed each check a bad sample and see it fail | references/07-testing.md |
| Gate exits 0 while checking nothing | Author assertion; common test runners do exit 0 when a filter selects zero tests. No measurement of how often agents hit it. | Reject "no tests ran"; require a nonzero count in the output | references/11-verification.md |
| Pipeline hides a failing command | Observed in this project (several runs): a suite piped through tail reported green. No measurement. | Quote the runner's own exit status and count line, with no pipe | references/11-verification.md |
| A revision written to clear findings adds contradictions | Observed twice in one spec run: a keep-it rule and a membership rule disagreed about trashed mail, and a shortcut guard disabled the key a later rule required. | Before re-panelling, list every requirement naming a state, view, count, key or verb, and confirm no two requirements and no criterion disagree about it | references/03-criteria-and-validation.md |
| An action described as both a toggle and idempotent | Observed: "star is idempotent when repeated" against "the toggle flips" cannot both hold; two reviewers returned it as a blocker. | Read each action's verb: a toggle restores on a repeat, only set-style actions are idempotent; say which in the action table | references/08-interfaces.md |
| The action table sets fields the state type does not have | Observed: actions set a label error and an info notice while the state type carried neither, and a criterion required a visible error. | For every "sets X" in the action table, find X in the state type and name the element that displays it | references/08-interfaces.md |
| A first run treated as a corrupted document | Observed: "an absent document shows a notice and backs up the old one" would fire on every fresh install with nothing to back up. | Enumerate the load outcomes and give each its own rule: absent is silent, corrupt backs up, unavailable refuses writes | references/03-criteria-and-validation.md |
| Save and revision bookkeeping left implicit | Observed: a stale-write guard that never advanced refused the app's own second save. | State what a successful save writes and what adopts it, then test two consecutive saves from one session | references/11-verification.md |

## Using the table

- Before closing a gate, read the rows that name its reference and run the check.
- When you meet a failure not listed here, add a row only after you can state the evidence strength honestly. "Observed once in this project" is an acceptable strength.
- A row's check is a cheap guard. If a check fails, record a finding in VERIFY.md and do not argue with it.
