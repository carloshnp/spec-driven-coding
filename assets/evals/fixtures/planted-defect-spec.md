# Spec: notes-export command

Status: frozen
Approved: "Looks right, go ahead" (user, 2026-10-12)

## Problem

Users keep short notes as Markdown files in one folder. They cannot hand the
notes to a colleague as a single file. The command `notes export` bundles a
folder of notes into one JSON file.

## Users and scope

- Users: one developer working in a terminal.
- In scope: reading notes from a folder, writing one JSON bundle, a summary line.
- Out of scope: editing notes, syncing, encryption, any network access.

## Requirements

1. The system SHALL read every file with the extension `.md` directly inside the
   source folder. Subfolders are not read.
2. When the user runs `notes export <folder> <output>`, the system SHALL write
   one JSON file at `<output>` holding a list of notes.
3. The system SHALL give each note the fields `title`, `body`, and `modified`.
4. The system SHALL take `title` from the first line that starts with `# `, and
   SHALL use the file name without extension when no such line exists.
5. The system SHALL store `modified` as an ISO 8601 UTC timestamp taken from the
   file's modification time.
6. The system SHALL sort notes by `modified`, newest first, and by `title` when
   two timestamps are equal.
7. When the source folder does not exist, the system SHALL print
   `error: folder not found` to standard error and exit with code 2.
8. When the source folder holds no `.md` files, the system SHALL write an empty
   list and exit with code 0.
9. If `<output>` already exists, the system SHALL stop with the message
   `error: output exists` and exit with code 3, unless the flag `--force` is given.
10. The system SHALL print `exported N notes` to standard output after a
    successful write, where N is the count of notes.
11. Notes that were marked as drafts SHALL be written to the staging ledger
    instead of the main list.

## Assumptions

- Files are UTF-8 text.
- Folders hold at most 5,000 notes.
- The command runs on Linux, macOS, and Windows with Python 3.9 or later.

## Open questions

- Should the bundle also include a `tags` field read from a front-matter block?
  Decision pending from the user.

## Frozen answers

| Round | Question | Answer | Requirement row |
|---|---|---|---|
| 1 | Which format for the bundle? | JSON | 2 |
| 1 | Recurse into subfolders? | No | 1 |
| 2 | Overwrite an existing output? | Only with `--force` | 9 |

## Expected interface

| Path | Name | Type | Input | Output |
|---|---|---|---|---|
| notes/cli.py | main | public function | argv list | exit code |
| notes/bundle.py | build_bundle | public function | folder path | list of note dicts |
| notes/bundle.py | _normalize_title | public function | raw text | title string |
| notes/writer.py | write_bundle | public function | notes, output path, force flag | none |

`build_bundle` returns the notes already sorted as in requirement 6.
`_normalize_title` trims the title and collapses inner whitespace.
`write_bundle` writes the JSON file using two-space indentation.

## Acceptance criteria

1. Given a folder with three `.md` files, the output file holds three notes in
   the order of requirement 6. False if the order differs or a note is missing.
2. Given a missing folder, the exit code is 2 and standard error holds the
   message from requirement 7. False if the code or message differs.
3. Given an existing output and no `--force`, the exit code is 3 and the file
   is unchanged. False if the file content changes.
4. Given an empty folder, the output file holds `[]`. False if it holds anything else.

## Decisions log

Decisions are recorded in STATE.md.
