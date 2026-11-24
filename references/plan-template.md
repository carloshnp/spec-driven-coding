# Living Plan Template (`PLAN.md`)

Use this template at the project root (`PLAN.md`) when work spans multiple milestones or sessions. Update it in place as milestones complete—do not create separate `SPEC.md`, `STATE.md`, `VERIFY.md`, or per-task markdown files.

For a single-milestone task in one session, present the same sections directly in chat without writing `PLAN.md` unless the user asks for a file.

````markdown
# Plan: <Project or Feature Name>

## Goal
<2–3 sentences: what problem this solves and what the finished system does.>

## Architecture Baseline
<!-- Include this full section ONLY when the project has no architecture yet.
     For an existing repo, replace with a 2–3 line summary of existing stack/conventions. -->
- **Style:** <Pattern name> — <1–2 sentence rationale for why it fits best>
- **Dependency rule:** <e.g., `cli/` and `api/` depend on `core/`; `core/` has no I/O imports>
- **Stack:**
  - Runtime & language: <e.g., Python 3.12 / TypeScript (Node 22)>
  - Frameworks & core libraries: <e.g., FastAPI, Pydantic, React, TanStack Query — only what is actually used>
  - Testing & checks: <e.g., pytest, Vitest, tsc --noEmit>
- **Folder structure:**
  ```text
  src/<pkg>/
    core/      # pure domain logic & data shapes
    ...        # boundary / I/O modules
  tests/       # public-function contract tests
  ```
- **Core data shapes:**
  - `<EntityName>`: `<field: type, ...>`
- **Key boundary & error model:** <Public exports / routes / CLI + consistent error convention>

## Non-Goals (Not Building Yet)
- <Explicitly excluded feature, abstraction, or concern>

## Milestones
- [ ] **M1:** <Thinnest end-to-end tracer bullet — 1-line demoable outcome> *(active)*
- [ ] **M2:** <Next vertical capability — 1-line demoable outcome>
- [ ] **M3:** <Next vertical capability — 1-line demoable outcome>

---

## Active Milestone: M1 — <Title>

### Public Functions Contract
<!-- List ONLY public entry points for THIS milestone (exported functions, API routes,
     CLI commands, or top-level feature hooks/components; typically 1–4).
     In existing repos, tag each entry [new] or [modified].
     Private helpers are implementation details and stay out of this list. -->
1. `[new|modified]` `<mnemonic_name>(<inputs>) -> <output>`
   - **File:** `<relative/path/to/module>`
   - **Behavior:** <1–2 sentences of observable behavior and explicit error cases.>

### Demo Check
- <Concrete command or interaction showing M1 works end-to-end.>

---

## Deferred / Ideas
<!-- Anti-bloat parking lot: edge cases or ideas spotted during coding go here, not into code. -->
- <None yet>

## Decisions
<!-- Optional: 1-line notes only for non-obvious choices made along the way. -->
- <YYYY-MM-DD>: <Decision and short reason>
````

## Resuming Across Sessions

When resuming work from an existing `PLAN.md`:
1. Read `PLAN.md` and run `git status` + the test command to confirm current reality on disk.
2. State in 2–3 lines which milestone is completed, which milestone is active, and wait or proceed according to the user's request.
3. When Milestone `k` is approved and finished, check it off (`[x]`), replace `## Active Milestone` with Milestone `k+1` (keeping the file short), and prune resolved items from `Deferred / Ideas`.
