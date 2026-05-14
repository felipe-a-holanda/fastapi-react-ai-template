#!/usr/bin/env python3
"""
forge-run — Autonomous execution loop for the FORGE protocol.

Finds the active change, drives the configured agent through one task per iteration,
and stops when all tasks are done, blocked, or limits are hit.

Usage:
    python forge_run.py
    python forge_run.py --max-iterations 50 --cooldown 10 --timeout 1200
    python forge_run.py --change add-auth    # target a specific change
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from agent_runner import print_agent_result, resolve_agent, run_agent
except ModuleNotFoundError:
    from forge.agent_runner import print_agent_result, resolve_agent, run_agent

# ── Constants ────────────────────────────────────────────────────────────────

FORGE_DIR = Path("forge")
CHANGES_DIR = FORGE_DIR / "changes"
LOGS_DIR = FORGE_DIR / "logs"

PROGRESS_START = (
    "<!-- forge:progress:start (auto-managed by forge_run; do not edit) -->"
)
PROGRESS_END = "<!-- forge:progress:end -->"
PROGRESS_BAR_WIDTH = 20

PROMPT = (
    "Read forge/AGENTS.md (bootstrap), AGENTS.md, and the active change's "
    "spec.md / tasks.md / decisions.md. Execute the next pending task following "
    "the FORGE protocol exactly. Stop after one task and commit."
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


def current_or_next_task(change_dir: Path) -> str:
    """Name of the in-progress task if any, else the first pending one."""
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.exists():
        return "(no tasks file)"

    text = tasks_file.read_text()
    lines = text.splitlines()

    def find_with_status(needle: str) -> str | None:
        for i, line in enumerate(lines):
            if line.startswith("### task-"):
                for j in range(i + 1, min(i + 5, len(lines))):
                    if needle in lines[j]:
                        return line.replace("### ", "").strip()
        return None

    return (
        find_with_status("status: [~]")
        or find_with_status("status: [ ]")
        or "(none found)"
    )


def render_progress_block(counts: dict, current: str) -> str:
    """Build the auto-managed progress block for the top of tasks.md."""
    done = counts["done"]
    in_prog = counts["in_progress"]
    pending = counts["pending"]
    blocked = counts["blocked"]
    total = done + in_prog + pending + blocked

    pct = int(round(100 * done / total)) if total else 0
    filled = int(round(PROGRESS_BAR_WIDTH * done / total)) if total else 0
    bar = "█" * filled + "░" * (PROGRESS_BAR_WIDTH - filled)
    updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return "\n".join(
        [
            PROGRESS_START,
            "## Progress",
            "",
            f"`{bar}` {pct}% ({done}/{total})",
            "",
            f"- ✅ {done} done · 🔄 {in_prog} in progress · ⏳ {pending} pending · 🚧 {blocked} blocked",
            f"- current: {current}",
            f"- updated: {updated}",
            "",
            PROGRESS_END,
        ]
    )


def update_tasks_progress(change_dir: Path, counts: dict, current: str) -> None:
    """Inject or replace the progress block in tasks.md (idempotent, no-op on errors)."""
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.exists():
        return

    try:
        text = tasks_file.read_text()
    except OSError:
        return

    block = render_progress_block(counts, current)

    if PROGRESS_START in text and PROGRESS_END in text:
        before, _, rest = text.partition(PROGRESS_START)
        _, _, after = rest.partition(PROGRESS_END)
        new_text = before + block + after
    else:
        # First run: inject after the H1, replacing any legacy `## Metadata` block.
        lines = text.splitlines(keepends=True)
        h1_idx = next((i for i, line in enumerate(lines) if line.startswith("# ")), -1)
        if h1_idx == -1:
            return
        insert_idx = h1_idx + 1
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1
        if insert_idx < len(lines) and lines[insert_idx].lstrip().startswith(
            "## Metadata"
        ):
            end_idx = next(
                (
                    i
                    for i in range(insert_idx + 1, len(lines))
                    if lines[i].startswith("## ")
                ),
                len(lines),
            )
        else:
            end_idx = insert_idx
        new_text = (
            "".join(lines[:insert_idx]) + block + "\n\n" + "".join(lines[end_idx:])
        )

    if new_text != text:
        tasks_file.write_text(new_text)


# ── Execution ────────────────────────────────────────────────────────────────


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
    print(
        f"  ✅ {done} done · ⏳ {pending} pending · 🚧 {blocked} blocked · 🔄 {in_prog} in progress"
    )
    print("═" * 60)


def print_final(counts: dict, reason: str):
    print()
    print("─" * 60)
    print(f"  FORGE run complete: {reason}")
    print(
        f"  ✅ {counts['done']} done · ⏳ {counts['pending']} pending · 🚧 {counts['blocked']} blocked"
    )
    print("─" * 60)


# ── Main loop ────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="FORGE autonomous execution runner")
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument(
        "--cooldown", type=int, default=5, help="seconds between iterations"
    )
    parser.add_argument(
        "--timeout", type=int, default=900, help="max seconds per agent invocation"
    )
    parser.add_argument(
        "--change", type=str, default=None, help="target a specific change ID"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show what would happen without running"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to pass through to the selected agent CLI. Defaults to the CLI's configured model.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Max turns per agent invocation (Claude only today; Codex ignores this flag).",
    )
    parser.add_argument(
        "--agent",
        choices=("claude", "codex"),
        default=None,
        help="Agent runner to invoke (default: FORGE_AGENT or claude)",
    )
    args = parser.parse_args()
    agent = resolve_agent(args.agent)

    print()
    print("🔨 FORGE — autonomous execution")
    print(f"   agent          : {agent}")
    print(f"   max iterations : {args.max_iterations}")
    print(f"   cooldown       : {args.cooldown}s")
    print(f"   timeout/iter   : {args.timeout}s")
    print(f"   max-turns/iter : {args.max_turns}")
    print(f"   model          : {args.model or '(CLI default)'}")

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
        current = current_or_next_task(change_dir)
        update_tasks_progress(change_dir, counts, current)
        print(f"\n  [dry-run] Would execute {counts['pending']} pending tasks")
        print(f"  Next: {current}")
        sys.exit(0)

    # Persistent log for this run — assistant text only. A sibling .jsonl file
    # gets raw agent events for offline forensics on tool calls, errors, etc.
    log_path = LOGS_DIR / f"{change_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    print(f"   log file       : {log_path}")
    print(f"   raw events     : {log_path.with_suffix('.jsonl')}")

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
        current = current_or_next_task(change_dir)
        update_tasks_progress(change_dir, counts, current)

        if counts["pending"] == 0 and counts["in_progress"] == 0:
            print_final(counts, "no pending tasks remain")
            break

        print_header(iteration, args.max_iterations, change_id, counts)
        print(f"  📌 Next: {current}")
        print(f"  🤖 Launching {agent} (timeout: {args.timeout}s)...")

        result = run_agent(
            agent=agent,
            prompt=PROMPT,
            timeout=args.timeout,
            max_turns=args.max_turns,
            model=args.model,
            log_path=log_path,
        )
        print_agent_result(agent, result)

        # Refresh progress block to reflect whatever the agent changed.
        post_counts = count_tasks(change_dir)
        update_tasks_progress(change_dir, post_counts, current_or_next_task(change_dir))

        if result.usage:
            tin = result.usage.get("input_tokens")
            tout = result.usage.get("output_tokens")
            if tin is not None or tout is not None:
                print(f"  🔢 tokens_in={tin} tokens_out={tout}")

        if result.hit_rate_limit:
            print_final(
                post_counts, "rate limit hit — stopping (check log for reset time)"
            )
            sys.exit(2)

        # Track consecutive failures
        if result.exit_code != 0:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print_final(
                    post_counts,
                    f"{max_consecutive_failures} consecutive failures — stopping",
                )
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
            capture_output=True,
            text=True,
        )
        if git_result.returncode == 0 and git_result.stdout.strip():
            print("\n  📁 Last commit changes:")
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
        print(
            f"\n  Final state: phase={state.get('phase')}, task={state.get('current_task')}"
        )


if __name__ == "__main__":
    main()
