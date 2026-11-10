# Scope: size the request and choose the gates

Read this when a request arrives and you must decide how much process it needs, or when a spec seems to be growing too large.

## The size gate

The test is one question: does the whole change fit in one context window, with room left to read the code, run the checks, and report? If yes, do not break it into tasks. Write the criteria, run the increment loop, and verify. If no, the change needs slices, and slices need the full gates.

Estimate before you act, not after you are half done. A change that turns out too big in the middle of work costs more than a short estimate up front.

## Sizing proxies

You cannot count tokens in advance. Use signals you can count:

- Criteria bullets. Up to 3 bullets in the draft spec is small. 4 to 8 is medium. More than 8 is large.
- Title words. If the one-line title needs the word "and" to be true, the request holds at least two changes. Treat each as its own unit of work.
- Clone requests. "Make a clone of <app>" is Large however short the sentence: it carries an interface, a behavior set and a data model, and the behavior set is unbounded until you name the cut. Ask which behaviors form v1 before sizing, and write the rest into Out of scope with a reason.
- Public names. A change that adds or alters more than about 5 public names is at least medium.
- Layers touched. Data, logic, interface, and tests all changing at once points to a vertical slice, not one step.
- Sessions. If you expect to stop and resume, treat it as large, because the state must live on disk.

When proxies disagree, take the larger class. A wrong small label skips the checks that catch large mistakes. A wrong large label costs a few minutes.

## Gate applicability

| Class | Typical shape | Gates used |
|---|---|---|
| Trivial | One line or one function, no new behavior to specify | Increment loop only |
| Small | One feature in one or two files, 3 or fewer criteria | 0, short 1 (criteria only), 3, 4 |
| Medium | Several files, 4 to 8 criteria | 0, 1, 2, 3, 4 |
| Large | Many files or sessions, more than 8 criteria, wide rename or migration | 0, 1, 2, 3, 4, review panel at 1 and 2, and state on disk |
| Compile request | The user asks for a PROMPT.md | Add gate 5 to the class above |

A short gate 1 still needs criteria with False if clauses and a validation method for each. It skips frontier rounds only when nothing is ambiguous.

## Examples per class

- Trivial: fix an off-by-one in a loop; change a default timeout from 30 to 60; rename a single private helper. Do the edit, run the existing tests, report.
- Small: add a `--json` flag to one command; reject empty names in one endpoint with a clear error. Write 2 or 3 criteria, implement, prove.
- Medium: add CSV export with a progress message and an error path; add token refresh to a client and its callers. Specify, slice into tasks, run in order.
- Large: replace one storage library across a code base; add a plugin system with a loader, a registry, and a sample plugin. Specify with rounds, review, plan, run in waves.
- Large, clone request: reproduce another product's interface and behavior. Expect fifteen or more criteria, a seeded data model, and a written out-of-scope list before the spec can freeze; the review panel will keep finding behaviors until that list exists.
- Wide rename: many call sites, one behavior. Large by blast radius even if each edit is trivial. See wide changes in references/06-increments.md.

## Record the decision

At the end of gate 0, write two lines: the class, and the reason with the proxy counts. Write them as scope-note.md at the project root, next to STATE.md, specs/ and tasks/. If the user disagrees with the class, the user wins. Re-size when the spec changes shape after gate 1.

## When the gates do not apply

Do not run the gates for work that has no code outcome to prove: an explanation, a reading of a file, a design discussion. Answer the question. Offer the gates only if the discussion turns into a build request.

## Checks before leaving gate 0

- The class is named and the reason is written.
- The list of gates to run is stated.
- A request that mixes two changes has been split, or the user chose to keep it together.
- For a large class, the state file location is chosen (references/09-context-and-resume.md).
