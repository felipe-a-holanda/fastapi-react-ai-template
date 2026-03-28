# 🤖 fastapi-react-ai-template

> A [Copier](https://copier.readthedocs.io/) template for full-stack monorepos **designed to be built by AI agents** — not just humans.

Every architectural decision in this template was made to minimize ambiguity, maximize context visibility, and give AI agents (Claude, Cursor, Gemini, GPT-4, etc.) the clearest possible signal for generating correct, consistent code.

---

## ✨ What You Get

After scaffolding, you'll have a production-ready monorepo with:

- **Backend** — FastAPI + SQLAlchemy 2.0 (async) + Alembic + Pydantic v2
- **Frontend** — Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **Contracts** — OpenAPI spec as the single source of truth
- **Type-safe API client** — auto-generated from OpenAPI, zero manual wrappers
- **Data layer** — TanStack Query + React Hook Form + Zod
- **Infra** — Docker Compose for local PostgreSQL
- **DX tools** — Justfile, Ruff, pre-commit, Vitest, pytest
- **Agent docs** — `AGENTS.md`, `ARCHITECTURE.md`, `CLAUDE.md` baked in from day one

See [`WHY.md`](./WHY.md) for the reasoning behind every choice.

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| [Copier](https://copier.readthedocs.io/) | ≥ 9.x | `pip install copier` |
| [pnpm](https://pnpm.io/) | ≥ 9.x | `npm i -g pnpm` |
| [just](https://just.systems/) | ≥ 1.x | `cargo install just` or `brew install just` |
| [Docker](https://www.docker.com/) | ≥ 24.x | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Python | ≥ 3.12 | [python.org](https://www.python.org/downloads/) |
| Node.js | ≥ 20.x | [nodejs.org](https://nodejs.org/) |

### Scaffold a New Project

```bash
copier copy gh:your-github-username/fastapi-react-ai-template ./my-project
```

Copier will ask you a few questions:

```
Project name: My SaaS App
Project slug [my-saas-app]:
Database name [my-saas-app]:
Python version [3.12]:
Node.js version [20]:
Author name: Jane Doe
Author email: jane@example.com
```

### Bootstrap the Project

```bash
cd my-project

# Install dependencies
pnpm install
cd apps/backend && pip install -e ".[dev]" && cd ../..

# Start the database
docker compose up -d db

# Apply migrations
just db-upgrade

# Start everything
just dev
```

Open [http://localhost:3000](http://localhost:3000) — you'll see a working CRUD app (the `items` reference feature).

---

## 📁 Generated Project Structure

```
my-project/
├── apps/
│   ├── backend/              # FastAPI application
│   │   ├── app/
│   │   │   ├── api/          # Routers (HTTP layer)
│   │   │   ├── services/     # Business logic
│   │   │   ├── repositories/ # Data access
│   │   │   ├── models/       # SQLAlchemy models
│   │   │   ├── schemas/      # Pydantic schemas
│   │   │   └── main.py
│   │   └── tests/
│   └── frontend/             # Next.js application
│       └── src/
│           ├── app/          # Next.js pages & layouts
│           ├── features/     # Feature modules (e.g. items/)
│           ├── components/ui # shadcn/ui primitives
│           └── lib/          # Shared utilities
├── packages/
│   ├── contracts/            # openapi.yaml (source of truth)
│   └── client/               # Generated TypeScript types
├── AGENTS.md                 # Rules for AI agents
├── ARCHITECTURE.md           # System map
├── CLAUDE.md                 # Claude Code context
├── justfile                  # Task runner
└── docker-compose.yml
```

---

## ⚡ Key Commands

All commands run from the project root via `just`:

```bash
just dev              # Start DB + backend (port 8000) + frontend (port 3000)
just test             # Run backend (pytest) + frontend (Vitest) tests
just lint             # Lint everything (Ruff + ESLint)
just format           # Auto-format everything
just generate-client  # Regenerate TypeScript types from openapi.yaml
just db-migrate "msg" # Create an Alembic migration
just db-upgrade       # Apply pending migrations
just db-downgrade     # Roll back one migration
just reset            # Wipe DB and reapply all migrations
```

---

## 🧱 Adding a New Feature

The template ships with a reference `items` CRUD feature. **Every new feature follows the exact same pattern.** This is by design — agents learn by imitation.

See `AGENTS.md` in the generated project for the full checklist. The short version:

1. Define the contract in `packages/contracts/openapi.yaml`
2. Run `just generate-client`
3. Create backend files (`model → schema → repository → service → router`)
4. Create migration (`just db-migrate "add <feature> table"`)
5. Create frontend files (`api.ts → schema.ts → List.tsx → Form.tsx`)
6. Write tests

---

## 🔄 Updating the Template

One of the key advantages of Copier over alternatives: **templates can be updated**. If this template releases a fix or new feature:

```bash
copier update
```

Copier will apply the diff to your project and let you resolve conflicts. Your project evolves *with* the template.

---

## 🤖 Why This Template Exists

Most project templates optimize for human ergonomics — flexibility, escape hatches, and customizability. This template optimizes for **AI agent ergonomics**: strict conventions, explicit contracts, and deterministic patterns that agents can replicate reliably.

Read [`WHY.md`](./WHY.md) for the full design rationale, including a table comparing every stack choice and why the alternatives were rejected.

---

## 📋 Template Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `project_name` | `str` | — | Human-readable name (e.g. `My SaaS App`) |
| `project_slug` | `str` | auto | kebab-case slug (e.g. `my-saas-app`) |
| `db_name` | `str` | `project_slug` | PostgreSQL database name |
| `python_version` | `str` | `3.12` | Python version |
| `node_version` | `str` | `20` | Node.js version |
| `author_name` | `str` | — | Author full name |
| `author_email` | `str` | — | Author email address |

---

## 🤝 Contributing

1. Fork this repo
2. Make changes inside `template/`
3. Test with: `copier copy . /tmp/test-project`
4. Submit a PR

When editing Copier template files, remember to escape literal `{{ }}` braces with `{% raw %}...{% endraw %}` blocks. See [`SPEC.md`](./SPEC.md) for the full template spec and Jinja2 escaping notes.

---

## 📄 License

MIT
