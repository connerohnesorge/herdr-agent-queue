#!/usr/bin/env python3
"""Codex-style prompt queue: hold prompts until the agent's turn ends, then submit one per turn."""
import fcntl
import json
import os
import readline
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

HERDR = os.environ.get("HERDR_BIN_PATH", "herdr")
STATE = Path(os.environ["HERDR_PLUGIN_STATE_DIR"])
TURN_OVER = {"idle", "done"}
TOKEN = "queued"


def herdr(*args):
    result = subprocess.run([HERDR, *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"herdr {' '.join(args[:2])}: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def pane(pane_id):
    panes = json.loads(herdr("pane", "list"))["result"]["panes"]
    return next((p for p in panes if p["pane_id"] == pane_id), None)


# Pane ids compact when panes close; terminal ids stay with the agent's terminal.
def queue_path(info):
    return STATE / f"{info['terminal_id']}.json"


def load(info):
    try:
        return json.loads(queue_path(info).read_text())
    except FileNotFoundError:
        return []


def save(info, items):
    STATE.mkdir(parents=True, exist_ok=True)
    path = queue_path(info)
    if items:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items))
        tmp.replace(path)
    else:
        path.unlink(missing_ok=True)
    args = ["pane", "report-metadata", info["pane_id"], "--source", "conner.agent-queue"]
    if items:
        args += ["--token", f"{TOKEN}={len(items)} queued"]
    else:
        args += ["--clear-token", TOKEN]
    herdr(*args)


@contextmanager
def locked():
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / "queue.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def deliver(pane_id):
    """Submit the next queued prompt if the pane's agent has finished its turn."""
    with locked():
        info = pane(pane_id)
        if not info or not info.get("agent") or info["agent_status"] not in TURN_OVER:
            return
        items = load(info)
        if not items:
            return
        # Waiting for `working` under the lock stops a racing done->idle event from sending a second prompt.
        herdr("agent", "prompt", pane_id, items[0], "--wait", "--until", "working", "--timeout", "10000")
        save(info, items[1:])
        print(f"submitted to {pane_id}: {items[0]!r} ({len(items) - 1} left)")


def frontmatter(path):
    """Return (name, description) from a SKILL.md or command .md frontmatter."""
    meta = {}
    key = None
    lines = path.read_text(errors="replace").splitlines()
    if lines[:1] == ["---"]:
        for line in lines[1:]:
            if line == "---":
                break
            if line.startswith((" ", "\t")) and key:  # continuation of a `key: >` block
                meta[key] = f"{meta[key]} {line.strip()}".strip()
                continue
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip().strip('"')
            meta[key] = "" if value in (">", "|", ">-", "|-") else value
    return meta.get("name"), meta.get("description", "")


def claude_skills(cwd):
    """Map each invocable /name to its description, from the same places Claude Code loads skills."""
    home = Path.home() / ".claude"
    roots = [("", home)]
    project = Path(cwd)
    for parent in [project, *project.parents]:
        if parent == Path.home():
            break
        roots.append(("", parent / ".claude"))
    try:
        enabled = json.loads((home / "settings.json").read_text()).get("enabledPlugins", {})
        installed = json.loads((home / "plugins" / "installed_plugins.json").read_text())["plugins"]
        for key, installs in installed.items():
            if enabled.get(key):
                roots.append((key.split("@")[0] + ":", Path(installs[0]["installPath"])))
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass

    skills = {}
    for prefix, root in roots:
        for skill in (root / "skills").glob("*/SKILL.md"):
            name, description = frontmatter(skill)
            skills.setdefault(f"/{prefix}{name or skill.parent.name}", description)
        commands = root / "commands"
        for command in commands.rglob("*.md"):
            name = ":".join(command.relative_to(commands).with_suffix("").parts)
            skills.setdefault(f"/{prefix}{name}", frontmatter(command)[1])
    return skills


def enable_skill_completion(skills):
    names = sorted(skills)

    def complete(text, state):
        matches = [n for n in names if n.lower().startswith(text.lower())] if text.startswith("/") else []
        return matches[state] if state < len(matches) else None

    def show(substitution, matches, longest):
        print()
        for match in matches:
            print(f"  {match:<{longest + 2}}{skills[match][:80]}")
        print(f"queue> {readline.get_line_buffer()}", end="", flush=True)

    readline.set_completer(complete)
    readline.set_completer_delims(" \t\n")
    readline.set_completion_display_matches_hook(show)
    # macOS's stock python links libedit, which ignores GNU readline binding syntax.
    if "libedit" in (readline.__doc__ or ""):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")


def open_popup():
    pane_id = os.environ["HERDR_PANE_ID"]
    info = pane(pane_id)
    if not info or not info.get("agent"):
        raise SystemExit(f"{pane_id} is not running a recognized agent")
    herdr("plugin", "pane", "open", "--plugin", os.environ["HERDR_PLUGIN_ID"],
          "--entrypoint", "compose", "--env", f"AGENT_QUEUE_PANE={pane_id}")


def compose():
    pane_id = os.environ["AGENT_QUEUE_PANE"]
    info = pane(pane_id)
    if not info:
        raise SystemExit(f"{pane_id} is gone")
    items = load(info)
    print(f"Queue for {info['agent']} in {pane_id} ({info['agent_status']})")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")
    if info["agent"] == "claude":
        enable_skill_completion(claude_skills(info.get("foreground_cwd") or info["cwd"]))
    print("Enter queues · tab completes /skills · empty line cancels · :clear empties the queue\n")
    try:
        text = input("queue> ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not text:
        return
    with locked():
        info = pane(pane_id)
        items = [] if text == ":clear" else load(info) + [text]
        save(info, items)
    deliver(pane_id)


def add(pane_id, text):
    """Queue text for a pane without the popup (scripts and tests)."""
    with locked():
        info = pane(pane_id)
        if not info or not info.get("agent"):
            raise SystemExit(f"{pane_id} is not running a recognized agent")
        save(info, load(info) + [text])
    deliver(pane_id)


def event():
    data = json.loads(os.environ["HERDR_PLUGIN_EVENT_JSON"])["data"]
    if data.get("agent_status") in TURN_OVER:
        deliver(data["pane_id"])


if __name__ == "__main__":
    commands = {"open": open_popup, "compose": compose, "event": event}
    if len(sys.argv) == 4 and sys.argv[1] == "add":
        add(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2 and sys.argv[1] in commands:
        commands[sys.argv[1]]()
    else:
        raise SystemExit("usage: agent_queue.py open|compose|event|add <pane> <text>")
