# FORGE — Spec-Driven Development Protocol

## What this is

FORGE is the development protocol for this AI-agent-optimized monorepo.
A human writes a prompt. The system builds a spec, breaks it into tasks, and executes autonomously — with permanent memory, automated verification, and full auditability.

Every decision lives in the repo. Every task is one commit. Every commit is revertable.

This protocol is tailored for a **contracts-first full-stack monorepo** with:
- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Alembic + Pydantic v2 + structlog
- **Frontend**: Next.js + TypeScript + Tailwind + shadcn/ui + TanStack Query + React Hook Form + Zod
- **Contracts**: OpenAPI spec as single source of truth
- **Infra**: PostgreSQL (Docker), pnpm workspaces, Justfile task runner
- **Auth**: JWT in httpOnly cookies, passlib (bcrypt), python-jose

---

## How it works

```
Human prompt
    ↓
  PLAN        Agent drafts spec + tasks (with self-critique)
    ↓
  REVIEW      Human approves, requests changes, or rejects
    ↓
  EXECUTE     Agent implements one task at a time (autonomous loop)
    ↔
  VERIFY      Automated tests, coverage, types, lint after each task
    ↓
  DONE        All tasks complete, final verification passes
```

The human is involved in two moments: providing the initial prompt, and approving the plan. Everything else is autonomous.

---

## Getting Started — Full Workflow

### 1. PLAN: Create a new change

**Manual (recommended for first time):**
```bash
# Create the change directory
mkdir -p forge/changes/add-notifications

# Create the required files
cd forge/changes/add-notifications
touch spec.md tasks.md decisions.md state.json

# Edit spec.md: write Goal, Non-Goals, Requirements, Constraints, Edge Cases, I/O, Open Questions
# Edit tasks.md: break down into atomic tasks with status/touches/depends/verify/notes
# Edit state.json: {"phase": "PLAN", "change_id": "add-notifications"}
# Leave decisions.md empty (header only)
```

**Or ask the agent to create the plan:**
```
"Create a FORGE plan for adding email notifications to items. 
Users should receive an email when someone comments on their item."
```

The agent will create the full `forge/changes/add-notifications/` directory with all files.

### 2. REVIEW: Approve the plan

Read `spec.md` and `tasks.md`. Then either:
- **Approve**: Update `state.json` to `{"phase": "EXECUTE", "change_id": "add-notifications", "current_task": "task-01", ...}`
- **Request changes**: Edit the spec/tasks, keep phase as `"PLAN"`
- **Reject**: Delete the change directory

### 3. EXECUTE: Run the autonomous loop

```bash
# Autonomous execution (runs until done or blocked)
just forge

# Or with options
just forge --max-iterations 5        # Stop after 5 tasks
just forge --change add-notifications # Specify which change (if multiple exist)

# Dry-run (see what would happen without executing)
just forge-status
```

The agent will:
- Read the current task from `tasks.md`
- Implement it
- Run verification (`just lint && just test`)
- Commit with `forge(add-notifications): task-NN — description`
- Advance to the next task
- Repeat until all tasks are done or max iterations reached

### 4. VERIFY: Check progress

```bash
# See current state
cat forge/changes/add-notifications/state.json

# See task progress
grep "status:" forge/changes/add-notifications/tasks.md

# See decisions made
cat forge/changes/add-notifications/decisions.md

# Run verification manually
just lint && just test
```

### 5. DONE: Final verification

When all tasks are `[x]` or `[!]`, the agent sets `state.json` phase to `"DONE"`.

Run final verification:
```bash
just lint && just test && cd apps/frontend && pnpm build
```

If all passes, the change is complete. The `forge/changes/add-notifications/` directory stays in git history as permanent documentation.

---

## Directory Structure

