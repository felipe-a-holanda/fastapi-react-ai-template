# Testing the Copier Template

This document describes how to test the copier template itself to ensure it generates valid, working projects.

## Testing Philosophy

The template is tested by:
1. **Generating a fresh project** from the template with test data
2. **Installing all dependencies** (backend Python packages + frontend pnpm packages)
3. **Running all quality checks** (linting, formatting, type checking)
4. **Executing database migrations** to verify the schema is valid
5. **Running the internal test suites** (pytest for backend, vitest for frontend)
6. **Building the frontend** to ensure production builds work
7. **Verifying critical files** exist in the generated project

This ensures that any project generated from this template will:
- Have valid, linted code
- Pass all internal tests
- Build successfully
- Have correct database migrations
- Match the OpenAPI contract spec

## Quick Start

### Local Testing (Manual)

Run the automated test script:

```bash
./test-template.sh
```

This will:
- Generate a test project in `/tmp/copier-template-test/test-project`
- Install all dependencies
- Run all checks and tests
- Clean up after completion

**Options:**

```bash
# Keep the test project for inspection
CLEANUP=false ./test-template.sh

# Use a custom test directory
TEST_DIR=/path/to/test ./test-template.sh
```

### CI Testing (Automated)

The template is automatically tested on every push/PR via GitHub Actions:

- **Workflow:** `.github/workflows/test-template.yml`
- **Triggers:** Push to `main`, PRs to `main`, manual dispatch
- **Duration:** ~5-10 minutes

The CI workflow runs the same validation steps as the local script.

## What Gets Tested

### 1. Template Generation
```bash
copier copy . /tmp/test-project \
  --data project_name="Test Project" \
  --data project_slug="test-project" \
  --data db_name="test_project" \
  --vcs-ref HEAD \
  --overwrite \
  --UNSAFE
```

Validates:
- Template renders without Jinja2 errors
- All template variables are properly substituted
- Generated project structure is correct

### 2. Dependency Installation

**Backend:**
```bash
cd apps/backend
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

**Frontend:**
```bash
pnpm install --frozen-lockfile
```

Validates:
- `pyproject.toml` dependencies are installable
- `package.json` dependencies are installable
- No version conflicts exist

### 3. Code Quality

**Backend:**
```bash
cd apps/backend
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

**Frontend:**
```bash
cd apps/frontend
pnpm lint
```

Validates:
- Generated code passes linting rules
- Generated code follows formatting standards
- No syntax errors in generated files

### 4. OpenAPI Contract Validation

```bash
pnpm --filter client generate
git diff --exit-code packages/client/src/types.ts
```

Validates:
- Generated TypeScript types match the OpenAPI spec
- No drift between contracts and types
- Type generation script works correctly

### 5. Database Migrations

```bash
cd apps/backend
.venv/bin/alembic upgrade head
```

Validates:
- Alembic configuration is correct
- Initial migrations apply cleanly
- Database schema is valid

### 6. Internal Test Suites

**Backend:**
```bash
cd apps/backend
.venv/bin/pytest -v
```

Tests:
- Auth endpoints (register, login, logout, /me)
- Items CRUD endpoints
- Database interactions
- Authentication flow

**Frontend:**
```bash
cd apps/frontend
pnpm test
```

Tests:
- Component rendering (basic smoke test)
- Ensures vitest is configured correctly

### 7. Production Build

```bash
cd apps/frontend
pnpm build
```

Validates:
- Next.js builds successfully
- No build-time errors
- All imports resolve correctly

### 8. File Structure Verification

Checks that critical files exist:
- Backend: `app/main.py`, `app/api/auth.py`, `app/api/items.py`, `tests/test_auth.py`
- Frontend: `src/app/page.tsx`, `src/features/auth/api.ts`, `src/features/items/api.ts`
- Contracts: `packages/contracts/openapi.yaml`, `packages/client/src/types.ts`
- Infrastructure: `docker-compose.yml`, `justfile`, `.github/workflows/ci.yml`
- Documentation: `AGENTS.md`, `ARCHITECTURE.md`

## Test Data

The template uses these test values during automated testing:

```yaml
project_name: Test Project
project_slug: test-project
db_name: test_project
python_version: "3.12"
node_version: "20"
author_name: Test Author
author_email: test@example.com
```

See `test-answers.yml` for the full data file.

## Running a Subset of Tests

You can manually test specific aspects:

```bash
# Generate project only
copier copy . /tmp/test-project --data-file test-answers.yml --overwrite

# Test backend only
cd /tmp/test-project
cd apps/backend
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check .
.venv/bin/pytest

# Test frontend only
cd /tmp/test-project
pnpm install
cd apps/frontend
pnpm lint
pnpm test
pnpm build
```

## Debugging Test Failures

### Template Generation Fails

- Check for Jinja2 syntax errors in template files
- Verify all template variables are defined in `copier.yml`
- Check for missing `{% raw %}...{% endraw %}` blocks around literal `{{ }}`

### Dependency Installation Fails

- Check `pyproject.toml` for invalid dependencies or version constraints
- Check `package.json` for deprecated or unavailable packages
- Verify pnpm workspace configuration is correct

### Linting Fails

- Run the generator locally with `CLEANUP=false ./test-template.sh`
- Inspect the generated code at `/tmp/copier-template-test/test-project`
- Fix the template files, not the generated files

### Tests Fail

- Check if template changes broke the test patterns
- Update tests in `template/apps/backend/tests/` or `template/apps/frontend/tests/`
- Ensure test fixtures in `conftest.py` match the schema

### Build Fails

- Check for import errors in generated frontend code
- Verify Next.js configuration is correct
- Check that all dependencies are properly declared

## Adding New Tests

When adding a new feature to the template:

1. Add tests to `template/apps/backend/tests/test_<feature>.py`
2. Add tests to `template/apps/frontend/tests/<feature>.test.tsx`
3. Run `./test-template.sh` to verify the generated project passes all tests
4. Commit both the template changes and the test changes

## Maintenance

### When to Run Tests

- Before releasing a new version of the template
- After modifying any file in `template/`
- After changing `copier.yml` configuration
- Before merging PRs to `main`

### Expected Test Duration

- Local: ~5 minutes (depends on network and CPU)
- CI: ~5-10 minutes (GitHub Actions runners)

### Updating Test Data

To change the test project configuration, edit `test-answers.yml`:

```yaml
project_name: My Test Name
project_slug: my-test-slug
# ... other values
```

Then run `./test-template.sh` to verify the changes work.

## Troubleshooting

### "Command not found: copier"

Install copier: `pip install copier`

### "Command not found: pnpm"

Install pnpm: `npm install -g pnpm`

### "Command not found: just"

Install just: `cargo install just` or `brew install just`

### "Permission denied: ./test-template.sh"

Make it executable: `chmod +x test-template.sh`

### Test directory already exists

The script cleans up automatically. If you used `CLEANUP=false`, manually remove it:
```bash
rm -rf /tmp/copier-template-test
```

## CI/CD Integration

The GitHub Actions workflow runs on:
- Every push to `main`
- Every pull request to `main`
- Manual trigger via "workflow_dispatch"

View test results:
- Go to the "Actions" tab in GitHub
- Select the "Test Template" workflow
- View logs for each step

## See Also

- `README.md` - Template usage documentation
- `WHY.md` - Design rationale
- `SPEC.md` - Template specification
- `template/.github/workflows/ci.yml` - Generated project CI (different from template testing)
