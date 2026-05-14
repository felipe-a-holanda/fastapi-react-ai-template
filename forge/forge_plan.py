#!/usr/bin/env python3
"""
forge_plan.py — FORGE PLAN phase: invoke Claude to produce a complete spec + task breakdown.

Claude is required to read global architecture, constraints, and verification docs before
writing anything. After this command, the change is in REVIEW phase and ready for human approval.

Usage:
    python forge/forge_plan.py <change-id> "<short description>"
    python forge/forge_plan.py <change-id> "<short description>" --max-turns 30
    python forge/forge_plan.py <change-id> --from-file <path/to/spec.md>
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

FORGE_DIR = Path("forge")
CHANGES_DIR = FORGE_DIR / "changes"
CLAUDE_CMD = "claude"

PLAN_PROMPT_TEMPLATE = """\
You are starting the FORGE PLAN phase.

Change ID: {change_id}

Feature request{source_label}:
---
{description}
---
{source_note}

MANDATORY — read ALL of these files before writing anything:
1. AGENTS.md
2. forge/global/architecture.md
3. forge/global/constraints.md
4. forge/global/verification.md
5. forge/CLAUDE.md  (for the full PLAN phase protocol and adversarial checklist)

After reading, create the following files in forge/changes/{change_id}/:

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

decisions.md — empty log with the standard header only.

state.json — set to:
  {{ "change_id": "{change_id}", "phase": "REVIEW", "current_task": null, "iteration": 0,
     "previous_phase": "PLAN", "last_updated": "<ISO timestamp>",
     "verification_failures": 0, "max_verification_retries": 3 }}

Before finalizing, run the adversarial checklist from forge/CLAUDE.md against your own spec.
Answer every item — "N/A" is valid, skipping is not.
Verify every requirement has at least one task covering it.

