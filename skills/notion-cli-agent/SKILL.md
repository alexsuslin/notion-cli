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
3. Prefer `notion-cli ... --dry-run` before any live command.
4. Treat `preset run` as a write operation unless the user clearly asked for mutation.
5. Keep private IDs only in the ignored local `notion-cli.toml`; use
   `notion-cli.example.toml` for tracked examples.

## Maintenance Rules

- Update `references/agent-cli.md` when commands, flags, or execution behavior change.
- Update `references/configuration.md` when config schema or examples change.
- Keep `docs/skill.md`, `docs/agent-cli.md`, `README.md`, and `AGENTS.md` aligned with
  this skill.
