# Agent CLI Guide

Use [skills/notion-cli-agent/references/agent-cli.md](../skills/notion-cli-agent/references/agent-cli.md)
as the canonical guide for agent usage.

Quick reminders:

- config lookup now prefers `--config`, then `NOTION_CLI_CONFIG`, then `./notion-cli.toml`, then the user config directory
- prefer config-backed aliases over raw IDs
- prefer `--dry-run` before live execution
- keep write operations explicit and user-approved
- YouTube enrichment uses `yt-dlp` and does not require an API key
- use `notion-cli item add-youtube ... --dry-run` for the first-class YouTube item workflow
