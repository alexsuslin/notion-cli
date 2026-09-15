---
name: notion-cli-agent
description: Config-backed automation skill for this repository's Notion CLI wrapper. Use when Codex should operate Notion through `notion-cli` instead of hardcoding datasource IDs, workspace IDs, or raw `ntn` command details in prompts, especially for resolving aliases, dry-running commands, safe read-only queries, or YouTube metadata enrichment.
---

# Notion CLI Agent

Use this skill to operate Notion through the local `notion-cli` project instead of
embedding private workspace settings or raw API details into prompts.

## Workflow

1. Read `references/agent-cli.md` for the command contract.
2. Read `references/configuration.md` when the task depends on datasources, bundles,
   presets, workspaces, or local config layout.
3. Prefer `notion-cli ... --dry-run` before any live command. Use global
   `notion-cli --dry-run-json ...` for a structured plan; this never invokes `ntn`.
   For queries, use `--filter`, repeatable `--sort`, `--page-size`, and explicit
   `--all` when every available page is needed. Use `datasource schema <alias>
   --check` for a read-only check of property mappings before writes when needed.
   Put global `--timeout` before the command; timed-out writes are not retried.
4. Use `item set <page-alias|UUID|Notion-URL> --author "Name" --dry-run` for focused
   corrections. It changes only supplied fields, uses `--datasource items` by
   default, and does not fetch YouTube metadata. Use `item add-youtube --author`
   when overriding metadata during creation or upsert.
5. Treat `preset run`, `item set`, and `item add-youtube` as write operations
   unless the user clearly asked for mutation.
6. Keep private IDs only in the ignored local `notion-cli.toml`; use
   `notion-cli.example.toml` for tracked examples.

## Maintenance Rules

- Update `references/agent-cli.md` when commands, flags, or execution behavior change.
- Update `references/configuration.md` when config schema or examples change.
- Keep `docs/skill.md`, `docs/agent-cli.md`, `README.md`, and `AGENTS.md` aligned with
  this skill.
