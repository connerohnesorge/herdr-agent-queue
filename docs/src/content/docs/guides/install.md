---
title: Install
description: Install herdr-agent-queue and bind its keyboard shortcut.
---

## Requirements

- [herdr](https://herdr.dev) 0.8.0 or later
- `python3` on the `PATH` of the herdr server. The plugin uses the standard library only.
- macOS or Linux

## 1. Install the plugin

```bash
herdr plugin install connerohnesorge/herdr-agent-queue --ref v0.1.0
```

herdr shows a preview of the action, event hook, and popup the plugin registers. Confirm it, or pass `--yes` to skip the preview. Check the [releases page](https://github.com/connerohnesorge/herdr-agent-queue/releases) for the latest tag.

## 2. Bind a key

Plugins cannot register keybindings themselves. Add this to herdr's `config.toml` (`~/.config/herdr/config.toml` by default):

```toml
[[keys.command]]
key = "prefix+shift+q"
type = "plugin_action"
command = "conner.agent-queue.open"
description = "queue a prompt for the focused agent until its turn ends"
```

Any free key works. `prefix+q` is herdr's default detach key, so the example uses `prefix+shift+q`.

Reload the config:

```bash
herdr server reload-config
```

## 3. Check the install

```bash
herdr plugin list --json | grep conner.agent-queue
herdr plugin action list --plugin conner.agent-queue
```

The action list should show `open`. Then follow [Usage](/herdr-agent-queue/guides/usage/).

## Update

herdr has no `plugin update` command. Uninstall and install the new tag:

```bash
herdr plugin uninstall conner.agent-queue
herdr plugin install connerohnesorge/herdr-agent-queue --ref <tag>
```

Queued prompts live in herdr's plugin state directory and survive reinstalls.

## Uninstall

```bash
herdr plugin uninstall conner.agent-queue
```

Remove the keybinding from `config.toml`. To delete leftover queues, remove `~/.local/state/herdr/plugins/conner.agent-queue/`.