```
/project-root
  CLAUDE.md                              ← agent operating manual (auto-loaded by Claude Code)
  AGENTS.md                              ← architecture rules + feature-addition checklist
  ARCHITECTURE.md                        ← system map + data flow diagrams

  /forge
    FORGE.md                             ← this file (protocol reference)
    forge_run.py                         ← autonomous execution loop

    /global
      architecture.md                    ← system-wide architecture (mirrors ARCHITECTURE.md)
      constraints.md                     ← non-negotiable rules for this stack
      verification.md                    ← test commands, thresholds, quality gates

    /changes
      /{change-id}                       ← e.g. "add-notifications", "fix-payment-flow"
        spec.md                          ← WHAT to build
        tasks.md                         ← HOW to build it (ordered, atomic)
        decisions.md                     ← WHY things are the way they are
        state.json                       ← WHERE we are right now

  /packages
    /contracts/openapi.yaml              ← OpenAPI spec (source of truth for all API contracts)
    /client/                             ← Generated TypeScript types from OpenAPI

  /apps
    /backend/                            ← FastAPI (Python)
      app/api/                           ← Routers (HTTP concerns only)
      app/services/                      ← Business logic
      app/repositories/                  ← Database access (SQLAlchemy)
      app/models/                        ← SQLAlchemy models
      app/schemas/                       ← Pydantic schemas
      tests/                             ← pytest tests
    /frontend/                           ← Next.js (TypeScript)
      src/features/                      ← Feature modules (api.ts, schema.ts, components)
      src/lib/                           ← Shared utilities (api-client, store)
      src/components/ui/                 ← shadcn/ui primitives
      tests/                             ← Vitest tests
```

### Why this structure

- **CLAUDE.md at root**: Claude Code reads it automatically — no prompt injection needed
- **AGENTS.md at root + per-app**: three-level instructions (root → backend → frontend)
- **`/forge/global/`**: slow-changing constraints that apply to everything
- **`/forge/changes/{id}/`**: per-feature memory, lives forever in git history
- **One directory per feature**: supports parallel development, clean git log
- **Contracts-first**: `openapi.yaml` is the single source of truth; types flow one direction

---

## File Contracts

### CLAUDE.md

The agent's single entry point. Read first, followed always. See the template file for the full version.

Key contents:
- Bootstrap protocol (what to read, in what order, every session)
- Behavioral rules (one task at a time, no scope expansion)
- Verification protocol reference
- FORGE directory location
- Key commands (`just test`, `just lint`, `just dev`, etc.)

### spec.md — WHAT to build

Source of truth for requirements. Created during PLAN, frozen during EXECUTE.

Required sections:
- **Goal**: one paragraph, what and for whom
- **Non-Goals**: what this explicitly does NOT do
- **Requirements**: numbered, each must be testable
- **Constraints**: feature-specific (beyond global constraints)
- **Edge Cases**: known edge cases and expected behavior
- **Inputs/Outputs**: API contracts (OpenAPI paths/schemas), Pydantic schemas, UI states (if applicable)
- **Open Questions**: things the human must decide before execution

Rules:
- If spec needs to change during EXECUTE → execution stops, decision is logged, PLAN reopens

### tasks.md — HOW to build it

Source of truth for execution plan. Each task is a structured block:

```markdown
### task-01: Define OpenAPI contract for feature
- status: [ ]
- touches: packages/contracts/openapi.yaml
- depends: none
- verify: just generate-client
- notes:
```

Fields:
- **status**: `[ ]` pending · `[x]` done · `[!]` blocked · `[~]` in progress
- **touches**: files/dirs this task expects to modify (blast radius)
- **depends**: prerequisite tasks
- **verify**: specific command to validate this task
- **notes**: filled after completion (what was done, surprises)

Rules:
- Tasks are atomic (one concern each)
- Tasks follow the feature-addition checklist in AGENTS.md: contract → generate → backend → migration → frontend → tests
- Order can be adjusted during EXECUTE, but must be logged in decisions.md
- New tasks can be appended (for bugs/missed requirements), but must be logged
- Tasks are never deleted — only marked `[!]` with explanation

### decisions.md — WHY things are the way they are

Append-only log of every non-trivial decision.

Format:
```markdown
## DEC-001 — 2026-03-29 — PLAN
**Context**: (what situation prompted this)
**Decision**: (what was decided)
**Rationale**: (why)
**Alternatives**: (what else was considered)
**Impact**: (what changes about the plan)
```

Log when: changing task order, adding tasks, modifying scope, choosing between alternatives, encountering unexpected behavior, deviating from any constraint, touching files outside declared blast radius.

### state.json — WHERE we are

Agent checkpoint. Enables resumption from any point.

```json
{
  "change_id": "add-notifications",
  "phase": "EXECUTE",
  "current_task": "task-03",
  "iteration": 1,
  "previous_phase": "VERIFY",
  "last_updated": "2026-03-29T14:30:00Z",
  "verification_failures": 0,
  "max_verification_retries": 3
}
```

### verification.md — Quality gate

Defines what "done" means. Lives in `/forge/global/`.

Contains:
- Ordered list of commands to run (`just lint`, `just test`, `just test-cov`)
- Thresholds (coverage %, zero errors policy)
- Failure protocol (retry → log → block)

---

## State Machine

### Phases

