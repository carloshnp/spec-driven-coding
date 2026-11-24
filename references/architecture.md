# Architecture Baseline Guide

Load this reference in Step 1 **only when the project has no established architecture yet** (a greenfield project or a new standalone subsystem). If an architecture already exists in the repository, follow it instead.

## Choosing the Architecture Style

Pick the **simplest architecture pattern** that keeps boundaries clean and matches the actual problem—never default to heavy enterprise layering for a small or early-stage codebase.

| Pattern | Best Fit | Avoid When |
|---|---|---|
| **Cohesive Modules (Library / CLI)** | Utilities, libraries, CLIs, focused tools where functions group cleanly by domain concept | The system has complex I/O boundaries mixed tightly into business rules |
| **Functional Core, Imperative Shell** | Domain logic, parsers, pricing/scheduling engines, simulations, state transitions; pure functions at the core, thin I/O shell at edges | Pure CRUD with almost no domain logic |
| **Vertical Slice (Feature-Sliced)** | Web APIs, backend services, multi-feature apps where each feature (route/handler/query) evolves independently | Tiny single-purpose scripts or shared algorithmic engines |
| **Pipeline (Staged Transforms)** | ETL, ingestion, compilers, document/media/data processing with clear typed stages (`A -> B -> C`) | Interactive request-response apps with shared mutable state |
| **Simple Layered (Interface -> Service -> Store)** | Services where multiple entry points (API, CLI, jobs) share the same domain operations and persistence model | Features are completely independent (vertical slices are simpler) |
| **Hexagonal (Ports & Adapters)** | Systems that genuinely require swappable external adapters *now* (e.g., multiple databases or transports in v1) | "Maybe we'll swap databases someday" — premature abstraction |

## What to Define in the Architecture Baseline

Keep the entire baseline concise (roughly 15–25 lines):

1. **Style & Rationale:** Name the chosen pattern and give 1–2 sentences explaining why it fits *this* project's real constraints (and why heavier patterns were skipped).
2. **Dependency Direction Rule:** One clear rule preventing circular spaghetti (e.g., `cli/ -> core/`, never `core/ -> cli/`; or `shell -> core`, `core` stays pure).
3. **Stack:** Explicitly name the language/runtime version, **frameworks and core libraries** (e.g., React, TanStack Query/Router, FastAPI, Pydantic, SQLite/ORM), test runner, and typecheck/build tools—each with a brief reason why it was chosen. Do not pull in unlisted frameworks or major libraries mid-milestone without user approval.
4. **Folder Structure:** A minimal directory tree showing where public modules, private helpers (if separate), and tests live. Create folders only when a milestone actually puts files in them.
5. **Core Data Shapes:** Only the 1–4 primary records/types/schemas that anchor the system (field names + types). Defer secondary entities to the milestone that introduces them.
6. **Key Boundary:** How external callers enter the system (imported library functions, HTTP endpoints, or CLI commands) and one consistent error convention for that boundary (e.g., typed exceptions, explicit result objects, or structured HTTP error responses).

## Anti-Bloat Architecture Rules

- **Deep modules over shallow wrappers:** Prefer a small number of cohesive modules with meaningful public functions over dozens of thin pass-through files (`Controller -> Facade -> Manager -> Service -> Repository`).
- **No empty scaffolding:** Do not create empty placeholder directories, abstract base classes, or plugin registries for future milestones.
- **Reversible by default:** Favor plain data structures, standard library primitives, and local storage (SQLite/files) unless the user asked for heavier infrastructure.
- **Let Milestone 1 prove the shape:** Milestone 1 cuts a thin end-to-end tracer bullet through the chosen architecture so the user sees the real structure working before Milestone 2 builds on it.
