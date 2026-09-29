---
title: Development
description: Test, link, and release the plugin.
---

## Test

```bash
python3 -m unittest -v
```

CI runs the tests on Ubuntu and macOS for every push to `main` and every pull request.

## Run a local checkout

```bash
herdr plugin uninstall conner.agent-queue   # if installed from GitHub
herdr plugin link "$PWD"
herdr plugin log list --plugin conner.agent-queue --limit 10
```

`plugin link` uses the checkout in place, so edits apply on the next action or event.

## Release

1. Bump `version` in `herdr-plugin.toml` and merge to `main`.
2. Tag and push:

   ```bash
   git tag -a v0.2.0 -m v0.2.0
   git push origin v0.2.0
   ```

The release workflow runs the tests, checks that the tag matches the manifest version, and publishes a GitHub release with install instructions.

## Docs

This site lives in `docs/` and is built with [Astro Starlight](https://starlight.astro.build). Pushes to `main` that touch `docs/` deploy it to GitHub Pages.

```bash
cd docs
npm ci
npm run dev
```
