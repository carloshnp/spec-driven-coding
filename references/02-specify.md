# Specify: rounds, decisions, glossary, approval, freeze

Read this when a new spec starts, the request is ambiguous, a term needs a definition, or you are about to freeze or ask approval for a spec.

## Contents

- Frontier rounds
- Facts versus decisions
- Exit and approval
- Freezing answers
- Glossary sharpening
- Decision records
- Completeness checks
- Implicit requirement sweep
- Scenario probes
- Code cross-check

## Frontier rounds

The frontier is the set of open questions that can be asked now. A question is on the frontier only if no other open question must be answered first.

1. List every open question you can find. Mark each one that depends on another open answer. Those wait.
2. Ask the frontier questions, at most 3 per round. Number them.
3. Give each question a recommended answer and one line of reason. The user can reply "yes" to all of them.
4. When the answers arrive, freeze them (see Freezing answers), then recompute the frontier. Questions that were waiting may now be askable.
5. Stop after 3 rounds even if questions remain. List the leftovers as assumptions, show them to the user, and ask for a decision on the ones that carry risk.

Do not ask what the code can tell you. Do not ask what the user already said. Do not bundle a question that has two parts; split it.

## Facts versus decisions

- A fact is something the repository or environment already holds: which framework, where the entry point is, what the tests run on. Send a fresh-context explorer, read only, to find facts. If delegation is not available, read the files yourself, then write the facts down before asking anything. The explorer reports paths and quotes, not opinions.
- A decision is a choice only the user can make: behavior, limits, naming the user will see, what to cut. Ask the user, with a recommendation.

Never ask the user a fact. Never decide a decision silently.

## Exit and approval

The gate exits only when both hold: the frontier is empty, and the user confirms in a later turn.

- The approval line lives in STATE.md under the Approvals section, and nowhere else. Its form is: `Approved by user on ISO-DATE: "QUOTED-WORDS"`. ISO-DATE is a calendar date such as 2026-11-05. QUOTED-WORDS is the user's own words in double quotation marks.
- Quote the words from the user's message. The date is the date of that message.
- The spec header points to STATE.md. The spec holds no approval line of its own.
- The agent never writes this line from its own judgment. If the user has not yet answered, there is no line.
- The same turn that presents the spec cannot carry the approval. Wait for the next user turn.
- A change to the spec after approval makes the line stale. Ask again and add a new line under Approvals; earlier lines stay as history.

## Freezing answers

Each answer becomes a row in the spec's Frozen answers table (templates/spec.md): round number, question, answer, and the requirement row it produced. A requirement row is one EARS sentence (references/03-criteria-and-validation.md). If an answer produced no requirement, the question was not needed or the answer was not applied; find out which.

Open questions must be empty at freeze, or each one has its recommended answer recorded as a provisional decision in STATE.md Decisions. The user confirms or changes each provisional decision at the approval step. A frozen spec with an open question that has no recorded decision is a defect.

## Glossary sharpening

Use a glossary when the same idea is named two ways, or one word means two things.

- Pick one canonical term for each concept. List the words to avoid next to it.
- Define it in one or two sentences, in terms of what it is, not how it is built.
- Include project terms only. Do not define general programming words.
- Leave out implementation details: no class names, no storage format.
- Create the file lazily, when the first real conflict appears. Write each entry at the moment the term is resolved, not at the end.
- Writing the glossary file into the user's repository needs the user's approval of that file in that turn.

Format: templates/glossary.md.

## Decision records

Write a decision record only when all three hold:

1. It is hard to reverse.
2. It would surprise a later reader who lacks the context.
3. There was a real trade-off between options.

If one of the three fails, record the decision as a row in the frozen answers or as an entry under Decisions in STATE.md instead. Name files `NNNN-slug.md` with a four-digit counter. Each file needs the user's approval in that turn. Format: templates/decision-record.md.

## Completeness checks

Before asking for approval, scan the spec for:

- Placeholders: TODO, TBD, "to be decided", empty cells, lorem text.
- Undefined references: a term, a name, or a section the spec uses but never defines.
- What without how to observe: a requirement that states a thing but no way to see it hold.
- No verifiable output: a requirement whose result no command, test, or screen shows.
- Conflicts: two requirements that cannot both hold.

Fix each hit or ask a question about it. Report the scan result in one line.

## Implicit requirement sweep

Walk this list and write one line per item. Either state the requirement or write N/A with a reason. A bare N/A is not allowed.

- Input validation and bad input
- Error messages and exit codes
- Empty, single, and very large cases
- Concurrency and repeat runs
- Permissions and missing files
- Backward compatibility and existing callers
- Logging, and what must not be logged
- Performance limits the user would notice
- Cleanup of partial work after a failure

## Scenario probes

Pick three concrete stories and trace each through the spec: the normal path, a mistake by the user, and an environment fault such as a missing file. If the spec does not say what happens at a step, add a question to the next round.

## Code cross-check

When the work changes existing code, compare the spec against the code once before freeze. List each place where the spec assumes behavior the code does not have, or where the code does something the spec forbids. Each mismatch is a question or a requirement.
