# Vertical TDD on Public Functions

Load this reference in Step 3 when writing or updating tests.

## Core Loop: Vertical Red-Green-Refactor

Never write the entire test suite for a milestone upfront ("horizontal slicing"). Bulk upfront tests lock in guessed interfaces and produce brittle, bloated suites.

Work **one public function and one behavior at a time**:

1. **Red:** Write **one** failing test that calls a public function from the active milestone contract with concrete inputs and asserts the expected output or error.
2. **Confirm failure:** Run the targeted test and verify it fails for the right reason (missing function, wrong return value, missing validation—not a syntax typo in the test).
3. **Green:** Write the **minimum code** needed to make that test pass. Create private helpers freely as implementation details, but keep them unexported/private.
4. **Refactor:** Clean up duplication or naming while tests remain green. Do not add new unrequested behavior during refactoring.
5. **Repeat:** Move to the next meaningful behavior of that public function, then the next public function in the milestone.

## Keep the Public Surface Small

- **Test public contracts, not private helpers.** Tests import only the public entries listed in the active milestone contract (exported functions, hooks, or public API routes/CLI commands).
- **Focus TDD where logic lives.** Apply vertical TDD to domain logic, API routes, state transitions, and data/query hooks. Verify pure visual layout or styling by running the app instead of writing brittle JSX/DOM snapshot tests.
- **Never export an internal helper just to unit-test it.** If internal logic feels complex, test it through the public function that exercises it. Exporting helpers bloats the API and breaks tests whenever internals are refactored.
- **Keep signatures stable and mnemonic.** Function names and parameters should read clearly from a caller's point of view.

## Test-Purpose Budget (Prevent Test Bloat)

Every test has a maintenance cost and must justify its existence by catching a realistic regression a caller cares about.

- Aim for **2–4 focused tests per public function**:
  - 1–2 tests for the primary happy path(s).
  - 1–2 tests for genuinely meaningful edge cases or error contracts specified in the milestone.
- **Do not write tests for:**
  - Trivial pass-throughs, getters, data-class field assignments, or constant tables.
  - Internal implementation details (call counts of private helpers, internal state shapes).
  - Volatile copy/formatting details unless exact formatting is part of the public contract.
  - Combinatorial matrices of every possible input when the logic does not branch on them.

## Real Dependencies Over Internal Mocks

- **Never mock the project's own internal modules or helpers.** Mocking internal collaborators tests the mocks and cements internal wiring.
- Prefer real local implementations: temporary directories (`tmp_path`), in-memory SQLite, or real local fixtures.
- Fake or stub **only true external boundaries** that cannot run deterministically in tests (network APIs, clocks, external payment/auth services, hardware).

## Readable, Change-Friendly Tests

- **DAMP over DRY:** Each test should show its input, public call, and expected result in one readable block without chasing opaque shared test helpers.
- **Verify real assertions:** Assert exact expected outputs or error types—never weak checks like "does not throw" or "is not None" when a concrete result is expected.
- **Check test counts:** Confirm the runner actually executed >0 tests and exited 0.
- **Make evolution cheap:** When the user changes a requirement, simplifies a design, or removes a feature after a milestone demo, cleanly update or delete the obsolete tests in the same change and mention what changed in the milestone report. Never keep dead tests or artificial test-count floors.
