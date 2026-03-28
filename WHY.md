# WHY.md — Design Rationale

> Why every decision in this template was made to optimize for **AI coding agents**, not just human developers.

---

## The Problem

AI agents (Claude, Cursor, Gemini, GPT-4o, etc.) make more mistakes with:

- **Flexible architectures** — too many valid ways to do the same thing → inconsistent output
- **Implicit conventions** — agents must infer patterns instead of reading them
- **Black-box dependencies** — agents can't reason about code they can't see
- **Ambiguous file locations** — agents don't know where to put new code
- **No working reference** — agents invent patterns instead of imitating them

This template eliminates all of those failure modes by choosing **opinionated, explicit, low-ambiguity** tools at every layer.

---

## The Guiding Principle

> **Constrain the solution space. The narrower the valid path, the more reliably agents walk it.**

Every decision below follows this principle. More convention = less hallucination. Less flexibility = fewer agent mistakes. Explicit contracts = zero frontend/backend mismatch.

---

## 🧱 Definitive AI-Agent-Optimized Stack

| System Part | Chosen Option | Why It Was Chosen (Agent-Optimized) | Alternative | Why It Was NOT Chosen |
|---|---|---|---|---|
| **Monorepo Structure** | pnpm workspaces | Minimal abstraction, zero config overhead, easy for agents to understand and modify. Keeps everything in one place → maximizes context visibility. | Turborepo | Adds pipeline complexity early. Great later, but increases cognitive overhead for agents in greenfield stage. |
| **Project Generator** | Copier | Templates are versionable and updatable. Agents can reapply structure consistently across projects. Reduces architectural drift. | Cookiecutter | One-shot generation. No evolution path → agents cannot easily propagate improvements. |
| **Task Runner** | Justfile | Provides a deterministic command interface (`just dev`, `just test`). Agents don't need to remember shell commands. | Makefile | Less readable, inconsistent syntax across systems, harder for LLMs to reliably generate/edit. |
| **Frontend Framework** | Next.js | Highly opinionated: routing, data fetching, SSR handled. Reduces architectural decisions → agents follow conventions instead of inventing. | Vite + React Router | Too flexible. Requires decisions about routing, structure, data fetching → increases chance of inconsistent agent output. |
| **Frontend Language** | TypeScript | Strong typing constrains agent output. Errors become visible immediately. Reduces hallucinated data shapes. | JavaScript | No type constraints → agents can silently introduce inconsistencies. |
| **Styling** | Tailwind CSS | Declarative and composable. Avoids CSS architecture decisions. Agents operate on inline utilities instead of managing stylesheets. | CSS Modules | Requires naming, structure decisions. Higher ambiguity → more agent mistakes. |
| **UI Components** | shadcn/ui | Components live inside the repo. Agents can read and modify them directly. No hidden abstractions. | Material UI | Black-box components. Agents must rely on docs instead of code → more errors and limitations. |
| **Forms** | React Hook Form | Minimal API, high repetition pattern. Agents reliably generate forms using `register` pattern. | Formik | More verbose, more state handling → more room for inconsistency. |
| **Validation** | Zod | Runtime + static validation unified. Agents can infer types and validation rules from one source. | Yup | Less aligned with TypeScript inference → duplication and drift risk. |
| **Data Fetching** | TanStack Query | Declarative server-state management. Eliminates manual loading/error logic. Agents follow consistent patterns. | useEffect + fetch | Imperative, error-prone. Agents frequently misuse lifecycle → bugs. |
| **Backend Framework** | FastAPI | Strong typing, automatic OpenAPI generation, simple mental model. Agents generate endpoints with high accuracy. | Django | Too many abstractions (ORM, admin, settings). Agents struggle with implicit behavior. You lose Django Admin, but gain predictability. |
| **Backend Schemas** | Pydantic v2 | Explicit, typed schemas. Direct mapping to OpenAPI. Agents can extend safely. | Marshmallow | Less common, more verbose → lower training signal for LLMs. |
| **ORM** | SQLAlchemy 2.0 (async) | Standard, widely used, explicit patterns. Agents have strong prior knowledge. | Django ORM | Tightly coupled to Django. Less flexible outside its ecosystem. |
| **Migrations** | Alembic | Declarative, predictable structure (`versions/`). Agents can generate migrations reliably. | Django migrations | Implicit behavior tied to Django models → less explicit control. |
| **Backend Architecture** | API → Service → Repository | Strict separation of concerns. Each file has a single role → reduces ambiguity for agents. | "Flat" structure | Logic scattered across layers → agents don't know where to put code. |
| **Dependency Injection** | FastAPI Depends | Explicit dependency graph. Agents understand flow of object creation. | Manual wiring | Hidden dependencies → harder for agents to reason about. |
| **Contracts (Source of Truth)** | OpenAPI | Single source of truth. Enables client generation. Eliminates guesswork in FE ↔ BE communication. | Zod-only contracts | Easier locally, but duplicates backend logic → drift risk. |
| **API Client** | Generated from OpenAPI | Zero ambiguity. Agents don't invent endpoints or types. | Manual fetch wrappers | Prone to mismatch with backend → frequent agent errors. |
| **Frontend State (Global)** | Zustand (optional) | Minimal API, low boilerplate. Easy for agents to generate and reason about. | Redux | High complexity, boilerplate-heavy → agents often misuse patterns. |
| **Frontend Organization** | Feature-based structure | Groups related code. Agents can find context quickly and extend features consistently. | Layer-based (components/, hooks/) | Scattered logic → harder for agents to navigate. |
| **Backend Config** | Pydantic Settings | Typed config, environment-driven. Agents can safely extend config. | .env ad-hoc usage | No structure → inconsistent usage across codebase. |
| **Linting/Formatting** | Ruff | Single fast tool for lint + format. Enforces consistency automatically. | Flake8 + Black + isort | Multiple tools → more complexity and drift. |
| **Testing (Backend)** | pytest + pytest-asyncio | Simple, popular, consistent patterns. Agents generate tests reliably. | unittest | Verbose, less idiomatic → fewer examples in training data. |
| **Testing (Frontend)** | Vitest + Testing Library | Matches modern React patterns. Agents generate tests close to real usage. | Jest (legacy setups) | More configuration overhead → inconsistent setups. |
| **Infra** | Docker Compose | Declarative environment. Agents can spin up full stack with one command. | Manual setup | Environment drift → agents fail to reproduce setup. |
| **Git Hooks** | pre-commit | Enforces standards automatically. Agents can rely on consistent formatting. | Manual linting | Inconsistent code quality → drift accumulates. |
| **Documentation** | ARCHITECTURE.md | Explicit system map. Agents use it as grounding context. | README-only | Too shallow → lacks structural guidance. |
| **Reference Implementation** | Example feature (CRUD) | Concrete pattern to copy. Agents learn by imitation. | No example | Agents must infer patterns → higher error rate. |
| **Agent Rules** | AGENTS.md (root + per app) | Defines constraints and workflow. Reduces ambiguity in multi-agent environments. | No agent spec | Agents improvise → inconsistent architecture. |

