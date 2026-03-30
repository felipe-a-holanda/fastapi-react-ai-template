#!/usr/bin/env python3
"""
forge-run — Autonomous execution loop for the FORGE protocol.

Finds the active change, drives Claude Code through one task per iteration,
and stops when all tasks are done, blocked, or limits are hit.

Usage:
    python forge_run.py
    python forge_run.py --max-iterations 50 --cooldown 10 --timeout 1200
    python forge_run.py --change add-auth    # target a specific change
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

FORGE_DIR = Path("forge")
CHANGES_DIR = FORGE_DIR / "changes"
CLAUDE_CMD = "claude"

PROMPT = (
    "Read CLAUDE.md and AGENTS.md. Execute the next pending task for the active change. "
    "Follow the FORGE protocol exactly. Use the items feature as reference pattern."
)

# ── Data helpers ─────────────────────────────────────────────────────────────


def load_state(change_dir: Path) -> dict | None:
    state_file = change_dir / "state.json"
    if not state_file.exists():
        return None
    with open(state_file) as f:
        return json.load(f)


def find_active_change(target: str | None = None) -> tuple[Path, dict] | None:
    """Find a change directory with an active (non-DONE) state."""
    if not CHANGES_DIR.exists():
        return None

    candidates = []
    for d in sorted(CHANGES_DIR.iterdir()):
        if not d.is_dir():
            continue
        if target and d.name != target:
            continue
        state = load_state(d)
        if state and state.get("phase") not in ("DONE", None):
            candidates.append((d, state))

    if not candidates:
        return None

    # Prefer EXECUTE/VERIFY phase over PLAN/REVIEW
    execution = [c for c in candidates if c[1].get("phase") in ("EXECUTE", "VERIFY")]
    return execution[0] if execution else candidates[0]


def count_tasks(change_dir: Path) -> dict[str, int]:
    """Count task statuses from tasks.md."""
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.exists():
        return {"pending": 0, "done": 0, "blocked": 0, "in_progress": 0}

    text = tasks_file.read_text()
    return {
        "pending": len(re.findall(r"- status: \[ \]", text)),
        "done": len(re.findall(r"- status: \[x\]", text)),
        "blocked": len(re.findall(r"- status: \[!\]", text)),
        "in_progress": len(re.findall(r"- status: \[~\]", text)),
    }


def next_task_name(change_dir: Path) -> str:
    """Get the name of the next pending task."""
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.exists():
        return "(no tasks file)"

    text = tasks_file.read_text()
    # Find task headers followed by pending status
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("### task-"):
            # Check if next non-empty line has pending status
            for j in range(i + 1, min(i + 5, len(lines))):
                if "status: [ ]" in lines[j]:
                    return line.replace("### ", "").strip()
    return "(none found)"


# ── Execution ────────────────────────────────────────────────────────────────


def run_claude(timeout: int) -> tuple[int, float]:
    """Run Claude Code with the FORGE prompt. Returns (exit_code, elapsed_seconds)."""
    start = time.monotonic()

    try:
        result = subprocess.run(
            [
                CLAUDE_CMD,
                "--dangerously-skip-permissions",
                "--max-turns", "50",
                "--verbose",
                "-p", PROMPT,
            ],
            timeout=timeout,
            capture_output=False,
            stdin=subprocess.DEVNULL,
        )
        elapsed = time.monotonic() - start
        return result.returncode, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return 124, elapsed
    except FileNotFoundError:
        print(f"\n  ✗ '{CLAUDE_CMD}' not found. Is Claude Code installed and in PATH?")
        sys.exit(1)


def run_verification() -> tuple[bool, str]:
    """Run the project test suite as independent verification."""
    verify_file = FORGE_DIR / "global" / "verification.md"
    if not verify_file.exists():
        return True, "no verification.md found, skipping"

    # Run just test as the primary verification command
    try:
        result = subprocess.run(
            ["just", "test"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            return True, "all tests pass (backend pytest + frontend vitest)"
        else:
            # Extract last few lines of output for context
            output = (result.stdout + result.stderr).strip().splitlines()
            summary = "\n".join(output[-10:]) if len(output) > 10 else "\n".join(output)
            return False, summary
    except FileNotFoundError:
        return True, "just not found, skipping independent verification"
    except subprocess.TimeoutExpired:
        return False, "test suite timed out (300s)"


# ── Display ──────────────────────────────────────────────────────────────────


def print_header(iteration: int, max_iter: int, change_id: str, counts: dict):
    now = datetime.now().strftime("%H:%M:%S")
    done = counts["done"]
    pending = counts["pending"]
    blocked = counts["blocked"]
    in_prog = counts["in_progress"]

    print()
    print("═" * 60)
    print(f"  FORGE — iteration {iteration}/{max_iter} — {now}")
    print(f"  change: {change_id}")
    print(f"  ✅ {done} done · ⏳ {pending} pending · 🚧 {blocked} blocked · 🔄 {in_prog} in progress")
    print("═" * 60)


def print_result(exit_code: int, elapsed: float):
    mins = int(elapsed) // 60
    secs = int(elapsed) % 60
    time_str = f"{mins}m{secs}s" if mins > 0 else f"{secs}s"

    if exit_code == 124:
        print(f"\n  ⚠  TIMEOUT after {time_str} — Claude was killed")
    elif exit_code != 0:
        print(f"\n  ⚠  Claude exited with code {exit_code} after {time_str}")
    else:
        print(f"\n  ✔  Claude finished in {time_str}")


def print_final(counts: dict, reason: str):
    print()
    print("─" * 60)
    print(f"  FORGE run complete: {reason}")
    print(f"  ✅ {counts['done']} done · ⏳ {counts['pending']} pending · 🚧 {counts['blocked']} blocked")
    print("─" * 60)


# ── Main loop ────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="FORGE autonomous execution runner")
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument("--cooldown", type=int, default=5, help="seconds between iterations")
    parser.add_argument("--timeout", type=int, default=900, help="max seconds per Claude invocation")
    parser.add_argument("--change", type=str, default=None, help="target a specific change ID")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen without running")
    args = parser.parse_args()

    print()
    print("🔨 FORGE — autonomous execution")
    print(f"   max iterations : {args.max_iterations}")
    print(f"   cooldown       : {args.cooldown}s")
    print(f"   timeout/iter   : {args.timeout}s")

    # Find active change
    result = find_active_change(args.change)
    if not result:
        if args.change:
            print(f"\n  ✗ No active change found with ID '{args.change}'")
        else:
            print("\n  ✗ No active change found in forge/changes/")
            print("    Run PLAN phase first to create a change.")
        sys.exit(1)

    change_dir, state = result
    change_id = state.get("change_id", change_dir.name)
    phase = state.get("phase", "UNKNOWN")

    print(f"   active change  : {change_id}")
    print(f"   current phase  : {phase}")

    if phase in ("PLAN", "REVIEW"):
        print(f"\n  ⏸  Change '{change_id}' is in {phase} phase.")
        print("    Approve the plan first (set phase to EXECUTE in state.json).")
        sys.exit(0)

    if args.dry_run:
        counts = count_tasks(change_dir)
        print(f"\n  [dry-run] Would execute {counts['pending']} pending tasks")
        print(f"  Next: {next_task_name(change_dir)}")
        sys.exit(0)

    # ── Execution loop ───────────────────────────────────────────────────

    consecutive_failures = 0
    max_consecutive_failures = 5

    for iteration in range(1, args.max_iterations + 1):
        # Reload state each iteration (agent may have changed it)
        state = load_state(change_dir)
        if not state:
            print("\n  ✗ state.json disappeared. Stopping.")
            break

        if state.get("phase") == "DONE":
            counts = count_tasks(change_dir)
            print_final(counts, "all tasks complete — phase is DONE")
            break

        if state.get("phase") == "PLAN":
            counts = count_tasks(change_dir)
            print_final(counts, "agent set phase back to PLAN — human review needed")
            break

        counts = count_tasks(change_dir)

        if counts["pending"] == 0 and counts["in_progress"] == 0:
            print_final(counts, "no pending tasks remain")
            break

        print_header(iteration, args.max_iterations, change_id, counts)
        print(f"  📌 Next: {next_task_name(change_dir)}")
        print(f"  🤖 Launching Claude (timeout: {args.timeout}s)...")

        # Run Claude
        exit_code, elapsed = run_claude(args.timeout)
        print_result(exit_code, elapsed)

        # Track consecutive failures
        if exit_code != 0:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                counts = count_tasks(change_dir)
                print_final(counts, f"{max_consecutive_failures} consecutive failures — stopping")
                sys.exit(1)
        else:
            consecutive_failures = 0

        # Independent verification (optional, non-blocking)
        print("\n  🔍 Independent verification...")
        ok, msg = run_verification()
        if ok:
            print(f"     ✔ {msg}")
        else:
            print(f"     ⚠ {msg}")

        # Git status
        git_result = subprocess.run(
            ["git", "diff", "--stat", "HEAD~1"],
            capture_output=True, text=True,
        )
        if git_result.returncode == 0 and git_result.stdout.strip():
            print(f"\n  📁 Last commit changes:")
            for line in git_result.stdout.strip().splitlines():
                print(f"     {line}")

        # Cooldown
        if iteration < args.max_iterations:
            print(f"\n  ⏱  Cooling down {args.cooldown}s...")
            time.sleep(args.cooldown)

    else:
        counts = count_tasks(change_dir)
        print_final(counts, f"reached max iterations ({args.max_iterations})")

    # Final summary
    state = load_state(change_dir)
    if state:
        print(f"\n  Final state: phase={state.get('phase')}, task={state.get('current_task')}")


if __name__ == "__main__":
    main()
