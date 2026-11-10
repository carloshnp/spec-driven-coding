# Prompt contract (PROMPT.md)

Read this when the user asks for a PROMPT.md, a compiled brief, or a frozen self-contained task statement, or when you run gate 5.

## Contents
- Two patterns
- The interface rule
- Expected Interface entry format
- Banned words and their positive targets
- Rubric rules
- No internal references
- Compile steps

## Two patterns
PROMPT.md is a frozen, self-contained copy of the work for a reader who has none of your context. Pick one pattern and keep its section order.

Pattern A (build something new or a feature with a stated stack):
1. Title: one line.
2. Description: what is wanted and why, in plain sentences.
3. Tech Stack: language, runtime, test framework, and pinned versions.
4. Key Requirements: numbered, one observable requirement each.
5. Current State: what exists now (write "empty repository" when true).
6. Expected Interface.

Pattern B (change an existing codebase):
1. Title.
2. Description.
3. Current State: what the code does today and what is wrong or missing.
4. Required Implementation: the changes, stated as outcomes.
5. Expected Interface.
6. Deliverables: what must exist when the work ends.

Every PROMPT.md needs Title, Description, and Expected Interface. Rubric is an optional last section. The spec (SPEC.md) holds the living detail; PROMPT.md holds only what a reader needs to do the work and what a grader will check.

## The interface rule
The Expected Interface lists only public names with their required behavior; every private function, method, class, module, or constant is the agent's own design choice and is not listed, described, or restricted; tests target public names, and the Expected Interface is the specification.

In full:
- Public means a name that callers or tests use. The Expected Interface section is the complete list. Nothing outside it is public.
- Each public name gets one entry. The Description of an entry is the implementation requirement for that name: observable behavior, results for valid input, error cases, edge cases.
- A Description does not prescribe internal structure, algorithms, or helper decomposition. Exception: the brief requires that exact structure; then the Description states the structure and says why.
- Private means everything not listed: functions, methods, classes, modules, constants. They are not listed, not described, not named, and not counted in PROMPT.md. The agent designs them as part of the system. Nothing in this skill caps their number, location, or names beyond the conventions of the chosen stack.
- PROMPT.md has no section for private or internal items. A heading inside Expected Interface that contains the separate word "private" or "internal" is an error.
- Private code may be tested directly. A test that imports a project name missing from the list gets a WARN from the coverage script, not an error; the Expected Interface remains the specification, so add the entry if the name is truly public.
- See references/08-interfaces.md for design guidance on public surfaces.

## Expected Interface entry format
Six fields, in this order, one entry per `###` heading. Input and Output may be N/A. The other four need content.

```
### parse_config
- Path: src/config.py
- Name: parse_config
- Type: public function
- Input: path (str), the file to read
- Output: dict mapping section names to key-value dicts
- Description: Reads an INI file and returns its sections. Raises FileNotFoundError when the path does not exist. Returns an empty dict for an empty file. Later duplicate keys replace earlier ones.
```

- Path: the file that defines the name. N/A is allowed for any Type when no single file defines the name. The layout of everything else is free.
- Name: identical to the heading. A method uses Class.method. A name never begins with an underscore, except a dunder such as `__init__`.
- Type: one of public function, public method, public class, public type, public constant, endpoint, command. No other value is valid.
- Use references/08-interfaces.md for what each Type means. Use templates/interface-entry.md as the starting entry.

## Banned words and their positive targets
The lint script rejects these words in PROMPT.md prose (fenced code and lines marked `<!-- allow-banned -->` are skipped). Each ban has a replacement target.

| Banned | Target |
|---|---|
| should | "must" for a requirement, or a plain statement of fact |
| or | one chosen option; if two cases both apply, write two sentences |
| alternatively | delete it and keep the one chosen route |
| either | name the single choice |
| recommended | state the decision: "Use X" |
| etc. | list every item, or state the rule that defines the set |
| you can | an imperative sentence, or "the function accepts" |
| something like | give the exact value, format, or an example marked as an example |
| relevant technologies | name each technology with its version |

Rule behind the list: where the prompt offers a choice, two agents build two different things. Pick one reading and commit. Do not carry contradictions from the spec into the prompt; resolve them at gate 1.

## Rubric rules
The Rubric section is optional. When present:
- 5 to 30 criteria, one per line: `- (w1) text`, `- (w3) text`, `- (w5) text`.
- Weights are only 1, 3, or 5. Use 5 for core behavior, 3 for important behavior, 1 for minor behavior.
- Positive phrasing: state what is true when the work is right ("Returns an empty list for empty input").
- Atomic: one check per line. Split a line that holds "and".
- Self-contained: understandable without the spec or the code.
- Only criteria the prompt itself states. A rubric line that needs knowledge missing from the prompt, or that mandates an unrequired library or style, is a defect.
- Observable: a grader can decide it from behavior or output. Replace "clear" or "clean" with a measurable condition.
- See templates/rubric.md.

## No internal references
Strip every pointer into your working notes: TODO, FIXME, TBD, "task 3", "AD-004", "TLC-12", spec section numbers, round numbers. The reader of PROMPT.md sees nothing but PROMPT.md.

## Compile steps
templates/prompt.md opens with a block headed `Compile notes (delete this block before linting):`, then an instruction list. Every placeholder in the template is a whole-line bracketed value. The lint script reports an error for a leftover whole-line placeholder and for the compile marker line.

1. Confirm the spec is frozen: no open questions, user approval recorded (references/02-specify.md).
2. Choose pattern A or B from Current State.
3. Derive each public name and its Path from the code or from the planned interface, not from memory. Write one entry per name.
4. Write Description, Key Requirements or Required Implementation as outcomes. Replace every banned word with its target.
5. Remove internal references. Check no private item is named anywhere.
6. Replace each whole-line bracketed placeholder with real content, and delete the whole Compile notes block, marker line included, plus any section the chosen pattern does not use.
7. Run `python3 scripts/lint_prompt.py PROMPT.md`. Fix every ERROR. On Windows use `python`.
8. Run `python3 scripts/check_interface_coverage.py --prompt PROMPT.md --tests <tests dir> --package <name>`. A WARN that a test imports a name outside the list: add the entry if the name is truly public, otherwise keep the private test and accept the WARN, or route it through a public name. A WARN that a public name has no importing test: add one.
9. Freeze: do not edit PROMPT.md again unless the spec changes and the user approves.
