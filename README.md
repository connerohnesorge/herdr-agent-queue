# herdr-agent-queue

A [herdr](https://herdr.dev) plugin that queues prompts for a coding agent and submits each one as a new turn after the current turn ends, like Codex's queue, instead of folding them into the running turn.

Claude Code folds messages typed during a turn into that turn. Sometimes you want the opposite: finish what you're doing, then do this next. Related requests: [anthropics/claude-code#50246](https://github.com/anthropics/claude-code/issues/50246), [#63190](https://github.com/anthropics/claude-code/issues/63190), [#73661](https://github.com/anthropics/claude-code/issues/73661), [#87656](https://github.com/anthropics/claude-code/issues/87656).

## Requirements

- herdr ≥ 0.8.0
- `python3` (standard library only)

## Install

```bash
herdr plugin install connerohnesorge/herdr-agent-queue --ref v0.1.0
```

Then bind the action in herdr's `config.toml` and run `herdr server reload-config`:

```toml
[[keys.command]]
key = "prefix+shift+q"
type = "plugin_action"
command = "conner.agent-queue.open"
description = "queue a prompt for the focused agent until its turn ends"
```

To update, reinstall: `herdr plugin uninstall conner.agent-queue && herdr plugin install connerohnesorge/herdr-agent-queue --ref <tag>`. Queued prompts survive reinstalls.

## Use

Focus an agent pane and press `prefix+shift+q`. A popup shows the pane's queue and a `queue>` prompt.

- `Enter` queues the prompt. If the agent is already idle, it is submitted immediately.
- `Tab` completes `/skills` and `/commands` for Claude Code panes and lists matches with descriptions.
- An empty line cancels. `:clear` empties the queue.

The sidebar shows `N queued` on panes with waiting prompts.

## How it works

- Prompts are stored per terminal under herdr's plugin state directory, so they survive herdr pane id changes.
- On `pane.agent_status_changed` to `done` or `idle`, the plugin submits the first queued prompt with `herdr agent prompt` and waits until the agent reports `working`. The next prompt goes after the next turn ends. One prompt is one turn.
- A `blocked` agent (permission prompt, question) never receives a queued prompt.
- If submission fails, the prompt stays queued.

Delivery works for any agent herdr tracks. Skill completion reads the places Claude Code loads skills from: `~/.claude/skills`, `~/.claude/commands`, `.claude/` in the pane's working directory and its parents, and enabled Claude Code plugins.

## Limitations

- Delivery depends on herdr's agent status detection. If herdr reports a turn as finished early, the next prompt is submitted early.
- Prompts are single-line.
- Queues for closed panes are not cleaned up automatically. They live in `~/.local/state/herdr/plugins/conner.agent-queue/`.

## Development

```bash
python3 -m unittest -v
herdr plugin link "$PWD"
herdr plugin log list --plugin conner.agent-queue --limit 10
```

Queue without the popup, for scripts: `HERDR_PLUGIN_STATE_DIR=~/.local/state/herdr/plugins/conner.agent-queue python3 agent_queue.py add <pane-id> "<prompt>"`.

Releases: bump `version` in `herdr-plugin.toml`, then push a matching `v<version>` tag. The release workflow runs the tests and publishes the GitHub release.

## License

MIT
