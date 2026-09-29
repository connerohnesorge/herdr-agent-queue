---
title: Troubleshooting
description: Diagnose a queue that does not open or does not submit.
---

## Read the plugin log

Every event and action run is logged, including what was submitted:

```bash
herdr plugin log list --plugin conner.agent-queue --limit 10
```

A successful delivery logs `submitted to <pane>: '<prompt>' (N left)`.

## The key does nothing

- Check the binding points to `conner.agent-queue.open` and run `herdr server reload-config`.
- The focused pane must run an agent herdr recognizes. Check with `herdr pane list` and look for an `agent` field on the pane. Otherwise the action exits with `<pane> is not running a recognized agent`.
- Another herdr popup may already be open. Close it and retry.

## A prompt stays queued

- Check the agent status with `herdr pane list`. Prompts only go when the status is `done` or `idle`.
- A `blocked` agent holds the queue. Answer its prompt.
- Look in the plugin log for a failed `herdr agent prompt`.
- Inspect the raw queue in `~/.local/state/herdr/plugins/conner.agent-queue/`.

## A prompt was submitted mid-turn

Delivery trusts herdr's status detection. If herdr reports `done` before the agent's turn has really ended, the prompt goes early. Report it to herdr with the agent version.

## Limitations

- One line per prompt.
- Queues for closed panes are not cleaned up. Delete their files from the state directory.
- Skill completion covers Claude Code only.
