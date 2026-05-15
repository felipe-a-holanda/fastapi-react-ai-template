#!/usr/bin/env python3
"""
forge_approve.py — Approve a FORGE plan and transition it to EXECUTE phase.

Reads tasks.md to find the first pending task, then updates state.json:
  phase: REVIEW → EXECUTE
  current_task: first pending task ID

Usage:
    python forge/forge_approve.py
    python forge/forge_approve.py --change add-notifications
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FORGE_DIR = Path("forge")
CHANGES_DIR = FORGE_DIR / "changes"


def load_state(change_dir: Path) -> dict | None:
    state_file = change_dir / "state.json"
    if not state_file.exists():
        return None
    return json.loads(state_file.read_text())


def find_review_change(target: str | None) -> tuple[Path, dict] | None:
    """Find a change in REVIEW phase."""
    if not CHANGES_DIR.exists():
        return None

    for d in sorted(CHANGES_DIR.iterdir()):
        if not d.is_dir():
            continue
        if target and d.name != target:
            continue
        state = load_state(d)
        if state and state.get("phase") == "REVIEW":
            return d, state

    return None


def find_first_pending_task(change_dir: Path) -> str | None:
    """Return the ID of the first pending task (e.g. 'task-01')."""
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.exists():
        return None

    lines = tasks_file.read_text().splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^### task-\S+", line):
            for j in range(i + 1, min(i + 6, len(lines))):
                if "status: [ ]" in lines[j]:
                    # Extract "task-01" from "### task-01: desc", "### task-01 — desc", etc.
                    match = re.match(r"^### (task-\S+?)(?:[\s:]|$)", line)
                    if match:
                        return match.group(1)
    return None


def count_tasks(change_dir: Path) -> dict[str, int]:
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.exists():
        return {}
    text = tasks_file.read_text()
    return {
        "pending": len(re.findall(r"- status: \[ \]", text)),
        "done": len(re.findall(r"- status: \[x\]", text)),
        "blocked": len(re.findall(r"- status: \[!\]", text)),
    }


def tag_spec_approved(change_id: str) -> str | None:
    """Create an annotated git tag marking the spec-approved point.

    Returns the tag name on success, None if skipped/failed (non-fatal).
    """
    tag = f"forge/{change_id}/spec-approved"
    try:
        in_repo = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
        )
        if in_repo.returncode != 0 or in_repo.stdout.strip() != "true":
            return None

        exists = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
            capture_output=True,
        )
        if exists.returncode == 0:
            print(f"   tag:          {tag} (already exists, skipped)")
            return None

        result = subprocess.run(
            [
                "git",
                "tag",
                "-a",
                tag,
                "-m",
                f"FORGE: spec approved for {change_id} — EXECUTE phase begins",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"   tag:          failed ({result.stderr.strip() or 'unknown error'})")
            return None
        return tag
    except FileNotFoundError:
        return None


def approve(change_dir: Path, state: dict) -> None:
    change_id = state.get("change_id", change_dir.name)

    first_task = find_first_pending_task(change_dir)
    if not first_task:
        print(f"❌ No pending tasks found in forge/changes/{change_id}/tasks.md")
        print("   Make sure tasks.md has at least one task with '- status: [ ]'")
        sys.exit(1)

    counts = count_tasks(change_dir)

    # Update state
    state["phase"] = "EXECUTE"
    state["previous_phase"] = "REVIEW"
    state["current_task"] = first_task
    state["iteration"] = 0
    state["verification_failures"] = 0
    state["last_updated"] = datetime.now(timezone.utc).isoformat()

    state_file = change_dir / "state.json"
    state_file.write_text(json.dumps(state, indent=2) + "\n")

    print()
    print("✓  Plan approved")
    print(f"   change:       {change_id}")
    print(f"   first task:   {first_task}")
    print(f"   total tasks:  {counts.get('pending', 0)} pending, {counts.get('done', 0)} done")

    created_tag = tag_spec_approved(change_id)
    if created_tag:
        print(f"   tag:          {created_tag}")
    print()
    print("  Run the autonomous execution loop:")
    print("    just forge")
    print()
    print("  Or target this change explicitly:")
    print(f"    just forge --change {change_id}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Approve a FORGE plan — transitions REVIEW → EXECUTE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python forge/forge_approve.py
  python forge/forge_approve.py --change add-notifications
        """,
    )
    parser.add_argument(
        "--change",
        "-c",
        default=None,
        help="Target a specific change ID (auto-detected if only one is in REVIEW)",
    )
    args = parser.parse_args()

    result = find_review_change(args.change)
    if not result:
        if args.change:
            print(f"❌ No change in REVIEW phase with ID '{args.change}'")
        else:
            print("❌ No change in REVIEW phase found in forge/changes/")
            print("   Run 'just forge-plan' first to create and plan a change.")
        sys.exit(1)

    change_dir, state = result
    approve(change_dir, state)


if __name__ == "__main__":
    main()
