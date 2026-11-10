# Testing

Read this when you write or change tests, map criteria to tests, or review a test that looks too easy.

## Contents

- Public names only
- Real over mocked
- Test integrity
- Anti-patterns
- Coverage matrix
- Bug fixes
- Style
- Negative controls
- The test command

## Public names only

Default to testing through the public names in the spec's Expected Interface. Behavior behind a private function is usually checked through the public name that uses it. Tests may also exercise private code directly when that is the clearest way to pin a rule. `python3 scripts/check_interface_coverage.py` then prints a WARN, not an ERROR: `test imports NAME, which is not in Expected Interface`, or `test imports private name NAME` for an underscore name. It also warns about each importable public name that no test imports. Endpoint and command entries are not importable, so they get no import warning; test them by calling the route or running the command.

The cost of a private import is coupling: a refactor of that private structure breaks the test (references/08-interfaces.md). The Expected Interface is the specification.

## Real over mocked

Use the real implementation. Fake only what sits outside the project and cannot run in the test: a network service, a clock, a payment provider, a hardware device. Prefer a small local stand-in, such as a temporary directory or an in-memory SQLite database, over a mock object.

Never mock the project's own code. A test of a public name that replaces its collaborators with mocks verifies the mocks.

Mock audit: whenever a diff adds or changes a mock, list each one and write why its target is external. A mock of internal code is a finding.

## Test integrity

- Never edit a test to make it pass. If a test is wrong, say why and get the user to agree, then change it in its own step.
- Never delete or skip a failing test.
- Never weaken an assertion (an exact value to "not empty", an equality to a type check) unless a recorded finding says the criterion changed.
- Tests are the executable form of the spec. When test and code disagree, find which one the spec supports.
- The verifier checks the diff for test, grader, lockfile, and cache changes that the task does not name (references/11-verification.md).

## Anti-patterns

| Pattern | Why it fails | Fix |
|---|---|---|
| Assert only that nothing raised | Passes for wrong output | Assert the exact result |
| Assert `is not None` or non-empty | Passes for any value | Assert the expected value |
| Copy the code's own formula into the test | Test repeats the bug | Use a hand-computed example |
| Mock the unit under test | Nothing real runs | Call the real public name |
| Test order or shared state needed to pass | Fails alone or in a different order | Build state inside each test |
| Skip, xfail, or comment out | Hides a red result | Fix the code or raise a finding |
| Test name says more than it checks | Reader trusts a gap | Rename, or add the missing assertion |
| Filter selects zero tests, run is green | "no tests ran" counts as a fail | Check the count in the output |
| Assert a fragment that other messages also contain | Removing the branch leaves the test green | Assert the exact fragment only the branch emits, on an otherwise valid input |

## Coverage matrix

Map every criterion to the test name that proves it. Keep the table in the plan, or in STATE.md under Decisions or Open items:

| Criterion | Test name | Gate |
|---|---|---|
| <criterion text or ID> | <test name> | quick | full | build |

Gate levels:

- quick: the tests for the current task. Run after each change.
- full: the whole test suite. Run at the end of each task and each wave.
- build: full, plus build or type check or lint, and the launch command. Run at checkpoints and gate 4.

A criterion with no test is either validated another way (cli transcript, computer use) and says so, or it is a gap to close before work starts.

## Bug fixes

Start with a failing test that reproduces the bug through a public name. Run it and see it fail for the reported reason. Then fix, and see it pass. A fix without a prior failing test cannot show it fixed the bug.

## Style

Prefer DAMP over DRY in tests: descriptive names and clear steps, even if lines repeat. A reader should see the input, the call, and the expected value in one place, without chasing helpers. Share setup only when it carries no logic.

## Negative controls

Prove a check can fail. Break the code on purpose (or run the check against the base commit), watch the check go red, and restore. For a script or checker, also run it on a deliberately bad sample and see the expected error. Record the red output in the evidence. Build the bad sample valid except for the one property under test: an unrelated error in the same input turns the check red for the wrong reason, which proves nothing about the rule. A test written for behavior that already holds passes at once, so its red step is a mutant of that behavior, applied in a scratch copy, with the failing run recorded.

## The test command

The command that runs the tests, and the quick, full, and build forms, are discovered as described in references/13-stack-and-env.md, run once, and written into STATE.md under `## Commands`. Do not guess a command and do not assume CI. If the project has no tests yet, the first task creates the minimal harness and shows one green run.
