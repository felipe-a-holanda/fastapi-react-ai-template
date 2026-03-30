# CLAUDE.md — Agent Operating Protocol (FORGE)

You are operating under the FORGE protocol in an AI-agent-optimized full-stack monorepo.
Follow this file exactly. Do not improvise beyond what it allows.

---

## Bootstrap (every new session)

Execute in this order before doing anything else:

1. Read this file completely
2. Read `AGENTS.md` (root-level architecture rules + feature-addition checklist)
3. Read `forge/global/constraints.md`
4. Read `forge/global/verification.md`
5. Find the active change:
   - Look in `forge/changes/` for any `state.json` where `phase` is not `"DONE"`
6. If an active change exists:
   - Read `state.json` → know your current phase and task
   - Read `spec.md` → know what you're building
   - Read `tasks.md` → know what to do next
   - Read `decisions.md` → know what was already decided
7. If no active change exists:
   - Wait for human instructions
   - If instructed to start a new feature, create a change directory under `forge/changes/`

---

## Key Commands

```bash
just dev                          # Start database + backend + frontend
just test                         # Run all tests (backend + frontend)
just lint                         # Lint all code (Ruff + Next.js)
just format                       # Format all code
just generate-client              # Regenerate TypeScript types from OpenAPI
just db-migrate "message"         # Create a new Alembic migration
just db-upgrade                   # Apply pending migrations
just seed                         # Seed database with admin user + sample data
just reset                        # Reset database and reapply migrations
```

---

## Behavioral Rules

- Work on **ONE task** at a time
- **Never** modify `spec.md` during EXECUTE phase
- **Never** implement anything not listed in `tasks.md`
- **Never** expand scope beyond what `spec.md` defines
- **Always** follow the `items` reference feature pattern when adding new features
- **Always** follow the AGENTS.md feature-addition checklist (contract → generate → backend → migration → frontend → tests)
- If you need to touch a file not listed in the task's `touches` field, log it in `decisions.md` first
- Record every non-trivial decision in `decisions.md` (append-only, never edit past entries)
- Every task must pass verification before being marked `[x]`
- Commit after each completed task with message format: `forge({change-id}): task-NN — {brief description}`
- If you discover the spec is wrong or incomplete, **stop execution**, log in `decisions.md`, set `state.json` phase to `"PLAN"`

### Backend-Specific Rules
- Routers NEVER touch the database or import SQLAlchemy
- Services NEVER import FastAPI (except HTTPException)
- Repositories NEVER contain business logic or raise HTTP exceptions
- Use structlog: `logger.info("event_name", key=value)` — never f-strings in logs
- All user-scoped data filtered by `owner_id` at repository level

### Frontend-Specific Rules
- No `fetch()` in components — use TanStack Query hooks in `features/*/api.ts`
- No ad-hoc types — use generated types from OpenAPI client
- Zustand for UI state only, never for server data
- Components in `components/ui/` never import from `features/` or `lib/api-client.ts`

---

## PLAN Phase

When creating a new change:

1. Read global docs (architecture.md, constraints.md, verification.md)
2. Read `AGENTS.md` for the feature-addition checklist
3. Analyze the human's request
4. Create `forge/changes/{change-id}/` with:
   - `spec.md` — full spec (Goal, Non-Goals, Requirements, Constraints, Edge Cases, I/O, Open Questions)
   - `tasks.md` — ordered atomic tasks, each with status/touches/depends/verify/notes
   - `decisions.md` — empty (with header)
   - `state.json` — `{ "phase": "PLAN", "change_id": "{change-id}" }`
5. Ensure tasks follow the AGENTS.md checklist order:
   - Contract (openapi.yaml) → Generate client → Backend (model → schema → repo → service → router → deps.py) → Migration → Frontend (hooks → schema → components) → Tests
6. Run the adversarial checklist against your own spec (see below)
7. Verify every requirement has at least one task covering it
8. Present to human for review

### Adversarial Checklist (mandatory before finalizing PLAN)

Answer each one. "N/A" is valid. Skipping is not.

1. Is any requirement ambiguous enough to allow two different implementations?
2. Does any requirement contradict a global constraint or AGENTS.md rules?
3. Are there implicit requirements not captured?
4. What is the worst-case failure if implemented incorrectly?
5. Are there undeclared external dependencies?
6. Can every requirement be verified with an automated test (pytest or Vitest)?
7. Is task ordering correct? Any hidden dependencies?
8. Are there shared resources (DB tables, openapi.yaml, config, env vars) multiple tasks touch?
9. If partially implemented, is the system still safe?
10. Does this introduce a security surface needing explicit handling?
11. Does this feature require OpenAPI contract changes? If so, is the contract task first?
12. Does this follow the `items` reference pattern? If not, why?

---

## EXECUTE Phase

For each task:

1. Read `state.json` → identify `current_task`
2. Read the task block in `tasks.md` → know what to implement and what files to touch
3. Set task status to `[~]` (in progress)
4. Implement the task (following AGENTS.md rules and `items` reference pattern)
5. Run the task's specific `verify` command
6. Run the full verification suite (see below)
7. If all passes:
   - Mark task `[x]` in `tasks.md`
   - Fill in the `notes` field with what was done
   - Log any decisions in `decisions.md`
   - `git add -A && git commit -m "forge({change-id}): task-NN — {description}"`
   - Update `state.json`: advance `current_task`, reset `iteration` to 0
8. If verification fails:
   - Increment `iteration` in `state.json`
   - Attempt fix
   - If `iteration` exceeds `max_verification_retries`:
     - Mark task `[!]` with detailed explanation
     - Log full failure context in `decisions.md`
     - Advance to next non-dependent task

---

## Verification Protocol

After every task, run in this order:

```bash
# 1. Task-specific verification (from tasks.md verify field)
{task.verify}

# 2. Full suite
just lint                # Ruff (backend) + Next.js lint (frontend), must exit 0
just test                # pytest (backend) + Vitest (frontend), must exit 0
```

Thresholds are defined in `forge/global/verification.md`.

If the full suite fails on something **unrelated** to the current task:
- Log in `decisions.md` as a known issue
- Do NOT block the current task

If the full suite fails on something **related** to the current task:
- Fix it (counts as a retry)

---

## Commit Convention

```
forge({change-id}): task-NN — {brief description of what was done}
```

Examples:
```
forge(add-notifications): task-01 — add notification paths and schemas to openapi.yaml
forge(add-notifications): task-02 — create Notification model and Alembic migration
forge(add-notifications): task-03 — implement notification repository and service
```

---

## When Things Go Wrong

| Situation | Action |
|-----------|--------|
| Task fails verification 3 times | Mark `[!]`, log context, advance |
| Task causes regression in unrelated area | Create corrective task at end of tasks.md, log in decisions.md |
| Spec is wrong or incomplete | Stop, log, set phase to PLAN, wait for human |
| Need to touch undeclared file | Log in decisions.md first, then proceed |
| Need to reorder tasks | Log in decisions.md, update tasks.md |
| Need to add a new task | Append to tasks.md, log in decisions.md |
| OpenAPI contract drift | Run `just generate-client`, create corrective task if types changed |
| Session interrupted mid-task | Next session reads state.json, finds `[~]`, resumes |
