# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

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
