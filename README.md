# spec-driven-coding

An agent skill for coding work that touches several files. It moves the work through fixed gates. Each gate ends in a written artifact and an exit check, so a person can review the run at known points, and another agent can resume it from the files alone.

The skill is agent-agnostic. It is plain Markdown plus five standard-library Python validators. Subagents are used when the harness can delegate, and the same roles run one after another when it cannot.

Version 0.1.0 (draft). License: MIT, declared in the SKILL.md frontmatter.

## Contents

- [What it does](#what-it-does)
- [When to use it](#when-to-use-it)
- [The gates](#the-gates)
- [Artifacts](#artifacts)
- [Install](#install)
- [Repository layout](#repository-layout)
- [Validation scripts](#validation-scripts)
- [The interface rule](#the-interface-rule)
- [Subagents](#subagents)
- [Verification](#verification)
- [Tests and evals](#tests-and-evals)
- [Status and known limits](#status-and-known-limits)
- [License and credits](#license-and-credits)

## What it does

Agents often write code first and check it afterwards. For work large enough to need it, this skill reverses that order:

1. Scope the request and decide which gates apply.
2. Specify the behavior as acceptance criteria. Each criterion says how it is checked and what result would make it false.
3. Plan slices that each demo something, written as task files.
4. Implement in waves of at most three tasks. The tree runs after every task.
5. Prove the work with command output recorded in `VERIFY.md`. A script checks that file.
6. Optionally compile a frozen `PROMPT.md` and lint it.

The user approves the spec and the task list. The agent never writes its own approval.

## When to use it

Use the gates for a multi-file feature, a change that spans sessions, or any task that needs a spec, a plan, or proof that it works.

Skip them for a one-line fix, a rename, a single regex, or a typo. For those, use only the increment loop in `references/06-increments.md`.

The skill is not a fit for spreadsheets, one-off data pulls with no tests, writing about specs, or reviewing a single file.

## The gates

| Gate | Work | Exit check |
|---|---|---|
| 0 Scope | Size the request and pick the gates | Class named; fits-one-window decision recorded |
| 1 Specify | Frontier rounds, criteria, validation methods | Frontier empty; every criterion has a "False if" clause and a method; spec frozen; approval recorded |
| 2 Plan and tasks | Slices and task files | Drafts pass `validate_tasks.py`; frozen only after the user approves the quiz |
| 3 Increments | Waves of at most three tasks | Each task has status and evidence; runnable after every task |
| 4 Verify | Proofs, completion gate, verifier | `validate_verification.py` exits 0 on `VERIFY.md` |
| 5 Compile (optional) | `PROMPT.md`, lint, coverage | `lint_prompt.py` and `check_interface_coverage.py` exit 0 |

The review panel (`references/12-review-panel.md`) runs at gates 1 and 2 when the artifact is large.

Operating rules ask the user in rounds of at most three questions, each with a recommended answer. When the user cannot be asked, open questions freeze only as provisional decisions recorded in `STATE.md`. The user confirms or changes each one at approval.

Approval is a later user turn. The agent records it in `STATE.md`, quoting the user's words with an ISO date. The agent never writes an approval line on its own.

## Artifacts

| File | Gate | Purpose |
|---|---|---|
| `scope-note.md` | 0 | The class of the request and the reason for it (project root) |
| `specs/spec.md` | 1 | Requirements and criteria. Frozen after approval; holds no approval line |
| `STATE.md` | all | Position, Approvals, Commands, Decisions, Open items (project root) |
| `tasks/NN-slug.md` | 2 | One task: Status, Blocked by, Demo, What it delivers, Interface, Validation method, Criteria, Evidence required |
| `tasks/plan.md` | 2 | Index of the task files |
| `VERIFY.md` | 4 | Head, Tree, Proofs, Verifier, Findings, Verdict |
| `PROMPT.md` | 5 | Optional frozen brief for a fresh agent, with Expected Interface |

Task numbers start at 01 and run without gaps. Branch names carry the work unit as `task-NN-slug`.

## Install

### Hermes

Hermes's linter forbids a README inside a skill folder, so the installed copy leaves out `README.md` and `.git`:

```bash
git clone https://github.com/carloshnp/spec-driven-coding
rsync -a --exclude .git --exclude README.md spec-driven-coding/ ~/.hermes/skills/software-development/spec-driven-coding/
python3 ~/.hermes/skills/software-development/spec-driven-coding/scripts/validate_skill.py ~/.hermes/skills/software-development/spec-driven-coding
```

Expected last line: `0 errors, 0 warnings`.

On Windows without `rsync`, copy the folder and delete `.git` and `README.md` from the copy.

### Other agents

Copy the folder into the directory your agent loads skills from. `SKILL.md` is the entry point. Its load table tells the agent which reference to open for each gate, so the agent reads only what the current gate needs. Nothing else is required. Subagents are optional.

## Repository layout

```
SKILL.md          entry point: frontmatter, purpose, gates, load table, rules, gotchas
references/       17 topic files, flat, each opened on demand
templates/        11 templates: spec, task, state, verification, prompt, review report, ...
scripts/          5 stdlib-only validators
assets/evals/     trigger queries, benchmark cases, answer key, planted-defect fixture
assets/tests/     5 unittest suites
```

A skill folder may hold only `references/`, `templates/`, `scripts/`, and `assets/` as subfolders.

| Reference | Topic |
|---|---|
| 01-scope | Size the request, choose the gates |
| 02-specify | Rounds, decisions, glossary, approval, freeze |
| 03-criteria-and-validation | Criteria, "False if" clauses, validation methods |
| 04-prompt-contract | PROMPT.md format and contract |
| 05-plan-and-tasks | Slices and task files |
| 06-increments | Implementation loop and waves |
| 07-testing | Test design and mutation checks |
| 08-interfaces | Public surface and Expected Interface |
| 09-context-and-resume | Long sessions, STATE.md, resuming |
| 10-subagents | Delegation, roles, tiers, DEGRADED mode |
| 11-verification | VERIFY.md, proofs, the Tree fingerprint |
| 12-review-panel | Independent review at gates 1 and 2 |
| 13-stack-and-env | Build, test, and run commands; Windows notes |
| 14-pitfalls | Failure patterns and their checks |
| 15-benchmark-task-authoring | Tasks graded by a hidden test suite in Docker |
| 16-sources | Credits and licenses |
| 17-web-ui-builds | Browser UI deliverables |

## Validation scripts

All scripts use only the standard library and parse as Python 3.9. Exit codes: 0 pass, 1 findings, 2 usage error.

| Script | Usage | What it checks |
|---|---|---|
| `validate_skill.py` | `python3 scripts/validate_skill.py SKILL_DIR` | Frontmatter and required keys; name matches the folder; description at most 60 characters; SKILL.md size; referenced paths exist; flat references and their length; forbidden files; stdlib-only scripts; denylisted names and slash commands; dashes; eval JSON |
| `validate_tasks.py` | `python3 scripts/validate_tasks.py [--frontier] TASKS_DIR` | File names and numbering from 01; plan.md index; required sections; Status values; Blocked by; Criteria with "False if"; unfilled placeholders. `--frontier` lists todo tasks whose blockers are all done |
| `validate_verification.py` | `python3 scripts/validate_verification.py [--root ROOT] VERIFY.md` | Sections; Tree line; proofs; verdict rules. With `--root`: Head and fingerprint checks. `--fingerprint --root ROOT` prints the working-tree fingerprint |
| `lint_prompt.py` | `python3 scripts/lint_prompt.py [--json] PROMPT.md` | Section pattern; banned words; internal references; Expected Interface fields and headings; unfilled placeholders; compile marker |
| `check_interface_coverage.py` | `python3 scripts/check_interface_coverage.py --prompt PROMPT.md --tests DIR [--package NAME] [--lang auto\|python\|js]` | Test imports against Expected Interface. WARN for names outside the list |

A passing skill directory looks like this:

```
$ python3 scripts/validate_skill.py ~/.hermes/skills/software-development/spec-driven-coding
0 errors, 0 warnings
```

Run `validate_skill.py` on an installed copy. Run on the repository root, it reports `README.md` as a forbidden file. That is the Hermes rule working as intended, and the installed copy has no README.

## The interface rule

The Expected Interface section lists public names only, each with the behavior it must have. Private functions, classes, and constants are the implementer's design choice, and they are never listed.

- Tests target public names. A test that imports a name outside the list gets a WARN from `check_interface_coverage.py`, not an error, because the list is the specification and private code may be tested directly.
- A heading that contains the standalone word "private" or "internal" is an error.
- A CamelCase heading whose first word is Internal or Private, such as `InternalCache`, gets a WARN for review.
- Dunder names such as `__version__` count as public.
- Endpoints and commands are never flagged as unimported.

## Subagents

1. Detect whether the harness can delegate. If it cannot, say so once and use the fallback.
2. If it can, read `references/10-subagents.md` before the first fan-out. Waves hold at most three workers.
3. Judge a worker by the files it left on disk, not by its summary.
4. Workers do not spawn workers. Workers do not commit.
5. Fallback: run the same roles one after another, each in a fresh session that reads only the files it needs. Label every result produced this way DEGRADED, in the report and in the verdict.

## Verification

`VERIFY.md` records the head commit and a Tree line:

- `clean` when the working tree has no changes.
- `dirty` followed by a SHA-256 fingerprint of the working-tree diff and the untracked files. `VERIFY.md` itself is excluded.

A PASS verdict on a dirty tree needs the fingerprint and `--root`. Without `--root`, the validator refuses the verdict. Each proof quotes real command output. A proof whose output says no tests ran is a failing result. Each closed finding names the commit that closed it, as a hex ID of at least seven characters.

## Tests and evals

The unit suites use only the standard library, and they run without pytest:

```bash
for t in assets/tests/test_*.py; do python3 "$t"; done
```

| Suite | Tests |
|---|---|
| test_check_interface_coverage.py | 46 |
| test_lint_prompt.py | 64 |
| test_validate_skill.py | 51 |
| test_validate_tasks.py | 41 |
| test_validate_verification.py | 54 |

The evals live in `assets/evals/`:

- `trigger_queries.json`: 20 queries. 10 should trigger the skill, 6 are near-misses, and 4 are negatives.
- `cases.json`: 7 benchmark cases, including a one-line-fix negative control and a multi-file bug fix.
- `answer-key.json`: 4 planted defects, scored against `fixtures/planted-defect-spec.md`.

The evals are defined but have not been run against a live agent. One blind routing run by a subagent scored 19 of 20 on an earlier build, against a threshold of 18.

## Status and known limits

- **Draft.** Version 0.1.0. The gates and references were written from scratch, then reviewed by subagent panels. The reviews found test and documentation gaps, which were fixed and re-checked.
- **Not yet run:** the eval cases against a live agent, and a full end-to-end run on a real project by a fresh agent. A walkthrough on a small toy project logged its friction points; the fixes are in this version.
- **Windows:** the notes are written, but nothing was run on Windows. Every test and validation so far ran on Linux.
- **Installed copies can drift.** Hermes can run a background curator that edits an installed skill. It did so once for this one. Compare the installed copy with this repository before relying on either.
- **Python:** Python 3 is required. Syntax targets Python 3.9.

## License and credits

Licensed MIT. The full text is in the `LICENSE` file, and the SKILL.md frontmatter declares the same license.

`references/16-sources.md` lists the sources the ideas came from, their licenses, and what was taken from each. The text is written from scratch. Where a source had no detected license, only its ideas were used, and the wording is original.
