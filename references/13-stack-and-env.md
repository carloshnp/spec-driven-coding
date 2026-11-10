# Stack and environment

Read this when you start a project and need to learn what tools exist and run, when you choose a stack for work that a Docker grader will run, or when you must record the build, test, and run commands.

## Discover before you choose

Look at what is there before proposing anything.

1. Find the project files that name a stack: a package manifest, a lockfile, a build file, a test config, a container file. List what exists. Do not assume a file you did not see.
2. Find the language and tool versions the project pins. Note each pin and where it came from.
3. Find how tests are run today. If there are no tests, say so in the spec's assumptions.
4. Find any existing instructions file for agents. Read it, and note its rules as standing constraints. Do not copy its text into the spec.
5. Empty project: ask the user for the stack in a gate 1 round, with a recommended answer from the portability list below.

## Feasibility: what runs

Do not write criteria that depend on a tool you have not run. Before gate 1 closes, answer three questions by running things.

| Question | How you find out | Record |
|---|---|---|
| What kind of program is it? (library, CLI, service, web UI, script) | Read the request and the entry points | One word in the spec |
| Does the toolchain run here? | Run the version command of each tool, then run the existing tests or a trivial build | The command and its first output line |
| How is it launched? | Find or define the one command that starts it | The launch command |

If a tool is missing, report it with the command that failed. Do not write criteria that need it, and do not install system software without the user's approval.

A criterion that needs a browser, a display, or a network service is only valid if the harness can drive it. Computer use is a validation method only when the harness offers it (references/03-criteria-and-validation.md).

## Portability for Docker-graded work

When a Docker grader will build and run the result, pick the stack least likely to break in a clean image.

| Prefer | Avoid | Reason |
|---|---|---|
| SQLite or plain files for storage | A database server such as Postgres | A server needs a second process and setup in the image |
| pytest for Python tests when installed (otherwise unittest) | Test runners that need a browser download | Fewer install steps, no network at run time |
| Vitest for TypeScript tests | Jest | Vitest needs less configuration for modern TypeScript |
| Python or TypeScript | Go, Rust | Compile steps, longer builds, more version drift |
| Command-line or HTTP checks | Playwright and other browser drivers | Browser binaries are large and fragile in images |

These are defaults, not rules for every project. A project that already uses another tool keeps it. For the full set of Docker rules (Dockerfile, run script, line endings, version alignment), read references/15-benchmark-task-authoring.md.

## Record the commands

Write the commands once, under `## Commands` in STATE.md (templates/state.md), and use them everywhere else.

**Test runner:** use pytest when it is installed; otherwise use unittest. Both run without network access. Say which one the project uses in Commands.

- Test command, with the filter form that runs one test and the form that runs all of them.
- Build command, if any.
- Run (launch) command.
- Lint or type-check command, if the project has one.

Every proof in VERIFY.md and every criterion check uses these exact commands. Make the test command print the number of tests that ran, so an empty selection shows up as zero and not as a pass. An output that matches "no tests ran" or "no test ran", or that collects nothing, is a failing proof, not a pass.

Do not assume a CI service. This skill has no CI step. Where a source says "CI must pass", the equivalent here is the recorded test command, run by the agent, with the output quoted in VERIFY.md.

## Windows notes

- Use `python` or `py -3` where `python3` is not found. Say which one worked in the recorded commands.
- Shell steps in this skill use POSIX syntax. On Windows, run them in Git Bash, or translate each one and record the translation.
- Keep repository files at LF line endings. A script saved with CRLF endings fails in a Linux image with an error that points at the wrong line. When creating a shell script, write it with LF and check with a byte-level look at the first line.
- Use forward slashes in relative paths inside documents. Let the tools translate.
- Do not rely on a case-insensitive file system. Match file name case exactly.

## Secrets and files

- No secrets in files. Never write tokens, keys, passwords, or connection strings into the spec, tasks, state, proofs, or tests.
- Read secrets from the environment. Name the variable in the docs and leave its value out.
- Do not create environment files with real values. If a sample is needed, write a placeholder name only.
- Do not paste command output containing a secret into VERIFY.md. Cut the line and write "redacted".
- Do not read or print a secret to check that it exists. Check for presence of the variable with a test that prints only yes or no.
