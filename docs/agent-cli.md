# Agent CLI Guide

Use [skills/notion-cli-agent/references/agent-cli.md](../skills/notion-cli-agent/references/agent-cli.md)
as the canonical guide for agent usage.

Quick reminders:

- config lookup now prefers `--config`, then `NOTION_CLI_CONFIG`, then `./notion-cli.toml`, then the user config directory
- prefer config-backed aliases over raw IDs
- prefer `--dry-run` before live execution
- keep write operations explicit and user-approved
- legacy database queries pin `--notion-version 2022-06-28` unless the datasource config uses `query_endpoint = "data_source"`
- upsert Link filters and create/update property values render as JSON input so URLs with `?v=...`, spaces, and unicode survive `ntn api` parsing
- use `[datasources.<alias>.property_types]` when the local Notion schema uses `select` or `multi_select` where the defaults differ
- YouTube enrichment uses `yt-dlp` by default and falls back to `YOUTUBE_API_KEY` when available
- use `notion-cli item add-youtube ... --dry-run` for the first-class YouTube item workflow

- use `item set <page-alias|UUID|Notion-URL> --author "Name" --dry-run` for focused corrections; `--datasource` defaults to `items`
- `item set` changes only explicit fields and never enriches metadata; `--tags ""` clears tags
- use `item add-youtube --author "Name"` to override the inferred author on creation/upsert
- Notion URLs with `?p=<page-id>` select the opened page; malformed targets fail before execution
- modern `data_source` aliases create pages under `data_source_id`; invalid upsert results stop before writing
- dry-run output is an argument preview, not shell-escaped executable text; environment overrides are not printed
- configuration/domain errors go to stderr with exit code 1; invalid CLI arguments use exit code 2

- query flags: `--filter JSON`, repeatable `--sort FIELD:asc|desc`, `--page-size 1..100`, `--start-cursor`, `--all`
- `--all` preserves request parameters and fails without partial output on invalid/incomplete responses or cursor cycles
- `datasource schema <alias> --check` is read-only and reports mapped name/type mismatches as JSON with exit code 1
- global `--dry-run-json` goes before the subcommand and includes args, allowlisted env, timeout, and upsert branches
- global `--timeout` overrides `[notion].timeout_seconds` (default 60); the limit applies per `ntn` call and no retries occur
