---
title: How it works
description: The event, state, and delivery rules behind the queue.
---

The plugin is one Python file, `agent_queue.py`, registered through `herdr-plugin.toml`:

| Manifest entry | Command | Role |
| --- | --- | --- |
| Action `open` | `agent_queue.py open` | Checks the focused pane runs an agent, then opens the popup for it |
| Popup `compose` | `agent_queue.py compose` | Shows the queue, reads one prompt, saves it |
| Event `pane.agent_status_changed` | `agent_queue.py event` | Submits the next prompt when a turn ends |

## Storage

Each queue is a JSON list in herdr's plugin state directory, `~/.local/state/herdr/plugins/conner.agent-queue/<terminal-id>.json`. Queues are keyed by terminal id because herdr pane ids are renumbered when panes close. The file is deleted when the queue is empty.

## Delivery rules

On every `pane.agent_status_changed` event:

1. If the new status is not `done` or `idle`, do nothing.
2. Take a file lock, then read the pane's live status from `herdr pane list`. If it is no longer `done` or `idle`, stop.
3. Submit the first queued prompt with `herdr agent prompt <pane> <text> --wait --until working`.
4. Only after herdr confirms the agent is `working`, remove the prompt from the queue and update the sidebar count.

The lock plus the wait in step 3 stop two close events, such as `done` then `idle`, from submitting two prompts into one turn. If submission fails, the prompt stays queued and the error appears in the plugin log.

## Status meanings

| herdr status | Queue behavior |
| --- | --- |
| `working` | Hold |
| `blocked` | Hold. The agent is waiting on a permission prompt or question. |
| `done`, `idle` | Submit the next prompt |
| `unknown` | Hold |

## Sidebar indicator

The plugin reports a `queued` token on the pane with `herdr pane report-metadata`, showing `N queued`. It clears the token when the queue empties.
