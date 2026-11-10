# Interfaces

Read this when you design or change something callers or tests use: a function, class, endpoint, command, type, or constant, or when you write the Expected Interface for a prompt.

## Contents
- The public and private split
- Type values
- Contract first
- Error semantics
- Validate at boundaries
- Addition over modification
- Hyrum's Law
- Endpoints and commands

## The public and private split
The Expected Interface lists only public names with their required behavior; every private function, method, class, module, or constant is the agent's own design choice and is not listed, described, or restricted; tests aim at public names.

- Public: a name that callers or tests use. Each has one entry with Path, Name, Type, Input, Output, Description (references/04-prompt-contract.md has the format).
- The Description is the implementation requirement for that name. It states observable behavior: what it does, results for valid input, error cases, edge cases. It does not prescribe internal structure or helper decomposition. If the brief demands an exact structure, the Description states it and gives the reason.
- Private: everything else. Not listed, not described, not named, not counted. You design it as part of the system. No rule in this skill limits how many private items exist, where they live, or what they are called, beyond the conventions of the stack.
- Path is the file defining the public name, or N/A when no single file defines it (allowed for any Type). The private layout is free.
- Tests aim at public names. Tests may exercise private code directly; check_interface_coverage then prints a WARN (`test imports NAME, which is not in Expected Interface`, or `test imports private name NAME`), never an ERROR. The Expected Interface is the specification.
- Every importable public name needs at least one test that imports it (WARN when missing). Entries of Type endpoint or command are not importable and never produce this WARN.
- If a test keeps needing a private name, the missing piece is often a public entry point or a better public Output. Consider adding that.

## Type values
Use exactly one of these in the Type field.
- public function: a top-level callable imported by callers.
- public method: a method on a public class, named Class.method.
- public class: a class callers construct or subclass.
- public type: a type alias, interface, enum, schema, or record shape callers rely on.
- public constant: a named value callers read, such as a limit, default, or version string.
- endpoint: a network route; Input and Output describe the request and response shape.
- command: a command-line entry point; Input and Output describe arguments, stdin, stdout, and exit status.

## Contract first
Define the public surface inside the first slice that uses it, not as a standalone slice. A slice with no behavior cannot be demoed and drifts from real use. Write the entry, write the check that imports it, then build behind it. Later slices extend the entry through addition.

## Error semantics
Choose one error model per public surface and use it everywhere on that surface. Examples: all functions raise typed exceptions; all endpoints return a status code with an error body of the same shape; all commands exit non-zero with a message on stderr. Mixed styles (some None returns, some exceptions, some codes) force callers to guess. State the model once in the Description of each affected entry, with the exact error cases.

## Validate at boundaries
Check input where it enters the system: at a public function, endpoint, or command. Reject bad input there with the surface's error model. Code behind the boundary can trust validated values. Do not scatter defensive checks through internal code, and do not skip the check at the boundary because callers "will not" send bad data.

## Addition over modification
Extend a public surface by adding: a new optional parameter with a default, a new field in a response, a new function. Avoid changing the meaning of an existing name, removing a field, or tightening accepted input. When a change must break callers, use expand-contract: add the new form, migrate callers in batches, remove the old form last. Keep one version of each public name live at a time.

## Hyrum's Law
With enough callers, every observable behavior becomes depended upon, whether or not you documented it: output ordering, error message text, timing, extra fields. Consequences:
- Decide on purpose what is observable. Say in the Description what is guaranteed, and say what is not (for example "order is unspecified").
- Keep incidental details out of Output: do not return internal ids, stack traces, or debug fields that callers may start to use.
- Treat any observable change as a possible break and check callers before shipping it.

## Endpoints and commands
Describe both as protocol shape, not as code.
- Endpoint entry: Path names the file that defines the route handler (or N/A when the framework generates it). Name is the route label, such as the method POST plus the route orders. Input lists the body fields, their types, and which are required. Output lists the success status and body, then each error status with its body. Description covers validation rules, idempotency, and edge cases.
- Command entry: Name is the command as typed. Input lists arguments, flags, and stdin. Output lists stdout content, stderr content, and exit codes. Description covers each error case with its exit code.
- Both follow the error model chosen for the surface.