When done, print a brief summary: goal, number of tasks, any open questions.
"""


def create_change_dir(change_id: str) -> Path:
    """Create the change directory and an initial PLAN-phase state.json."""
    change_dir = CHANGES_DIR / change_id
    if change_dir.exists():
        state_file = change_dir / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            phase = state.get("phase", "")
            if phase not in ("PLAN", "REVIEW"):
                print(f"❌ Change '{change_id}' already exists in phase '{phase}'.")
                print("   Only PLAN or REVIEW phase changes can be re-planned.")
                sys.exit(1)
            print(f"↺  Re-planning existing change '{change_id}' (phase: {phase})")
        return change_dir

    change_dir.mkdir(parents=True, exist_ok=True)

    # Write a minimal state so the directory is recognizable
    state = {
        "change_id": change_id,
        "phase": "PLAN",
        "current_task": None,
        "iteration": 0,
        "previous_phase": None,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "verification_failures": 0,
        "max_verification_retries": 3,
    }
    (change_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    print(f"✓  Created forge/changes/{change_id}/")
    return change_dir


def run_claude_plan(
    change_id: str,
    description: str,
    max_turns: int,
    timeout: int,
    source_path: Path | None = None,
) -> int:
    """Invoke Claude Code with the planning prompt. Returns exit code."""
    if source_path is not None:
        source_label = f" (sourced from {source_path})"
        source_note = (
            "\nNOTE: The feature request above is a detailed spec document. "
            "Treat it as authoritative — decompose into as many atomic tasks as needed, "
            "do not condense or skip details. If anything conflicts with the global constraints "
            "or AGENTS.md rules, surface it in Open Questions rather than silently dropping it.\n"
        )
    else:
        source_label = ""
        source_note = ""

    prompt = PLAN_PROMPT_TEMPLATE.format(
        change_id=change_id,
        description=description,
        source_label=source_label,
        source_note=source_note,
    )

    print(f"\n🤖 Invoking Claude (max-turns: {max_turns}, timeout: {timeout}s)...")
    print("   Claude will read global architecture docs and produce the spec.\n")

    start = time.monotonic()
    try:
        result = subprocess.run(
            [
                CLAUDE_CMD,
                "--dangerously-skip-permissions",
                "--max-turns", str(max_turns),
                "--verbose",
                "-p", prompt,
            ],
            timeout=timeout,
            capture_output=False,
            stdin=subprocess.DEVNULL,
        )
        elapsed = time.monotonic() - start
        mins, secs = divmod(int(elapsed), 60)
        time_str = f"{mins}m{secs}s" if mins else f"{secs}s"

        if result.returncode == 0:
            print(f"\n✔  Claude finished in {time_str}")
        else:
            print(f"\n⚠  Claude exited with code {result.returncode} after {time_str}")

        return result.returncode

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        print(f"\n⚠  Timeout after {int(elapsed)}s — Claude was killed")
        return 124
    except FileNotFoundError:
        print(f"\n✗ '{CLAUDE_CMD}' not found. Is Claude Code installed and in PATH?")
        sys.exit(1)


def print_next_steps(change_id: str, change_dir: Path) -> None:
    """Check final state and print what to do next."""
    state_file = change_dir / "state.json"
    if not state_file.exists():
        print("\n⚠  state.json not found — Claude may not have completed the plan.")
        return

    state = json.loads(state_file.read_text())
    phase = state.get("phase", "UNKNOWN")

    print()
    print("─" * 60)
    if phase == "REVIEW":
        print(f"  Plan ready for review: forge/changes/{change_id}/")
        print()
        print("  Next steps:")
        print(f"    1. Review:  just forge-review {change_id}")
        print(f"    2. Approve: just forge-approve {change_id}")
        print(f"    3. Execute: just forge")
        print()
        print("  To request changes: edit spec.md then re-run forge-plan.")
    else:
        print(f"  Plan is in phase '{phase}' — may need manual review.")
        print(f"  Check: forge/changes/{change_id}/spec.md")
    print("─" * 60)


def validate_change_id(change_id: str) -> None:
    if not change_id.replace("-", "").replace("_", "").isalnum():
        print(f"❌ Invalid change ID: '{change_id}'")
        print("   Use kebab-case (e.g., add-notifications, fix-payment-flow)")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="FORGE PLAN phase — invoke Claude to produce a complete spec",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python forge/forge_plan.py add-notifications "Add email notifications for item comments"
  python forge/forge_plan.py fix-auth "Fix JWT expiry handling in refresh flow" --max-turns 20
        """,
    )
    parser.add_argument("change_id", help="Change ID in kebab-case")
    parser.add_argument(
        "description",
        nargs="?",
        default=None,
        help="Feature description (omit if using --from-file)",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        default=None,
        help="Read the feature description from a file (e.g. _input/SPEC.md). "
             "When set, defaults to --max-turns 60 --timeout 1800.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Max Claude turns (default: 25 inline, 60 with --from-file)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Max seconds (default: 600 inline, 1800 with --from-file)",
    )
    args = parser.parse_args()

    validate_change_id(args.change_id)

    if args.from_file and args.description:
        print("❌ Pass either a positional description OR --from-file, not both.")
        sys.exit(1)
    if not args.from_file and not args.description:
        print("❌ Missing feature description. Pass it as a positional arg or use --from-file PATH.")
        sys.exit(1)

    if args.from_file:
        if not args.from_file.is_file():
            print(f"❌ --from-file path does not exist: {args.from_file}")
            sys.exit(1)
        description = args.from_file.read_text()
        source_path: Path | None = args.from_file
        default_max_turns, default_timeout = 60, 1800
        desc_preview = f"<{len(description)} chars from {args.from_file}>"
    else:
        description = args.description
        source_path = None
        default_max_turns, default_timeout = 25, 600
        desc_preview = args.description

    max_turns = args.max_turns if args.max_turns is not None else default_max_turns
    timeout = args.timeout if args.timeout is not None else default_timeout

    print()
    print("🔨 FORGE — PLAN phase")
    print(f"   change:      {args.change_id}")
    print(f"   description: {desc_preview}")

    change_dir = create_change_dir(args.change_id)

    exit_code = run_claude_plan(
        args.change_id,
        description,
        max_turns,
        timeout,
        source_path=source_path,
    )

    print_next_steps(args.change_id, change_dir)

    sys.exit(0 if exit_code == 0 else exit_code)


if __name__ == "__main__":
    main()
