# Spec: [feature name]

Approvals and decisions are recorded in STATE.md (sections Approvals and Decisions). This file holds no approval line.

## Problem
[Two to four sentences: who has the problem, what happens today, what outcome is wanted.]

## Users and scope
- Users: [who uses the result]
- In scope: [behavior included]
- Out of scope: [behavior excluded, with the reason]

## Requirements
One requirement per line, in EARS form, using the keyword SHALL.
- R-01 (ubiquitous): The [system] SHALL [response].
- R-02 (event-driven): When [trigger], the [system] SHALL [response].
- R-03 (state-driven): While [state], the [system] SHALL [response].
- R-04 (unwanted behavior): If [unwanted condition], the [system] SHALL [response].
- R-05 (optional feature): Where [feature is present], the [system] SHALL [response].

## Expected Interface
Public names only, one line each: the name and its required behavior. The six-field entry for each name (Path, Name, Type, Input, Output, Description) is written in PROMPT.md when it is compiled at the optional gate 5 (references/04-prompt-contract.md). Private items are not listed.
- [Name]: [one-line behavior]

## Assumptions
- [Assumption, and how it will be checked]

## Open questions
Leave this section empty at freeze. Write each question with a recommended answer while rounds run.
- [Question] (recommended: [answer])

## Frozen answers
| Round | Question | Answer | Requirement row |
|---|---|---|---|
| [1] | [question] | [answer in the user's words] | [R-01] |

## Acceptance criteria
Each criterion is one EARS sentence with the word SHALL.
- AC-01 (covers [R-01]; method: [tests, cli transcript, or computer use]): When [trigger], the [system] SHALL [observable result]. False if: [the observation that would make it false].
- AC-02 (covers [R-04]; method: [tests, cli transcript, or computer use]): If [unwanted condition], then the [system] SHALL [observable result]. False if: [the observation that would make it false].

## Decisions log
Decisions made during the work are recorded in STATE.md under Decisions.