---

## Key Patterns Explained

### Contracts-First Development

```
openapi.yaml  ←── single source of truth
    │
    ├─► FastAPI validates against it (auto-generated docs)
    │
    └─► pnpm generate  ──►  packages/client/src/types.ts
                                    │
                                    └─► Frontend uses generated types only
                                        (never defines them manually)
```

This eliminates the most common agent failure: **frontend and backend types silently diverging**. With a generated client, there's a hard build error when they drift.

### The Layered Backend

```
HTTP Request
    │
    ▼
app/api/<feature>.py        ← Router: only HTTP concerns
    │ (calls)
    ▼
app/services/<feature>.py   ← Service: business logic, raises HTTPException
    │ (calls)
    ▼
app/repositories/<feature>.py ← Repository: only SQLAlchemy queries
    │ (accesses)
    ▼
Database
```

**Why this matters for agents:** Each file has exactly one job. When an agent needs to add a feature, there's no question about where each piece goes. When an agent reads the codebase for context, each layer is completely predictable.

### The `items` Reference Feature

The template ships with a complete CRUD feature for `items`. This isn't just a demo — it's the **canonical pattern** that every new feature should copy.

Agents are better at imitation than invention. By providing one working example of the full stack (model → schema → repository → service → router → TanStack Query hook → form component → list component), agents can replicate the pattern with high fidelity instead of inventing from scratch.

### Feature-Based Frontend Organization

```
src/features/
  items/
    api.ts        ← TanStack Query hooks (all server state)
    schema.ts     ← Zod schemas (form validation)
    ItemList.tsx  ← List view component
    ItemForm.tsx  ← Create/edit form component
```

All code for a feature lives together. Agents don't have to hunt across `components/`, `hooks/`, `services/`, `types/` directories to understand one feature.

---

## What This Template Deliberately Sacrifices

Optimizing for agents means making tradeoffs that would be wrong for a human-first project:

| Sacrifice | In Favor Of |
|-----------|-------------|
| Framework flexibility (Vite + custom router) | Next.js conventions (one way to do routing) |
| Django Admin UI | Predictable, explicit Python patterns |
| Custom CSS architecture | Tailwind utilities (no naming decisions) |
| Gradually typed JS | Full TypeScript from day one |
| Microservices from the start | Monorepo with clear boundaries |
| Docs as afterthought | AGENTS.md, ARCHITECTURE.md baked in |

---

## When This Template Is (and Isn't) Right

### ✅ Choose this template when:
- Your primary "developer" for new features is an AI agent
- You want AI pair-programming to produce consistent, predictable output
- You're building a CRUD-heavy web app or internal tool
- You want to move fast without accumulating architectural debt

### ❌ Don't use this template when:
- You need maximum framework flexibility and custom architecture
- Your team has strong opinions about different stack choices
- You need Django Admin or a built-in CMS
- You're building a non-web project (CLI tool, ML pipeline, etc.)

---

## Further Reading

- [`SPEC.md`](./SPEC.md) — Full template specification and Jinja2 escaping notes
- [`ARCHITECTURE.md`](./template/ARCHITECTURE.md) — System map and data flow (in generated project)
- [`AGENTS.md`](./template/AGENTS.md) — Agent rules and feature-addition checklist (in generated project)
- [`CLAUDE.md`](./template/CLAUDE.md) — Claude Code–specific context (in generated project)
- [Copier documentation](https://copier.readthedocs.io/) — Template engine docs
