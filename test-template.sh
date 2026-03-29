#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="${TEST_DIR:-/tmp/copier-template-test}"
PROJECT_NAME="test-project"
CLEANUP="${CLEANUP:-true}"

echo -e "${YELLOW}==> Testing Copier Template${NC}"
echo "Test directory: $TEST_DIR"
echo "Cleanup after test: $CLEANUP"
echo ""

# Cleanup function
cleanup() {
    if [ "$CLEANUP" = "true" ]; then
        echo -e "${YELLOW}==> Cleaning up test directory${NC}"
        rm -rf "$TEST_DIR"
    else
        echo -e "${YELLOW}==> Skipping cleanup (test directory preserved at $TEST_DIR)${NC}"
    fi
}

# Register cleanup on exit
trap cleanup EXIT

# Step 1: Generate project from template
echo -e "${GREEN}==> Step 1: Generating project from template${NC}"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

copier copy . "$TEST_DIR/$PROJECT_NAME" \
    --data project_name="Test Project" \
    --data project_slug="test-project" \
    --data db_name="test_project" \
    --data python_version="3.12" \
    --data node_version="20" \
    --data author_name="Test Author" \
    --data author_email="test@example.com" \
    --vcs-ref HEAD \
    --overwrite \
    --UNSAFE

cd "$TEST_DIR/$PROJECT_NAME"
echo -e "${GREEN}✓ Project generated successfully${NC}"
echo ""

# Step 2: Install backend dependencies
echo -e "${GREEN}==> Step 2: Installing backend dependencies${NC}"
cd apps/backend
python -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e ".[dev]"
cd ../..
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# Step 3: Install frontend dependencies
echo -e "${GREEN}==> Step 3: Installing frontend dependencies${NC}"
pnpm install --frozen-lockfile
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
echo ""

# Step 4: Lint backend
echo -e "${GREEN}==> Step 4: Linting backend code${NC}"
cd apps/backend
.venv/bin/ruff check .
.venv/bin/ruff format --check .
cd ../..
echo -e "${GREEN}✓ Backend lint passed${NC}"
echo ""

# Step 5: Lint frontend
echo -e "${GREEN}==> Step 5: Linting frontend code${NC}"
cd apps/frontend
pnpm lint
cd ../..
echo -e "${GREEN}✓ Frontend lint passed${NC}"
echo ""

# Step 6: Verify contracts
echo -e "${GREEN}==> Step 6: Verifying OpenAPI contracts${NC}"
pnpm --filter client generate
if git diff --exit-code packages/client/src/types.ts; then
    echo -e "${GREEN}✓ Generated types match committed types${NC}"
else
    echo -e "${RED}✗ Generated types differ from committed types${NC}"
    exit 1
fi
echo ""

# Step 7: Setup test database and run migrations
echo -e "${GREEN}==> Step 7: Setting up test database${NC}"
cd apps/backend
# Create SQLite database for testing
.venv/bin/alembic upgrade head
echo -e "${GREEN}✓ Database migrations applied${NC}"
cd ../..
echo ""

# Step 8: Run backend tests
echo -e "${GREEN}==> Step 8: Running backend tests${NC}"
cd apps/backend
.venv/bin/pytest -v
echo -e "${GREEN}✓ Backend tests passed${NC}"
cd ../..
echo ""

# Step 9: Run frontend tests
echo -e "${GREEN}==> Step 9: Running frontend tests${NC}"
cd apps/frontend
pnpm test
echo -e "${GREEN}✓ Frontend tests passed${NC}"
cd ../..
echo ""

# Step 10: Build frontend
echo -e "${GREEN}==> Step 10: Building frontend${NC}"
cd apps/frontend
pnpm build
echo -e "${GREEN}✓ Frontend build successful${NC}"
cd ../..
echo ""

# Step 11: Verify critical files exist
echo -e "${GREEN}==> Step 11: Verifying generated project structure${NC}"
CRITICAL_FILES=(
    "apps/backend/app/main.py"
    "apps/backend/app/api/auth.py"
    "apps/backend/app/api/items.py"
    "apps/backend/app/models/user.py"
    "apps/backend/app/models/item.py"
    "apps/backend/tests/test_auth.py"
    "apps/backend/tests/test_items.py"
    "apps/frontend/src/app/page.tsx"
    "apps/frontend/src/features/auth/api.ts"
    "apps/frontend/src/features/items/api.ts"
    "packages/contracts/openapi.yaml"
    "packages/client/src/types.ts"
    "docker-compose.yml"
    "justfile"
    "AGENTS.md"
    "ARCHITECTURE.md"
    ".github/workflows/ci.yml"
)

MISSING_FILES=()
for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All critical files present${NC}"
else
    echo -e "${RED}✗ Missing files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    exit 1
fi
echo ""

# Success!
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All tests passed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Template is ready for use."
