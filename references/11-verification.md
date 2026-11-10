# Verification

Read this when you reach gate 4, when you write or check VERIFY.md, when you act as the verifier, or when a slice finishes and the integrated result needs checking.

## Contents
- Gate 4 flow
- Proofs are prose
- The VERIFY.md format
- The fingerprint
- The completion gate
- Verifier rules
- Fix pass and escalation
- Evidence rule
- Tamper check
- Mock audit
- Slice boundaries

## Gate 4 flow

1. Confirm every task is done and the working tree holds the integrated result.
2. Run the checks for every criterion and write the Proofs table.
3. Start the verifier in a fresh context. It fills the Verifier table and the Findings table.
4. Fix open findings in one pass, then re-check (see Fix pass and escalation).
5. Fill Head and Verdict. Fill Tree last (see The fingerprint).
6. Run `python3 scripts/validate_verification.py VERIFY.md --root .` (on Windows, `python` or `py -3`). Fix every ERROR. The gate is passed only when the script exits 0 and the verdict is PASS, or when the user accepts a PARTIAL verdict.

Use templates/verification.md as the skeleton.

## Proofs are prose

A proof is a table row of text: the command as it was run, the words the output must contain, and one line quoted from the real output. No tool executes commands from Markdown. The skill's scripts read VERIFY.md and compare text. They never run what a Command cell says. The agent runs the command in its own shell, then copies one line of the output into the row.

This is a settled decision, and it has a reason: a file that runs its own commands is a way to run unreviewed code. Keeping proofs as prose keeps the check safe and auditable.

Proof rule:
- The Expected words cell lists words separated by semicolons.
- Each word must appear in the Output excerpt, in that order, on one line.
- An excerpt that matches the phrase "no tests ran" or "no test ran" (any case) fails.
- The excerpt is not empty.

## The VERIFY.md format

```
# Verification
## Head
<40 lowercase hex characters>
## Tree
clean | dirty <64 lowercase hex>
## Proofs
| Criterion | Command | Expected words | Output excerpt | Result |
## Verifier
| Check | Holds | Finding |
## Findings
| ID | Severity | Summary | Status | Closed by |
## Verdict
PASS | FAIL | PARTIAL
```

Head is the output of `git rev-parse HEAD`. Tree is `clean` when `git status --porcelain` prints nothing, except that a change to VERIFY.md itself is ignored (Editing VERIFY.md does not change the fingerprint either). Otherwise it is `dirty` followed by one space and a 64-character lowercase hex fingerprint. Result is pass or fail. Holds is yes or no. Status is open or closed. Closed by is a commit id of 7 to 40 hex characters, set by the person who owns the repository when a fix is committed. Tasks do not commit, so a closed finding names a commit that already exists.

## The fingerprint

Tasks do not commit, so most trees are dirty at gate 4. The fingerprint ties the Verdict to the exact files that were proven.

1. Finish every proof run and every fix first. The fingerprint is the last step; any later edit makes it stale.
2. Run `python3 scripts/validate_verification.py --fingerprint --root .`. It prints 64 hex characters and exits 0.
3. Write `dirty <those characters>` under Tree. Write `clean` instead when the status output is empty.
4. Run `python3 scripts/validate_verification.py VERIFY.md --root .` to validate.

The fingerprint hashes the output of `git diff HEAD --binary`, then each untracked, non-ignored file (sorted by path, VERIFY.md excluded) as its path, a NUL byte, its bytes, a NUL byte. Editing VERIFY.md does not change it. A PASS on a dirty tree needs `--root` and a matching fingerprint; without `--root`, a dirty PASS is an ERROR.

## The completion gate

validate_verification.py checks these, in order:

1. Every section exists: Head, Tree, Proofs, Verifier, Findings, Verdict.
2. Head is 40 lowercase hex characters. With `--root`, it must equal `git rev-parse HEAD` of that root. If git is unavailable, the script warns and skips the comparison.
3. Tree is `clean` or `dirty` plus a 64-character lowercase hex fingerprint. With `--root`, an empty `git status --porcelain` must agree with clean, and a dirty fingerprint is recomputed; a mismatch is an ERROR.
4. Each proof row: Result is pass or fail; the excerpt is not empty; an excerpt matching "no tests? ran" is a fail; the Expected words appear in the excerpt in order. A row marked pass whose words are missing is an ERROR.
5. Each Verifier row: Holds is yes or no. A "no" must name a finding ID that exists in the Findings table.
6. Each finding: Status is open or closed. Closed needs a Closed by of 7 to 40 hex characters. With `--root`, the commit must exist (`git cat-file -e`).
7. Verdict is PASS, FAIL, or PARTIAL. PASS needs: a valid Head, a clean Tree or a dirty Tree with a matching fingerprint (checked with `--root`), every proof pass, every Holds yes, and no open findings. A PASS that breaks any of these is an ERROR.

The script exits 0 when there are no ERROR lines, 1 when there are, and 2 on a usage error.

## Verifier rules

The verifier is not the author and starts without the author's context.

- It judges each criterion's test: does the test fail if the criterion is false? A test that passes whatever the code does is a finding.
- It writes its own examples for each criterion, including at least one unhappy path, and runs them against the result.
- It reports any assertion that is looser than the criterion, such as a check for "no error" where the criterion names a value.
- A "no" in the Verifier table is never silent. Each "no" gets a finding with an ID, a severity, and a summary.
- It records what it ran and what it saw. It does not repair code. Repair is a separate pass.

Severity values: BLOCKER, MAJOR, MINOR. Any open BLOCKER or MAJOR finding prevents PASS in practice, and the script blocks PASS on any open finding.

## Fix pass and escalation

After the verifier reports, run one fix pass: an implementer fixes the open findings, and the verifier re-checks only those items and anything the fix touched. If findings remain after that pass, stop and escalate to the user with the finding list, what was tried, and the options. Do not loop a third time.

## Evidence rule

A completion claim needs two things: the command output and the artifact path. "Tests pass" with no output is not evidence. "Done" with no path is not evidence. Quote a line, name the file. If the output was empty or said no test ran, the claim is false. Read the exit status of the test command itself. A pipeline reports the status of its last command, so `cmd | tail` shows green for a failing suite. Run the command without a pipe, or read the first command's status, and quote the runner's own count line.

## Tamper check

Compare the working tree with the base commit. The diff must not change any of these, unless a task names them in its criteria:
- test files that existed before the task,
- grader or check files,
- lockfiles,
- caches and generated fixtures.

Use `git diff --name-only` against the base. A change in a listed area without a task that names it is a BLOCKER finding. A test that was edited to pass, deleted while failing, or weakened is the same finding.

## Mock audit

List every test that mocks something. Each mock must stand at an external boundary: network, clock, a paid service, hardware. A mock of the project's own code hides defects. Report each such mock as a finding. See references/07-testing.md.

## Slice boundaries

At the end of each slice, not only at the end of the project, re-validate the integrated result. Run the full check set for the slice's criteria and the criteria of earlier slices, on the integrated working tree. A slice that passed alone can break an earlier one. Record the run in the task evidence, and run the full gate 4 at the end.
