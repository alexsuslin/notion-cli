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
