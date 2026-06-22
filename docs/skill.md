# Skill Notes

Use [skills/notion-cli-agent/SKILL.md](../skills/notion-cli-agent/SKILL.md) as the
canonical skill definition for this repository.

This file stays intentionally short for repo-level discovery:

- prefer the in-repo skill instead of embedding raw Notion API details in prompts
- keep private workspace IDs, datasource IDs, bundles, and presets in local `notion-cli.toml`
- use `notion-cli ... --dry-run` before any live command that could mutate Notion content
- update `skills/notion-cli-agent/`, [agent-cli.md](agent-cli.md), `README.md`, and `AGENTS.md`
  together when agent-facing behavior changes
