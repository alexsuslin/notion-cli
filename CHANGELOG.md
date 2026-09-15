# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added

- datasource query filters, repeatable property sorts, page size, cursors, and complete-result `--all` pagination
- global `--dry-run-json` with versioned argument/env/timeout plans, including conditional upsert branches
- configurable per-call `ntn` timeout via `[notion].timeout_seconds` and global `--timeout`
- read-only `datasource schema --check` for configured property names and types
- CI matrix for Ubuntu/Windows and Python 3.12/3.14, with real subprocess transport and timeout tests

- `item set` for focused property updates with datasource mappings, aliases, page UUIDs, Notion URLs, and offline dry-run support (issue #14)
- `item add-youtube --author` to override the inferred author

### Fixed

- decode `ntn` output as UTF-8 to preserve Unicode on Windows

- use `data_source_id` parents when creating pages for modern datasource aliases
- reject malformed upsert query results before creating duplicate items
- report configuration and domain errors on stderr with a nonzero exit code

## [0.2.2] - 2026-07-03

### Changed

- require Python 3.12 and update CI/release workflows to run on Python 3.12
- render Notion page create/update property values as JSON input so URLs, titles with spaces, and unicode values survive `ntn api` inline parsing

### Fixed

- reject page-create presets that do not resolve to a datasource instead of rendering `parent[database_id]=None`

## [0.2.1] - 2026-06-25

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
