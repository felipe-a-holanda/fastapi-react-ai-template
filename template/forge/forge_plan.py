#!/usr/bin/env python3
"""
forge_plan.py — FORGE PLAN phase: invoke Claude to produce a complete spec + task breakdown.

The prompt template lives in `forge/PLAN_PROMPT.md` (one source of truth, also used by
the `forge-plan` skill). This script substitutes the variables and feeds the result to
`claude -p`, streaming progress events live.

After this command, the change is in REVIEW phase and ready for human approval.

Usage:
    python forge/forge_plan.py <change-id> "<short description>"
    python forge/forge_plan.py <change-id> "<short description>" --max-turns 30
    python forge/forge_plan.py <change-id> --from-file <path/to/spec.md>
"""

import argparse
import json
import string
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

FORGE_DIR = Path("forge")
CHANGES_DIR = FORGE_DIR / "changes"
PROMPT_FILE = FORGE_DIR / "PLAN_PROMPT.md"
CLAUDE_CMD = "claude"

HEARTBEAT_INTERVAL = 30  # seconds between "still running…" pings if no output


def load_prompt_template() -> str:
    """Read the prompt template from PLAN_PROMPT.md.

    The file contains a documentation header followed by '---' on its own line,
    then the actual prompt. Only the part after the first standalone '---' is
    returned (the header is for human readers and the skill, not the LLM).
    """
    if not PROMPT_FILE.is_file():
        print(f"❌ Missing prompt template: {PROMPT_FILE}")
        sys.exit(1)
    raw = PROMPT_FILE.read_text()
    # Split on the first '---' that sits on its own line.
    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        print(f"❌ {PROMPT_FILE} is missing the '---' separator between header and prompt.")
        sys.exit(1)
    return parts[1].lstrip("\n")


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


# ── Stream-json rendering ────────────────────────────────────────────────────


def _fmt_size(n: int) -> str:
    if n >= 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n}B"


def _summarize_tool_input(name: str, inp: dict) -> str:
    if name in ("Read", "Edit"):
        path = inp.get("file_path", "?")
        return str(path).replace(str(Path.cwd()) + "/", "")
    if name == "Write":
        path = inp.get("file_path", "?")
        size = len(inp.get("content", "") or "")
        rel = str(path).replace(str(Path.cwd()) + "/", "")
        return f"{rel} ({_fmt_size(size)})"
    if name == "Bash":
        cmd = (inp.get("command") or "").splitlines()[0] if inp.get("command") else ""
        return cmd[:100]
    if name == "Glob":
        return inp.get("pattern", "?")
    if name == "Grep":
        return inp.get("pattern", "?")
    if name == "TodoWrite":
        todos = inp.get("todos") or []
        return f"{len(todos)} todo(s)"
    # Generic fallback — first one or two short fields.
    bits = []
    for k, v in list(inp.items())[:2]:
        sv = str(v)
        if len(sv) > 60:
            sv = sv[:57] + "…"
        bits.append(f"{k}={sv}")
    return ", ".join(bits)


def _render_event(event: dict, *, start: float) -> None:
    """Print a single one-line summary for an interesting stream-json event."""
    et = event.get("type")
    if et == "assistant":
        msg = event.get("message") or {}
        for block in msg.get("content") or []:
            bt = block.get("type")
            if bt == "tool_use":
                name = block.get("name", "?")
                summary = _summarize_tool_input(name, block.get("input") or {})
                elapsed = int(time.monotonic() - start)
                mins, secs = divmod(elapsed, 60)
                print(f"  [{mins:02d}:{secs:02d}] {name:<10} {summary}", flush=True)
            elif bt == "text":
                text = (block.get("text") or "").strip()
                if text:
                    first = text.splitlines()[0][:140]
                    print(f"         · {first}", flush=True)
    elif et == "result":
        # Final summary handled by caller (so we can show cost/turns alongside time).
        pass


def run_claude_plan(
    change_id: str,
    description: str,
    max_turns: int,
    timeout: int,
    source_path: Path | None = None,
) -> int:
    """Invoke Claude Code with the planning prompt, streaming events. Returns exit code."""
    template = load_prompt_template()

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

    prompt = string.Template(template).safe_substitute(
        change_id=change_id,
        description=description,
        source_label=source_label,
        source_note=source_note,
    )

    print(f"\n🤖 Invoking Claude (max-turns: {max_turns}, timeout: {timeout}s)")
    print("   Streaming progress (elapsed mm:ss):\n")

    start = time.monotonic()
    try:
        proc = subprocess.Popen(
            [
                CLAUDE_CMD,
                "--dangerously-skip-permissions",
                "--max-turns", str(max_turns),
                "--output-format", "stream-json",
                "--verbose",
                "-p", prompt,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        print(f"\n✗ '{CLAUDE_CMD}' not found. Is Claude Code installed and in PATH?")
        sys.exit(1)

    stop_event = threading.Event()
    timed_out = threading.Event()

    def heartbeat() -> None:
        while not stop_event.wait(HEARTBEAT_INTERVAL):
            elapsed = int(time.monotonic() - start)
            mins, secs = divmod(elapsed, 60)
            print(
                f"  ⏳ still running… {mins}m{secs}s elapsed (timeout at {timeout}s)",
                file=sys.stderr, flush=True,
            )

    def watchdog() -> None:
        if not stop_event.wait(timeout):
            timed_out.set()
            try:
                proc.kill()
            except ProcessLookupError:
                pass

    hb = threading.Thread(target=heartbeat, daemon=True)
    wd = threading.Thread(target=watchdog, daemon=True)
    hb.start()
    wd.start()

    final_event: dict | None = None
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                # Non-JSON line (shouldn't happen in stream-json, but pass through)
                print(line, flush=True)
                continue
            if event.get("type") == "result":
                final_event = event
            _render_event(event, start=start)
    finally:
        stop_event.set()
        proc.wait()

    elapsed = time.monotonic() - start
    mins, secs = divmod(int(elapsed), 60)
    time_str = f"{mins}m{secs}s" if mins else f"{secs}s"

    if timed_out.is_set():
        print(f"\n⚠  Timeout after {int(elapsed)}s — Claude was killed")
        return 124

    rc = proc.returncode
    if rc == 0:
        print(f"\n✔  Claude finished in {time_str}")
        if final_event:
            cost = final_event.get("total_cost_usd")
            turns = final_event.get("num_turns")
            if cost is not None or turns is not None:
                bits = []
                if turns is not None:
                    bits.append(f"turns: {turns}")
                if cost is not None:
                    bits.append(f"cost: ${cost:.3f}")
                print("   " + ", ".join(bits))
    else:
        print(f"\n⚠  Claude exited with code {rc} after {time_str}")
    return rc


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
