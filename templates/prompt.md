Compile notes (delete this block before linting):
1. Pick the one pattern that fits (letter A, letter B) and keep only its sections. Pattern A keeps Tech Stack and Key Requirements. Pattern B keeps Required Implementation and Deliverables.
2. Replace every bracketed placeholder with real content. Leave no brackets in the compiled file.
3. List public names only under Expected Interface. A public name is one that callers and tests use. The Expected Interface is the specification. Do not list, name, count, nor describe private items. Do not add a heading for them.
4. Write each Description as observable behavior: results for valid input, error cases, edge cases. Do not prescribe helpers and do not prescribe internal structure.
5. Use plain verbs: must, will, is. Do not use hedge words.
6. Do not refer to task numbers, decision numbers, nor other project documents.
7. Rubric is optional: 5 to 30 lines, weights 1, 3, and 5 only, each line a positive and complete statement.
8. Replace every whole-line bracketed placeholder with real content. Delete the sections the chosen pattern does not use.
9. Run the prompt lint script and the interface coverage script before freezing.

## Title
[One line naming the deliverable]

## Description
[What is to be built and why, in plain sentences.]

## Tech Stack
[Language, runtime version, frameworks, test runner, and package manager, each with a version.]

## Key Requirements
[Numbered list of the behaviors that must hold, each observable.]

## Current State
[What exists today in the codebase, and what is missing.]

## Required Implementation
[What must change, stated as required outcomes.]

## Expected Interface
### [Name]
- Path: [file where the name is defined, and N/A when none]
- Name: [Name, identical to the heading]
- Type: [one of: public function, public method, public class, public type, public constant, endpoint, command]
- Input: [parameters with types, and N/A when none]
- Output: [return value with type, and N/A when none]
- Description: [required observable behavior: results for valid input, error cases, edge cases]

## Deliverables
[The files, commands, and results that must exist when the work ends.]

## Rubric
- (w1) [minor criterion, stated positively]
- (w1) [minor criterion, stated positively]
- (w3) [important criterion, stated positively]
- (w3) [important criterion, stated positively]
- (w5) [critical criterion, stated positively]
