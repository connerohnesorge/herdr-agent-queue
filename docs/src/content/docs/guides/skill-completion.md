---
title: Skill completion
description: Tab-complete Claude Code skills and commands in the queue popup.
---

When the focused pane runs Claude Code, the popup completes `/names` with `Tab`.

## Keys

- Type `/` and part of a name, then press `Tab`.
- One match completes the full name: `/Her` becomes `/Herdr`.
- Several matches complete their shared prefix. Press `Tab` again to list each match with its description.
- Completion works anywhere in the line: `run /Her` becomes `run /Herdr`.

```text
queue> /ponytail:ponytail
  /ponytail:ponytail         Forces the laziest solution that actually works...
  /ponytail:ponytail-audit   Whole-repo audit for over-engineering...
  /ponytail:ponytail-review  Code review focused exclusively on over-engineering...
```

## Where names come from

The popup reads the same places Claude Code loads skills and commands from:

| Source | Name |
| --- | --- |
| `~/.claude/skills/<dir>/SKILL.md` | `/<name>` from frontmatter, or the directory name |
| `~/.claude/commands/<path>.md` | `/<path>` with `/` replaced by `:`, for example `/spectr:apply` |
| `.claude/skills` and `.claude/commands` in the pane's working directory and each parent, up to your home directory | Same as above |
| Skills and commands of Claude Code plugins enabled in `~/.claude/settings.json` | `/<plugin>:<name>` |

Descriptions come from each file's `description` frontmatter.

Completion is only for Claude Code. Other agents get the plain prompt. Queue delivery works for every agent herdr tracks.
