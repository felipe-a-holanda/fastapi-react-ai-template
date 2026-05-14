#!/usr/bin/env python3
"""Agent subprocess adapters for FORGE.

The FORGE protocol is agent-neutral, but the automation needs to invoke a
specific CLI. This module keeps those CLI details out of forge_plan.py and
forge_run.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

HEARTBEAT_INTERVAL = 30
RATE_LIMIT_NEEDLE = "you've hit your limit"

DEFAULT_MODELS = {
    ("claude", "plan"): "claude-opus-4-7",
    ("claude", "execute"): "claude-sonnet-4-6",
    ("codex", "plan"): "gpt-5.5",
    ("codex", "execute"): "gpt-5.3-codex",
}

MODEL_ENV_VARS = {
    ("claude", "plan"): "FORGE_CLAUDE_PLAN_MODEL",
    ("claude", "execute"): "FORGE_CLAUDE_EXEC_MODEL",
    ("codex", "plan"): "FORGE_CODEX_PLAN_MODEL",
    ("codex", "execute"): "FORGE_CODEX_EXEC_MODEL",
}


@dataclass
class AgentResult:
    exit_code: int
    elapsed: float
    usage: dict | None = None
    hit_rate_limit: bool = False
    final_event: dict | None = None
    timed_out: bool = False


def resolve_agent(agent: str | None) -> str:
    selected = (agent or os.environ.get("FORGE_AGENT") or "claude").strip().lower()
    if selected not in {"claude", "codex"}:
        print(f"❌ Unsupported FORGE agent: {selected}")
        print("   Supported agents: claude, codex")
        sys.exit(1)
    return selected


def resolve_model(agent: str, phase: str, model: str | None) -> str:
    if model:
        return model
    env_var = MODEL_ENV_VARS[(agent, phase)]
    return os.environ.get(env_var) or DEFAULT_MODELS[(agent, phase)]


def build_command(
    agent: str, prompt: str, max_turns: int, model: str | None
) -> list[str]:
    if agent == "claude":
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--max-turns",
            str(max_turns),
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["-p", prompt])
        return cmd

    cmd = [
        "codex",
        "exec",
        "--json",
        "--sandbox",
        "danger-full-access",
        "--ask-for-approval",
        "never",
        "-C",
        str(Path.cwd()),
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def build_env(agent: str) -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_PAGER"] = "cat"

    if agent == "claude":
        # Claude CLI prefers ANTHROPIC_API_KEY over OAuth credentials. Long
        # FORGE runs should use the logged-in Claude Code account by default.
        env.pop("ANTHROPIC_API_KEY", None)
    else:
        # Codex may run in a sandbox where /run/user/$UID is read-only.
        env["XDG_RUNTIME_DIR"] = os.environ.get("FORGE_XDG_RUNTIME_DIR", "/tmp")

    return env


def _format_elapsed(elapsed: float) -> str:
    mins, secs = divmod(int(elapsed), 60)
    return f"{mins}m{secs}s" if mins else f"{secs}s"


def _summarize_tool_input(name: str, inp: dict) -> str:
    if name in ("Read", "Edit"):
        return str(inp.get("file_path", "?")).replace(str(Path.cwd()) + "/", "")
    if name == "Write":
        path = str(inp.get("file_path", "?")).replace(str(Path.cwd()) + "/", "")
        size = len(inp.get("content", "") or "")
        size_s = f"{size / 1024:.1f}KB" if size >= 1024 else f"{size}B"
        return f"{path} ({size_s})"
    if name == "Bash":
        cmd = (inp.get("command") or "").splitlines()[0] if inp.get("command") else ""
        return cmd[:100]
    if name in ("Glob", "Grep"):
        return inp.get("pattern", "?")
    if name == "TodoWrite":
        return f"{len(inp.get('todos') or [])} todo(s)"
    bits = []
    for k, v in list(inp.items())[:2]:
        sv = str(v)
        bits.append(f"{k}={sv[:57] + '...' if len(sv) > 60 else sv}")
    return ", ".join(bits)


def _extract_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_extract_text(v) for v in value)
    if not isinstance(value, dict):
        return ""

    if isinstance(value.get("content"), list):
        return "".join(_extract_text(v) for v in value["content"])
    for key in ("text", "delta", "content", "message", "output"):
        text = value.get(key)
        if isinstance(text, str):
            return text
    for key in ("item", "event", "data"):
        text = _extract_text(value.get(key))
        if text:
            return text
    return ""


def render_plan_event(agent: str, event: dict, *, start: float) -> None:
    """Print a concise progress line for an agent event."""
    if agent == "claude":
        if event.get("type") != "assistant":
            return
        msg = event.get("message") or {}
        for block in msg.get("content") or []:
            bt = block.get("type")
            if bt == "tool_use":
                name = block.get("name", "?")
                summary = _summarize_tool_input(name, block.get("input") or {})
                mins, secs = divmod(int(time.monotonic() - start), 60)
                print(f"  [{mins:02d}:{secs:02d}] {name:<10} {summary}", flush=True)
            elif bt == "text":
                text = (block.get("text") or "").strip()
                if text:
                    print(f"         · {text.splitlines()[0][:140]}", flush=True)
        return

    et = str(event.get("type") or "")
    text = _extract_text(event).strip()
    if text:
        print(f"         · {text.splitlines()[0][:140]}", flush=True)
    elif et:
        mins, secs = divmod(int(time.monotonic() - start), 60)
        print(f"  [{mins:02d}:{secs:02d}] {et}", flush=True)


def _update_result_from_event(agent: str, event: dict, result: AgentResult) -> None:
    if agent == "claude" and event.get("type") == "result":
        result.final_event = event
        usage = event.get("usage") or {}
        result.usage = {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
        }
        return

    if agent == "codex":
        if event.get("type") in {"result", "session.completed", "turn.completed"}:
            result.final_event = event
        usage = event.get("usage")
        if isinstance(usage, dict):
            result.usage = usage


def run_agent(
    *,
    agent: str,
    prompt: str,
    timeout: int,
    max_turns: int,
    model: str | None = None,
    log_path: Path | None = None,
    render_plan: bool = False,
) -> AgentResult:
    """Run an agent CLI and normalize the result."""
    start = time.monotonic()
    result = AgentResult(exit_code=1, elapsed=0)
    cmd = build_command(agent, prompt, max_turns, model)
    env = build_env(agent)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env,
        )
    except FileNotFoundError:
        print(f"\n✗ '{cmd[0]}' not found. Is it installed and in PATH?")
        sys.exit(1)

    stop_event = threading.Event()
    timed_out = threading.Event()

    def heartbeat() -> None:
        while not stop_event.wait(HEARTBEAT_INTERVAL):
            mins, secs = divmod(int(time.monotonic() - start), 60)
            print(
                f"  ⏳ {agent} still running... {mins}m{secs}s elapsed (timeout at {timeout}s)",
                file=sys.stderr,
                flush=True,
            )

    def watchdog() -> None:
        if not stop_event.wait(timeout):
            timed_out.set()
            try:
                proc.kill()
            except ProcessLookupError:
                pass

    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()

    log_handle: TextIO | None = None
    jsonl_handle: TextIO | None = None
    try:
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = open(log_path, "a", buffering=1)
            jsonl_handle = open(log_path.with_suffix(".jsonl"), "a", buffering=1)
            marker = json.dumps(
                {
                    "_forge_marker": "iteration_started",
                    "agent": agent,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
            )
            log_handle.write(
                f"\n\n=== iteration started {datetime.now().isoformat()} ({agent}) ===\n"
            )
            jsonl_handle.write(marker + "\n")

        assert proc.stdout is not None
        for line in proc.stdout:
            if jsonl_handle is not None:
                jsonl_handle.write(line if line.endswith("\n") else line + "\n")

            stripped = line.rstrip("\n")
            if not stripped:
                continue

            try:
                event = json.loads(stripped)
            except json.JSONDecodeError:
                if log_handle is not None:
                    log_handle.write(stripped + "\n")
                print(stripped, flush=True)
                continue

            _update_result_from_event(agent, event, result)
            text = _extract_text(event)
            if text and RATE_LIMIT_NEEDLE in text.lower():
                result.hit_rate_limit = True

            if render_plan:
                render_plan_event(agent, event, start=start)
            elif text:
                sys.stdout.write(text)
                sys.stdout.flush()
                if log_handle is not None:
                    log_handle.write(text)
    finally:
        stop_event.set()
        proc.wait()
        if log_handle is not None:
            log_handle.close()
        if jsonl_handle is not None:
            jsonl_handle.close()

    result.elapsed = time.monotonic() - start
    result.timed_out = timed_out.is_set()
    result.exit_code = 124 if timed_out.is_set() else proc.returncode
    return result


def print_agent_result(agent: str, result: AgentResult) -> None:
    time_str = _format_elapsed(result.elapsed)
    if result.exit_code == 124:
        print(f"\n  ⚠  TIMEOUT after {time_str} — {agent} was killed")
    elif result.exit_code != 0:
        print(f"\n  ⚠  {agent} exited with code {result.exit_code} after {time_str}")
    else:
        print(f"\n  ✔  {agent} finished in {time_str}")