```
PLAN ←→ REVIEW → EXECUTE ←→ VERIFY → DONE
                               ↓
                            BLOCKED
```

### PLAN

Agent drafts spec + tasks in a single pass. No artificial separation between proposing and critiquing — the agent thinks freely but must produce complete, self-critiqued output.

Must run the adversarial checklist (see below) before finalizing.

Output: complete `/forge/changes/{change-id}/` directory.

**Stack-specific planning rules:**
- If the feature touches API contracts, the first task must update `packages/contracts/openapi.yaml`
- If the feature adds a new backend resource, tasks must follow the layered pattern: Model → Schema → Repository → Service → Router → deps.py wiring
- If the feature adds frontend UI, tasks must include: TanStack Query hooks → Zod schema → Components
- Always include a migration task if new/modified DB tables are involved
- Always include test tasks for both backend (pytest) and frontend (Vitest)

### REVIEW

Human-only gate. Read spec.md and tasks.md. Approve, request changes, or reject.

This is the **only mandatory human checkpoint**.

### EXECUTE

One task per agent invocation. The agent:
1. Reads state.json → finds current task
2. Reads task in tasks.md → knows what to implement and what files to touch
3. Implements the task (following AGENTS.md rules and `items` reference pattern)
4. Runs task-level verification
5. On success: marks `[x]`, fills notes, logs decisions, commits, advances
6. On failure: increments iteration, attempts fix, blocks after max retries

Rules:
- ONE task per invocation
- Never modify spec.md
- Touching files outside declared `touches` → log in decisions.md first
- New tasks → append to tasks.md + log in decisions.md
- Commit after every completed task
- Follow the layered architecture strictly: Router → Service → Repository
- Never put database logic in routers or services
- Never put business logic in repositories
- Always use `items` feature as reference pattern

### VERIFY

Automatic after each task:
1. Run task-specific `verify` command
2. Run full verification suite (`just lint && just test`)
3. Failures related to current task → return to EXECUTE
4. Failures unrelated to current task → log in decisions.md, don't block
5. All clear + more tasks → next EXECUTE
6. All clear + no tasks → final verification → DONE

### DONE

All tasks `[x]` or `[!]`. Final verification passes. State set to DONE. No further modifications.

### BLOCKED

Task exceeded max retries. Agent marks `[!]`, logs context, advances to next non-dependent task. If all remaining tasks depend on blocked one → stops, reports to human.

---

## Error Recovery

### Task fails verification
→ retry (up to max) → block → advance to next task

### Task introduces regression
→ create corrective task appended to tasks.md → original task stays `[x]`

### Spec needs to change during execution
→ stop → log in decisions.md → set phase to PLAN → human re-reviews

### Session dies mid-task
→ next session reads state.json → finds `[~]` in progress → resumes or restarts

### OpenAPI contract drift
→ run `just generate-client` → if generated types changed, create corrective task → log in decisions.md

### Rollback
→ `git revert` the task's commit → mark task `[ ]` or create replacement → log in decisions.md

Every task = one commit. Rollback is always surgical.

---

## Adversarial Critic Checklist

Used during PLAN. The agent must answer each one explicitly before finalizing.

```
 1. Is any requirement ambiguous enough to allow two different implementations?
 2. Does any requirement contradict a global constraint or AGENTS.md rules?
 3. Are there implicit requirements that users would expect but aren't written?
 4. What is the worst-case failure if implemented incorrectly?
 5. Are there external dependencies not declared?
 6. Can every requirement be verified with an automated test (pytest or Vitest)?
 7. Is the task ordering actually correct? Does task N depend on task N+2?
 8. Are there shared resources (DB tables, openapi.yaml, config, env vars) that multiple tasks touch?
 9. If partially implemented (8 of 15 tasks), is the system still safe?
10. Does this introduce any security surface that needs explicit handling?
11. Does this feature require OpenAPI contract changes? If so, is the contract task first?
12. Does this follow the `items` reference pattern? If not, why?
```

"Not applicable" is a valid answer. Skipping is not.

---

## Design Principles

**Memory over intelligence** — the agent forgets between sessions; the file system doesn't.

**Constraints over creativity** — free to think, not free to act.

**Contracts over convention** — OpenAPI is the source of truth; types are generated, never hand-written.

**Atomic progress** — every task is one commit, every commit is revertable.

**Explicit state** — anyone can read state.json + tasks.md and know exactly where things stand.

**Blast radius awareness** — every task declares what it touches; deviation requires justification.

**Imitation over invention** — copy the `items` reference feature; don't invent new patterns.
