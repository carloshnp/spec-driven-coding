# Web UI builds under the gates

Read this when the deliverable is a browser app: an SPA, a dashboard, or a clone of an existing product's interface. It adds the specifics the generic gates leave open; the gates, criteria rules, and approval rules are unchanged.

## Contents

- Sizing a clone request
- Round 1 questions for a UI
- Red-first evidence for a UI suite
- A DOM contract that survives restyling
- jsdom gaps and the fixes
- Storage ports and recovery notices
- Toolchain pairing

## Sizing a clone request

A request worded "a clone of <product>" is at least Large: appearance and behavior are two units, and every view, action, and empty state is its own criterion. Something small is only possible after the cut is named, so size it after round 1, not before.

Split the request into the three axes the user is really choosing between: how faithful the appearance is, where the data comes from, and how the result is delivered. Each is a separate requirement row.

## Round 1 questions for a UI

Ask these three, in this order, each with a recommendation:

1. Appearance: pixel-faithful, same layout and behavior with an own visual identity, or wireframe only. Recommend the middle option; a pixel-faithful target is a moving one and costs review time on spacing rather than behavior.
2. Data: seeded deterministic demo data, a real account, or an importer. Recommend seeded data and state why (no credentials, no OAuth consent, no network failure path hiding the client work).
3. Delivery: local dev server plus a production build, a served static bundle, or an installable PWA. Recommend local plus build unless the user asks to share it.

Route the technical forks (store, state, test stack) to the decision oracle before asking the user; those are not the user's preferences. Then ask only the axes above.

## Red-first evidence for a UI suite

Scaffold the project, install the toolchain, then write the whole suite against the public names before any implementation. Run it once and keep the runner's own line plus exit status.

- A run that fails to resolve the spec's modules reports `Test Files N failed (N)` and `Tests no tests`, exit 1. That is a valid red record for a new feature: the public names do not exist yet. Quote it as the gate-1 evidence, and note that zero tests collected is expected at this point.
- Do not confuse that with the gate-4 failure mode, where a filtered run collects nothing because of a bad selector. There the zero count is a defect.
- Keep test files resolving `../src/...` directly; a path alias that exists only in the build config makes the suite unresolvable before the code exists.

## A DOM contract that survives restyling

Name the semantics in the spec's Expected Interface description, then query by role and accessible name in tests. Restyling must not break the suite; markup rewrites should.

| Surface | Contract |
|---|---|
| Sidebar | `<nav aria-label="Mailbox">` |
| List | `<ul aria-label="Conversations">`, each row `role="option"`, `aria-selected` for selection |
| Reading pane | `<section role="region" aria-label="Conversation">`, one `<article>` per item |
| Compose | `<form aria-label="Compose">`, labelled `To`, `Subject`, body as `role="textbox"` |
| Errors | `role="alert"` inside the surface that failed |
| Notices | `role="status"` for non-blocking recovery messages |

Use a `data-*` attribute only for identity the test must follow (an item id), never for styling hooks a test depends on. Assert visible text for behavior and the id attribute for ordering.

Scope assertion helpers: `within(screen.getByRole("list", { name: new RegExp("conversations", "i") }))` and `within(row)`. Unscoped `getByText` collides as soon as one string appears in two panes.

## jsdom gaps and the fixes

- `document.execCommand` does not exist. Implement inline formatting by wrapping the selected `Range` in the allowed elements, and guard the no-selection case. This also keeps the formatting testable.
- `window.prompt` throws "not implemented". Have the caller read it, and stub it in the test (`window.prompt = () => "https://example.com"`), or use an inline input instead.
- Typing into a `contenteditable` is unreliable. Set `innerHTML`, then assert on what the send path stores.
- Clear `localStorage` and any document-level attribute (a `data-theme`) in an `afterEach`, or the second render in a file inherits the first one's persisted state.
- jsdom has no layout: `toBeVisible` on geometry is meaningless. Prove three-pane geometry, contrast, and theme change with a screenshot, and name the AC in its caption.

## Storage ports and recovery notices

A criterion that says "fall back to seed data and show a notice" cannot be built on a `load(): state | null` port: null conflates "nothing stored" with "stored data rejected". Return a discriminated result instead (`{status: "ok" | "empty" | "corrupt"}`), so the bootstrap layer can tell a first visit from a recovered failure and the notice is testable without stubbing an exception.

Generalize the rule: when a requirement distinguishes causes of failure, the boundary's return type must carry the cause. Otherwise the distinction is smuggled through a nullable field or a thrown error the caller cannot type-check.

## Toolchain pairing

- Match peer majors before installing: a Vite plugin declares the Vite major it supports, so install the pair the registry resolves rather than pinning one side and adding `--force`.
- A `test` block in `vite.config.ts` is typed only by `defineConfig` from `vitest/config`; importing it from `vite` leaves the block outside the type.
- Package managers that block postinstall scripts warn but may still leave the native binary installed by the platform-specific package. Check the tool runs (`npx vite --version`) before chasing the warning; allow the script only if the run fails.
- Install the browser-driven test layer last, and only when a criterion needs it. A download of browser binaries is a cost the user did not ask for; the screenshots the session browser already produces usually cover the visual criteria.
