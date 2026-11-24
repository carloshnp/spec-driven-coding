# spec-driven-coding

An agent-agnostic skill for milestone-driven, public-contract software development using vertical TDD.

Instead of planning an entire codebase upfront or letting an agent silently add speculative features and brittle tests, `spec-driven-coding` keeps work small, transparent, and human-steered:

1. **Architecture Baseline & Milestone Roadmap** — Follows existing repo conventions, or defines the simplest fitting architecture style/pattern, explicit stack (frameworks & core libraries), folder layout, core data shapes, and key boundaries when starting fresh. Maps 3–5 one-line milestones and explicit non-goals.
2. **Active-Milestone Public Contract** — Defines only the **current** milestone's public entry points (exported functions, API routes, CLI commands, or top-level feature hooks/components) with mnemonic names, exact file paths, inputs, outputs/errors, and observable behavior. Private helpers stay out of the contract. Stops for approval before writing code.
3. **Vertical TDD Build** — Implements one public entry point and one behavior at a time (Red → Green → Refactor), targeting public contracts only, with a purposeful test budget and strict YAGNI (`Deferred / Ideas` parking lot for anything unasked).
4. **Milestone Demo & Steering Gate** — Stops after each milestone with real command output, `git diff --stat`, a 1-line justification per test added, and deferred ideas—so you can run the result and steer the next milestone.

## Repository Layout

```text
spec-driven-coding/
├── SKILL.md                      # Main skill entrypoint (109 lines)
├── references/
│   ├── architecture.md           # Simplest-fit architecture baseline guide (greenfield only)
│   ├── testing.md                # Vertical TDD on public contracts, anti-bloat test rules
│   └── plan-template.md          # Compact living PLAN.md template for multi-milestone work
├── LICENSE                       # MIT
└── README.md
```

## Install

### Antigravity

Global (all workspaces):

```bash
git clone https://github.com/carloshnp/spec-driven-coding
rsync -a --exclude .git --exclude README.md --exclude LICENSE spec-driven-coding/ ~/.gemini/config/skills/spec-driven-coding/
```

Or project-local inside `.agents/skills/spec-driven-coding/`.

### Hermes

```bash
git clone https://github.com/carloshnp/spec-driven-coding
rsync -a --exclude .git --exclude README.md spec-driven-coding/ ~/.hermes/skills/software-development/spec-driven-coding/
```

### Other Agents (Claude Code, Codex, Cursor, etc.)

Install via `skills` CLI or copy `SKILL.md` and `references/` into your agent's skills directory:

```bash
npx skills add carloshnp/spec-driven-coding
```

## When to Use — and When to Skip

- **Use:** Greenfield projects, new modules/services, or multi-file features where clear architecture, explicit public boundaries, and incremental human steering matter.
- **Skip:** One-line bug fixes, renames, typos, formatting, or pure Q&A.

## License

MIT — see [LICENSE](./LICENSE).
