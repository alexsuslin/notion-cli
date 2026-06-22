# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added

- optional `query_endpoint` and `notion_version` datasource config to distinguish legacy database queries from `data_source` queries
- `youtube.provider = "api_key"` mode for explicit YouTube Data API enrichment
- optional `[datasources.<alias>.property_types]` overrides for local Notion schema differences

### Changed

- legacy database query and preset-backed page commands now render `--notion-version 2022-06-28` by default
- YouTube enrichment now falls back to the YouTube Data API when `yt-dlp` fails and `YOUTUBE_API_KEY` is available
- `item add-youtube --upsert` now renders the Link filter as JSON input so canonical YouTube URLs survive `ntn api` parsing

## [0.2.0] - 2026-06-22

### Added

- first-class `item add-youtube` workflow with score, project alias, tags, done/date, and upsert dry-run support
- `resolve page` command for config-backed relation targets

### Changed

- config lookup now checks `--config`, `NOTION_CLI_CONFIG`, the local working tree, and the user config directory
- datasource query and page create rendering now target legacy database IDs through `ntn api`

## [0.1.0] - 2026-06-22

### Added

- Python package scaffold for a config-driven wrapper around the official Notion CLI
- `notion-cli.example.toml` template for named datasources, bundles, and presets
- dry-run support for passthrough and config-backed commands
- read-only datasource query flow verified against a live Notion data source
- no-key YouTube metadata enrichment for title, URL, and duration
- Windows-safe `ntn` subprocess resolution for npm-installed shims
- test suite covering config, resolver, rendering, execution, CLI, and YouTube helpers
- CI workflow for tests, lint, and type checks
- release workflow that builds artifacts and publishes release notes from the changelog
- in-repository Codex skill layer with `SKILL.md`, `agents/openai.yaml`, and agent references

### Changed

- private workspace and datasource IDs now stay only in the ignored local `notion-cli.toml`
