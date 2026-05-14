#!/usr/bin/env python3
"""
forge_new.py — Bootstrap a new FORGE change

Usage:
    python forge/forge_new.py add-notifications
    python forge/forge_new.py add-notifications --description "Add email notifications for item comments"
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def create_change(change_id: str, description: str = "") -> None:
    """Create a new FORGE change directory with template files."""

    # Validate change_id
    if not change_id.replace("-", "").replace("_", "").isalnum():
        print(f"❌ Invalid change ID: {change_id}")
        print("   Use kebab-case (e.g., add-notifications, fix-payment-flow)")
        sys.exit(1)

    # Create directory
    change_dir = Path("forge/changes") / change_id
    if change_dir.exists():
        print(f"❌ Change already exists: {change_dir}")
        sys.exit(1)

    change_dir.mkdir(parents=True, exist_ok=True)

    # Create spec.md
    spec_content = f"""# {change_id} — {description or "TODO: Add description"}

## Goal

TODO: One paragraph describing what this change does and for whom.

## Non-Goals

- TODO: What this explicitly does NOT do

## Requirements

1. TODO: First requirement (must be testable)
2. TODO: Second requirement
3. TODO: Third requirement

## Constraints

- TODO: Feature-specific constraints (beyond global constraints in forge/global/constraints.md)

## Edge Cases

- TODO: Known edge cases and expected behavior

## Inputs / Outputs

### API Endpoints (if applicable)

```
POST /api/resource
Request:  {% raw %}{{ "field": "value" }}{% endraw %}
Success:  201 {% raw %}{{ "id": 1, "field": "value" }}{% endraw %}
Failure:  400 {% raw %}{{ "detail": "Validation error" }}{% endraw %}
```

### Database Schema (if applicable)

```sql
-- TODO: Table definitions or migrations
```

### UI States (if applicable)

- TODO: Loading, success, error states

## Open Questions

- TODO: Things the human must decide before execution
"""

    (change_dir / "spec.md").write_text(spec_content)

    # Create tasks.md
    tasks_content = f"""# Tasks — {change_id}

## Metadata
- total: 0
- completed: 0
- blocked: 0

## Task List

### task-01: TODO: First task description
- status: [ ]
- touches: TODO: files/dirs this task modifies
- depends: none
- verify: TODO: command to verify this task (e.g., just generate-client, pytest tests/test_feature.py)
- notes:

TODO: Detailed description of what this task does.

---

### task-02: TODO: Second task description
- status: [ ]
- touches: TODO: files/dirs
- depends: task-01
- verify: TODO: verify command
- notes:

TODO: Task description.

---

## Task Template

Copy this for new tasks:

### task-NN: TODO: Task description
- status: [ ]
- touches: TODO: files/dirs
- depends: TODO: task-XX or none
- verify: TODO: verify command
- notes:

TODO: Detailed description.

---
"""

    (change_dir / "tasks.md").write_text(tasks_content)

    # Create decisions.md
    decisions_content = f"""# Decisions — {change_id}

> Append-only log of non-trivial decisions made during planning and execution.

## Format

```markdown
## DEC-NNN — YYYY-MM-DD — PHASE
**Context**: (what situation prompted this)
**Decision**: (what was decided)
**Rationale**: (why)
**Alternatives**: (what else was considered)
**Impact**: (what changes about the plan)
```

---

(Decisions will be logged here during execution)
"""

    (change_dir / "decisions.md").write_text(decisions_content)

    # Create state.json
    state = {
        "change_id": change_id,
        "phase": "PLAN",
        "current_task": None,
        "iteration": 0,
        "previous_phase": None,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "verification_failures": 0,
        "max_verification_retries": 3
    }

    (change_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n")

    # Success message
    print(f"✓ Created FORGE change: {change_dir}")
    print()
    print("Next steps:")
    print(f"  1. Edit {change_dir}/spec.md — define requirements")
    print(f"  2. Edit {change_dir}/tasks.md — break down into atomic tasks")
    print(f"  3. Review the plan")
    print(f"  4. Update {change_dir}/state.json phase to 'EXECUTE' when ready")
    print(f"  5. Run: just forge")
    print()
    print(f"Or ask the agent to help fill out the plan:")
    print(f'  "Read {change_dir}/spec.md and help me complete the requirements and tasks"')


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a new FORGE change",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python forge/forge_new.py add-notifications
  python forge/forge_new.py add-notifications --description "Email notifications for item comments"
        """
    )

    parser.add_argument(
        "change_id",
        help="Change ID in kebab-case (e.g., add-notifications, fix-payment-flow)"
    )

    parser.add_argument(
        "--description",
        "-d",
        default="",
        help="Short description of the change"
    )

    args = parser.parse_args()

    create_change(args.change_id, args.description)


if __name__ == "__main__":
    main()
