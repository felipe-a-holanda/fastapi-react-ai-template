# Verification Protocol

> Defines what "done" means. The agent runs these checks after every task.

## Commands (run in order, all must pass)

```bash
# 1. Backend lint (Ruff check + format check)
just lint                  # must exit 0

# 2. Backend tests (pytest against test database)
just test                  # must exit 0

# 3. Frontend build (catches TypeScript errors)
cd apps/frontend && pnpm build   # must exit 0
```

### Individual commands (for task-level verification)

```bash
# Backend only
cd apps/backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .
cd apps/backend && DATABASE_URL="postgresql+asyncpg://app:app@localhost:54325/app_test" .venv/bin/pytest

# Backend specific test file
cd apps/backend && DATABASE_URL="postgresql+asyncpg://app:app@localhost:54325/app_test" .venv/bin/pytest tests/test_<feature>.py -v

# Frontend only
cd apps/frontend && pnpm lint
cd apps/frontend && pnpm test --run

# OpenAPI client generation (verify contract consistency)
just generate-client
```

### Coverage (optional, for final verification)

```bash
just test-cov              # backend coverage report
```

## Thresholds

| Metric            | Minimum |
|-------------------|---------|
| Backend lint errors (Ruff) | 0 |
| Backend test failures | 0 |
| Frontend lint errors | 0 |
| Frontend test failures | 0 |
| Frontend build errors | 0 |

Coverage thresholds are advisory (aim for 80%+ line coverage on backend).

## Task-Level Verification

Each task in `tasks.md` has a `verify` field with a specific command.
The task-level command runs **first**. If it passes, run the full suite above.

Common task-level verify patterns:
- **Contract task**: `just generate-client`
- **Backend model/schema/repo/service**: `cd apps/backend && .venv/bin/pytest tests/test_<feature>.py -v`
- **Backend router**: `cd apps/backend && .venv/bin/pytest tests/test_<feature>.py -v`
- **Migration**: `just db-upgrade`
- **Frontend component**: `cd apps/frontend && pnpm test --run`
- **Full stack**: `just lint && just test`

## Failure Protocol

1. **First failure**: analyze error, fix, retry
2. **Second failure**: log root cause analysis in `decisions.md`, fix, retry
3. **Third failure**: mark task `[!]` blocked, log full context in `decisions.md`, advance to next non-dependent task

## What "unrelated failure" means

If the full suite fails on a test that:
- Existed before the current task
- Tests functionality outside the current task's scope
- Was not modified by the current task

Then it is **unrelated**. Log it in `decisions.md` as a known issue. Do NOT block the current task.

## Final Verification

When all tasks are complete, run the full suite one last time:

```bash
just lint && just test && cd apps/frontend && pnpm build
```

All thresholds must be met. If they are, set `state.json` phase to `"DONE"`.
