---
name: spec-driven-coding
description: >-
  Milestone-driven, public-contract coding workflow using vertical TDD.
  Use for greenfield projects or multi-file features that need an architecture
  baseline (style, folder structure, data shapes, boundaries), explicit public
  function contracts (mnemonic name, file path, inputs, outputs), incremental
  milestone demos, and purposeful tests without speculative bloat. Skip for
  one-line fixes, typos, pure Q&A, or single-file tweaks.
license: MIT
compatibility: Agent-agnostic (Antigravity, Hermes, Claude Code, Codex, Cursor, or any coding agent).
metadata:
  version: 1.0.0
---

# Spec-Driven Coding

Build software step by step in small, demoable milestones. Define the architecture once (only if missing), contract only the public functions for the **current** milestone, implement them with vertical TDD while keeping private helpers free, and stop after each milestone so the user can run it and steer what comes next.

## When to Use — and When to Skip

- **Use:** Greenfield projects, new modules/services, or multi-file features where clear structure, public interfaces, and incremental steering matter.
- **Skip:** One-line bug fixes, renames, typos, formatting, or read-only explanations. For a simple bug fix, write one failing test reproducing the bug, fix it minimally, and verify.

## Operating Rules

1. **Inspect before proposing.** Read existing repository files, build/test commands, and conventions first. Never ask the user facts the codebase already answers.
2. **Clarify only what blocks Milestone 1.** If the request is ambiguous, ask at most 3 concrete questions, each with a recommended default. Never silently invent major product decisions.
3. **Contract the public boundary, free the internals.** Define public functions (mnemonic name, target file path, inputs, outputs/errors, behavior) before coding. Private functions, helpers, and internal decomposition stay out of the contract and belong to implementation.
4. **Milestone-by-milestone, never full upfront detail.** Map the whole journey as 3–5 one-line milestones, but write detailed public function contracts **only for the active milestone**.
5. **Strict YAGNI + Deferred Ideas valve.** Build only what the current milestone requires. Never add speculative abstractions, extra config flags, unused layers, logging frameworks, or unasked edge-case machinery. When you spot a useful edge case or future improvement, **do not code it**—record a 1-line note under `Deferred / Ideas` for the milestone review.
6. **Verify with real commands.** Never claim done from memory. Run the actual test/typecheck/build/demo commands without pipes that mask exit codes, and report the real output. Never commit or push unless the user asks.

## The Rolling Milestone Loop

### Step 1: Architecture Baseline & Milestone Roadmap

Check whether the project already has an established architecture and stack.

- **Existing project:** Summarize the existing stack (language, frameworks, key libraries, test runner), folder layout, and conventions in 2–4 lines and follow them. Do not redesign working structure or install competing frameworks unless asked.
- **No architecture yet (greenfield or new standalone subsystem):** Read [references/architecture.md](./references/architecture.md) and define:
  1. **Architecture style / pattern** that fits best, with a 1–2 sentence rationale and dependency direction rule.
  2. **Stack** — language/runtime, **frameworks and core libraries** (e.g., React, TanStack Router/Query, FastAPI, Pydantic, Drizzle), test runner, and build/typecheck tools. Do not install unlisted frameworks or major libraries later without asking.
  3. **Folder structure** (exact directories and what belongs in each).
  4. **Core data shapes** (primary types/entities needed now).
  5. **Key boundary** (how callers enter: library exports, API routes, CLI commands, or top-level feature hooks/components).

Then propose:
- **Goal** (2–3 sentences).
- **Non-Goals** (what is explicitly *not* being built yet).
- **Milestones** (3–5 short bullets: title + 1-line demoable outcome; Milestone 1 must be the thinnest end-to-end tracer bullet).

For multi-milestone or multi-session work, save this in `PLAN.md` at the project root using [references/plan-template.md](./references/plan-template.md). For small single-milestone work, present it directly in your reply.

### Step 2: Public Functions Contract (Active Milestone Only)

