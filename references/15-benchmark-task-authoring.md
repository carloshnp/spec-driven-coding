# Benchmark task authoring

Read this when the work will be graded by building a Docker image and running a hidden test suite against it (a benchmark-style task with a written brief, a Dockerfile, and a hidden test suite). Skip it for ordinary projects.

## Contents
- What is different
- Dockerfile rules
- run.sh rules
- Version alignment
- Stack portability
- Tests
- Baseline and golden runs
- Release check

## What is different
A grader builds your image, copies in a candidate solution, and runs tests. Nothing you did by hand on your machine counts. Every failure that only appears when the image is built and run is yours to catch before release, because no reviewer reading the files will see it. The prompt (references/04-prompt-contract.md) is the only spec the candidate gets; the tests may check only what the prompt states.

## Dockerfile rules
- The Dockerfile installs dependencies and sets up the runtime. It has no COPY or ADD of project files: the grader supplies the code at run time.
- Pin the base image to an explicit tag. A floating tag can change under you and break the build later.
- Install every dependency the tests need, test runner included. A missing package shows up only on a real build.
- Build the image from a clean state at least once and read the output.

## run.sh rules
- LF line endings only. CRLF makes the shell fail on the first line with an unhelpful error. On Windows, set the editor or git to LF and check the file bytes before release.
- The first line is a shebang for the shell actually present in the image.
- It runs the test command and nothing else of consequence: no network calls, no interactive prompts, no reliance on state from an earlier run.
- It exits with the test runner's status.
- Mark it executable if the grader invokes it directly.

## Version alignment
The language and library versions must agree in three places: the project file (pyproject.toml, package.json), the prompt's Tech Stack, and the Dockerfile. A mismatch (prompt says Python 3.11, image has 3.12) produces failures unrelated to the candidate's work. After any change in one place, grep the other two.

## Stack portability
Choose stacks that build quickly and run without external services.
- Prefer: Python or TypeScript, pytest or Vitest, SQLite or plain files.
- Avoid for graded work: Postgres, MongoDB, Jest, Playwright, Go, Rust. They add services, heavy installs, or flaky runs.
- The task must run offline after the image is built.
- Details: references/13-stack-and-env.md.

## Tests
- Tests import public names only, those listed in Expected Interface. Tests that import private names break valid solutions that organise code differently.
- No mocks of internals. Patching an import path or an internal function ties the test to one layout. Mock only external boundaries, and only when the prompt names them.
- Do not assert on incidental details: exact error message wording, constant names, keyword-only signatures that the prompt did not state.
- Each test traces to a sentence in the prompt. If the prompt does not say it, the test must not require it.
- Make tests deterministic: fixed seeds, no wall clock dependence, no network.
- Check behavior at runtime, not just by reading code: a route that returns a redirect where the prompt says 401, or data re-seeded on every restart, shows only when the app runs.

## Baseline and golden runs
1. Baseline: run the test suite in the same image against an empty codebase (or the starting stub). It must fail. If any test passes on nothing, a broad exception handler or a vacuous assertion is hiding a gap. Fix the test.
2. Golden: run the suite against the reference solution. It must pass completely. If it fails, either the solution or the prompt-to-test mapping is wrong.
3. Run both in the grading environment, not on the host. Record the commands and the quoted output in VERIFY.md (references/11-verification.md).

## Release check
- Image builds from scratch with no cache.
- run.sh has LF endings and runs.
- Versions match across the three places.
- Baseline fails; golden passes.
- Every public name has an importing test (check_interface_coverage) and PROMPT.md passes lint_prompt.
- Rubric lines, if any, each trace to the prompt.
