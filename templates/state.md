# State

## Position
- Gate: [current gate]
- Last finished task: [NN-slug.md, or None]
- Next task: [NN-slug.md, or None]
- Last update: [YYYY-MM-DD]

## Approvals
One line per approval, written only after the user says so in a later turn. The agent never writes the user's words for them.
- Approved by user on [YYYY-MM-DD]: "[the user's own words]"
- Pending: spec not yet approved

## Commands
- Test: [command that runs all tests, and the form that runs one test]
- Build: [command, or None]
- Run: [command that launches the program]

## Decisions
Entries are numbered in order. Status is active or superseded. Log only choices that belong to this project. A superseded entry keeps its text.

### AD-001: [Use a file for storage]
- Status: superseded
- Date: [2026-01-10]
- Decision: [Store records in a JSON file.]
- Rationale: [No server is needed for the first slice.]
- Supersedes: None

### AD-002: [Use SQLite for storage]
- Status: active
- Date: [2026-01-14]
- Decision: [Store records in a SQLite file.]
- Rationale: [The file store could not filter by date without loading everything.]
- Supersedes: AD-001

## Open items
- [Item awaiting an answer, and who answers]