In the same proposal (for Milestone 1) or at the start of Milestone `k`, define **only the public entry points** introduced or changed in the active milestone—exported functions, API routes (e.g., FastAPI endpoints), CLI commands, or top-level feature hooks/components (typically **1–4 cohesive public entries**):

- **Mnemonic name & status** — clear, intention-revealing name matching stack conventions; in existing repos, tag each entry `[new]` or `[modified]` so signature changes are obvious.
- **File path** — exact module where it will live, so the architecture is visible upfront.
- **Inputs** — parameter/prop/request names and types/shapes.
- **Output & errors** — return type/response shape and explicit failure behavior.
- **Behavior** — 1–2 sentences of observable behavior (*what*, not *how*).

Add a 1-line **Milestone Demo** describing how the user will see it work.

**STOP and wait for user approval** before writing code for the milestone. The user can cut extras, rename functions, or adjust paths while changes cost zero lines of code.

### Step 3: Build with Vertical TDD

Read [references/testing.md](./references/testing.md) before writing tests. Implement the active milestone one behavior at a time:

1. Pick one public function and one concrete behavior from the active milestone.
2. Write **one** failing test calling the **public function** (never private internals).
3. Run the targeted test and verify it fails for the expected reason.
4. Write the **minimum code** (plus any clean private helpers needed) to make the test pass.
5. Refactor while green so the code stays plain, readable, and minimal.
6. Repeat for the remaining purposeful behaviors of the milestone (typically **2–4 focused tests per public function**).

Keep the project runnable and earlier milestone tests passing at every step. If a milestone requires updating or removing earlier behavior, cleanly update or delete the obsolete tests in the same edit and note why in the report.

### Step 4: Milestone Demo & Steering Gate

When the active milestone's tests pass, run the relevant test suite (and build/typecheck if configured) plus the milestone demo command. Then **STOP** and report:

1. **Demo & verification:** Exact command(s) run and quoted summary output (including test count and exit status).
2. **Blast radius:** Exact files created/modified (e.g. `git diff --stat`) so the user immediately sees footprint.
3. **Tests added & purpose:** One short line per test/group explaining what real regression it catches.
4. **Deferred / Ideas:** Edge cases or enhancements intentionally *not* built.
5. **Next step:** Ask whether to refine anything in Milestone `k` or move on to define the public contract for Milestone `k+1`.

Never start the next milestone until the user reviews the current one and confirms direction.

## Anti-Rationalization Guardrails

| Temptation | Rule |
|---|---|
| "I'll define all milestones' public functions now to be thorough." | Future signatures drift once Milestone 1 runs. Contract only the active milestone. |
| "I'll add an interface/adapter layer in case we swap backends later." | Speculative indirection hardens the codebase. Keep it direct until a second implementation exists. |
| "I'll write all tests for the milestone first, then implement." | Horizontal test batches lock in imagined details. Use vertical TDD: one test, minimal code, repeat. |
| "I'll make this helper public so I can unit-test it directly." | Inflates the public surface and couples tests to internals. Keep helpers private and test via the public function. |
| "I'll also add caching / retries / i18n / extra config just to be safe." | Unrequested scope bloat. Log it as a 1-line bullet in `Deferred / Ideas` instead. |
| "I'll add tests for every getter, constant, and trivial error case." | High maintenance, low signal. Keep tests few, behavioral, and tied to real caller risk. |

## Reference Files (Load Only When Needed)

- [references/architecture.md](./references/architecture.md) — Load in Step 1 **only** when the project has no architecture yet (choosing the simplest fitting pattern, folder layout, data shapes, and boundaries).
- [references/testing.md](./references/testing.md) — Load in Step 3 for vertical TDD rules, keeping the public surface small, real dependencies over internal mocks, and clean test updates.
- [references/plan-template.md](./references/plan-template.md) — Load when creating or updating `PLAN.md` for multi-milestone or multi-session work.
