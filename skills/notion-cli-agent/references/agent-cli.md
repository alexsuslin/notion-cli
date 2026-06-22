# Agent CLI Guide

This is the canonical guide for agents that use `notion-cli-agent`.

## Purpose

Use the local `notion-cli` wrapper instead of embedding raw Notion datasource IDs,
workspace IDs, or ad hoc `ntn` argument strings into prompts. The CLI keeps local
configuration in `notion-cli.toml` and exposes a small set of repeatable commands.

## Configuration Sources

The CLI reads project structure from a TOML file.

Preferred usage:

```bash
notion-cli --config notion-cli.toml <command>
```

Default behavior:

- if `--config` is omitted, the CLI looks for `./notion-cli.toml`
- `notion-cli.toml` is local and ignored
- `notion-cli.example.toml` is the public template that should stay safe to commit

Authentication for live `ntn api` calls can come from:

- `ntn login`
- `NOTION_API_TOKEN` in the environment

## Execution Mode

Prefer `--dry-run` first:

```bash
notion-cli datasource query items --dry-run
notion-cli preset run add_youtube --url https://youtu.be/example --dry-run
```

`--dry-run` prints the resolved `ntn` command. Use that output to inspect aliases,
workspace env vars, and encoded properties before any live execution.

Treat these commands as read-only by default:

- `doctor`
- `api v1/users/me`
- `datasource query <alias>`

Treat `preset run <name>` as a write operation because it renders a `v1/pages`
creation request.

## Commands

### `login`

Starts standard `ntn` authentication.

```bash
notion-cli login
```

### `doctor`

Checks the local Notion CLI installation.

```bash
notion-cli doctor
notion-cli doctor --dry-run
```

### `api`

Passes raw `ntn api` arguments through the wrapper.

```bash
notion-cli api --dry-run v1/users/me
notion-cli api v1/users/me
```

Use this for safe read-only endpoints when there is no higher-level wrapper command yet.

### `exec`

Passes raw `ntn` subcommands through the wrapper.

```bash
notion-cli exec --dry-run whoami
```

Use sparingly; prefer dedicated wrapper commands when available.

### `resolve datasource`

Returns the concrete datasource ID for a named alias.

```bash
notion-cli resolve datasource items
```

The output is the ID only.

### `resolve preset`

Returns the preset's resolved datasource ID when present.

```bash
notion-cli resolve preset add_item
```

### `datasource query`

Runs a query against a configured datasource alias.

```bash
notion-cli datasource query items --dry-run
notion-cli datasource query items
```

### `preset run`

Resolves a named preset into a `v1/pages` create call.

```bash
notion-cli preset run add_item --title "Inbox item" --dry-run
```

If the preset has `youtube = true`, `--url` is required and the CLI fills:

- title
- canonical YouTube URL
- duration

Example:

```bash
notion-cli preset run add_youtube --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

## YouTube Metadata

The repository intentionally prefers a no-key flow.

- provider: `no_key`
- implementation: `yt-dlp`
- fields collected: title, canonical URL, duration

No YouTube API key is required for the default enrichment path.

## Recommended Agent Behavior

- prefer datasource aliases and presets over raw IDs
- keep write operations explicit
- inspect `--dry-run` output before live mutation
- do not commit local `notion-cli.toml`
- if a needed wrapper command is missing, add it to the CLI instead of teaching the
  agent raw Notion payload shapes
