# FORGE PLAN Prompt

Canonical instruction set for the FORGE PLAN phase. Consumed by two entry points:

- **Headless** — `forge/forge_plan.py` substitutes the variables below and feeds the
  result to `claude -p` in a subprocess.
- **Iterative** — the `forge-plan` skill reads this file inside an existing Claude Code
  session, substitutes the variables from the user's args, and follows it with
  human-in-the-loop iteration before finalizing.

Both paths read this same file so the protocol stays in one place.

## Variables

These placeholders are substituted before the prompt is used:

- `${change_id}` — the change ID (kebab-case, e.g. `add-notifications`).
- `${description}` — the feature description (may be a one-liner or a long spec doc).
- `${source_label}` — empty string, or ` (sourced from <path>)` when `--from-file` was used.
- `${source_note}` — empty string, or a note clarifying the source is an authoritative spec.

Everything below the `---` is the prompt itself.

---

You are starting the FORGE PLAN phase.

Change ID: ${change_id}

Feature request${source_label}:
---
${description}
---
${source_note}

MANDATORY — read ALL of these files before writing anything:
1. AGENTS.md
2. forge/global/architecture.md
3. forge/global/constraints.md
4. forge/global/verification.md
5. forge/CLAUDE.md  (for the full PLAN phase protocol and adversarial checklist)

After reading, create the following files in forge/changes/${change_id}/:

spec.md — complete spec with:
  - Goal: one paragraph, what and for whom
  - Non-Goals: what this explicitly does NOT do
  - Does Not Touch: explicit list of modules, files, and domains this change must NOT modify
  - Requirements: numbered, each must be testable
  - Constraints: feature-specific (beyond global constraints already in forge/global/constraints.md)
  - Invariants: domain rules the implementation must respect (e.g. "items MUST always have an owner_id"). Omit only if the feature introduces no domain rules worth enforcing.
  - Edge Cases: known edge cases and expected behavior
  - Inputs/Outputs: API endpoints (request/response), DB schema changes (SQL), UI states as applicable
  - Open Questions: anything the human must decide before execution

tasks.md — ordered atomic tasks following the AGENTS.md feature-addition checklist:
  openapi.yaml → generate-client → backend (model→schema→repo→service→router→deps.py wiring)
  → migration → frontend (hooks→schema→components) → tests (pytest + Vitest)
  Each task must have: status [ ], touches, depends, verify, notes fields.

  **Task sizing (executor is Claude Sonnet by default — plan for that):**
  - Each task touches AT MOST ~3 files and adds ~80 lines of new code.
  - Each task has ONE primary concern. If your `notes` describes more than three
    distinct concerns (e.g. "streaming + persist + async schedule + error
    paths"), SPLIT into sub-tasks with suffixes `a`/`b`/`c`/`d`
    (e.g. `task-29a`, `task-29b`). Sub-tasks ship in the same commit as
    the parent and share the same commit-boundary verification.
  - Orchestration-heavy services (multi-step async generators with error
    branches, streaming + persistence + side effects) MUST be split — at
    minimum: (a) scaffold + pure helpers, (b) state load/save + input
    validation, (c) main loop / happy path, (d) error/cancel paths.
  - Test files that bundle >4 scenarios MUST be split per scenario family
    into separate test files (one task each).

  **Verify command rule:**
  - The `verify` command of a task MUST pass at the moment that task
    completes — it CANNOT reference test files created by later tasks.
  - For backend implementation tasks scheduled BEFORE their test file
    exists, use import-smoke:
    `cd apps/backend && .venv/bin/python -c "from app.x.y import Z"`.
  - Pytest verify (`.venv/bin/pytest tests/test_x.py`) is owned ONLY by
    the test-authoring task that creates that file.
  - Migration tasks verify with `just db-upgrade && just db-downgrade && just db-upgrade`.
  - OpenAPI tasks verify with `just generate-client` followed by a
    build check (`pnpm build` or pytest contract test if test exists).

decisions.md — empty log with the standard header only.

state.json — set to:
  { "change_id": "${change_id}", "phase": "REVIEW", "current_task": null, "iteration": 0,
    "previous_phase": "PLAN", "last_updated": "<ISO timestamp>",
    "verification_failures": 0, "max_verification_retries": 3 }

Before finalizing, run the adversarial checklist from forge/CLAUDE.md against your own spec.
Answer every item — "N/A" is valid, skipping is not.
Verify every requirement has at least one task covering it.

When done, print a brief summary: goal, number of tasks, any open questions.
