#!/usr/bin/env python3
"""
forge_plan.py — FORGE PLAN phase: invoke an agent to produce a complete spec + task breakdown.

The prompt template lives in `forge/PLAN_PROMPT.md` (one source of truth). This script
substitutes the variables and feeds the result to the selected agent runner, streaming
progress events live.

After this command, the change is in REVIEW phase and ready for human approval.

Usage:
    python forge/forge_plan.py <change-id> "<short description>"
    python forge/forge_plan.py <change-id> "<short description>" --max-turns 30
    python forge/forge_plan.py <change-id> "<short description>" --agent codex
    python forge/forge_plan.py <change-id> --from-file <path/to/spec.md>
"""

import argparse
import json
import string
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from agent_runner import print_agent_result, resolve_agent, run_agent
except ModuleNotFoundError:
    from forge.agent_runner import print_agent_result, resolve_agent, run_agent

FORGE_DIR = Path("forge")
CHANGES_DIR = FORGE_DIR / "changes"
PROMPT_FILE = FORGE_DIR / "PLAN_PROMPT.md"


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
        print(
            f"❌ {PROMPT_FILE} is missing the '---' separator between header and prompt."
        )
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


def run_agent_plan(
    change_id: str,
    description: str,
    max_turns: int,
    timeout: int,
    agent: str,
    model: str | None,
    source_path: Path | None = None,
) -> int:
    """Invoke the selected agent with the planning prompt. Returns exit code."""
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

    print(f"\n🤖 Invoking {agent} (max-turns: {max_turns}, timeout: {timeout}s)")
    print("   Streaming progress (elapsed mm:ss):\n")

    result = run_agent(
        agent=agent,
        prompt=prompt,
        timeout=timeout,
        max_turns=max_turns,
        model=model,
        render_plan=True,
    )
    print_agent_result(agent, result)
    if result.final_event:
        cost = result.final_event.get("total_cost_usd")
        turns = result.final_event.get("num_turns")
        if cost is not None or turns is not None:
            bits = []
            if turns is not None:
                bits.append(f"turns: {turns}")
            if cost is not None:
                bits.append(f"cost: ${cost:.3f}")
            print("   " + ", ".join(bits))
    return result.exit_code


def print_next_steps(change_id: str, change_dir: Path) -> None:
    """Check final state and print what to do next."""
    state_file = change_dir / "state.json"
    if not state_file.exists():
        print("\n⚠  state.json not found — the agent may not have completed the plan.")
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
        print("    3. Execute: just forge")
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
        description="FORGE PLAN phase — invoke an agent to produce a complete spec",
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
        help="Max agent turns (default: 25 inline, 60 with --from-file)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Max seconds (default: 600 inline, 1800 with --from-file)",
    )
    parser.add_argument(
        "--agent",
        choices=("claude", "codex"),
        default=None,
        help="Agent runner to invoke (default: FORGE_AGENT or claude)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to pass through to the selected agent CLI",
    )
    args = parser.parse_args()
    agent = resolve_agent(args.agent)

    validate_change_id(args.change_id)

    if args.from_file and args.description:
        print("❌ Pass either a positional description OR --from-file, not both.")
        sys.exit(1)
    if not args.from_file and not args.description:
        print(
            "❌ Missing feature description. Pass it as a positional arg or use --from-file PATH."
        )
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
    print(f"   agent:       {agent}")
    print(f"   change:      {args.change_id}")
    print(f"   description: {desc_preview}")

    change_dir = create_change_dir(args.change_id)

    exit_code = run_agent_plan(
        args.change_id,
        description,
        max_turns,
        timeout,
        agent,
        args.model,
        source_path=source_path,
    )

    print_next_steps(args.change_id, change_dir)

    sys.exit(0 if exit_code == 0 else exit_code)


if __name__ == "__main__":
    main()
