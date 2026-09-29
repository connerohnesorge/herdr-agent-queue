---
title: Usage
description: Queue prompts from the popup and watch them submit turn by turn.
---

## Queue a prompt

1. Focus a pane running a coding agent.
2. Press `prefix+shift+q` (or the key you bound during [install](/herdr-agent-queue/guides/install/)).
3. Type the prompt and press `Enter`.

The popup shows the agent, its pane, its current status, and anything already queued:

```text
Queue for claude in w1:p3 (working)
  1. Run the test suite and fix failures
Enter queues · tab completes /skills · empty line cancels · :clear empties the queue

queue> Then update the changelog
```

If the agent is `working`, the prompt waits. If the agent is already `idle` or `done`, it is submitted immediately.

## Popup keys

| Input | Effect |
| --- | --- |
| `Enter` | Add the prompt to the end of the queue |
| `Tab` | Complete a `/skill` name (Claude Code panes). See [Skill completion](/herdr-agent-queue/guides/skill-completion/) |
| Empty line, `Ctrl+C`, or `Ctrl+D` | Close without queueing |
| `:clear` | Empty this pane's queue |

The popup accepts one line per prompt. Open it again to queue more.

## What happens next

- herdr's sidebar shows `N queued` on the pane while prompts are waiting.
- When the agent's turn ends, the first prompt is submitted as a new user message. The agent starts a new turn.
- When that turn ends, the next prompt goes. The queue drains one prompt per turn, in order.
- If the agent stops on a permission prompt or a question (`blocked`), nothing is submitted. Answer it and the queue continues when the turn ends.

## Example

You ask Claude to refactor a module. While it works, you queue two prompts:

1. `Run the tests and fix anything that broke`
2. `/simplify`

Claude finishes the refactor. The plugin submits prompt 1 as its own turn. When that turn ends, it submits `/simplify`. The refactor turn never saw either prompt.

## Queue from a script

The popup is the normal path. Scripts can queue directly:

```bash
ROOT=$(herdr plugin list --json | python3 -c 'import sys,json; print(next(p["plugin_root"] for p in json.load(sys.stdin)["result"]["plugins"] if p["plugin_id"]=="conner.agent-queue"))')
HERDR_PLUGIN_STATE_DIR=~/.local/state/herdr/plugins/conner.agent-queue \
  python3 "$ROOT/agent_queue.py" add <pane-id> "Run the tests"
```
