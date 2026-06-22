# notion-cli

`notion-cli` is a Python wrapper around the official Notion CLI, `ntn`.
It keeps datasource IDs, presets, and reusable field mappings in project
configuration instead of hardcoding them in PowerShell or ad hoc shell commands.

## What It Does

- wraps standard `ntn` commands like `api`, `doctor`, and `login`
- resolves named datasources from `notion-cli.toml`
- supports dry-run output for safe inspection before live execution
- enriches YouTube presets with title, canonical URL, and duration
- works with `NOTION_API_TOKEN` so read-only automation does not require local keychain setup

## Requirements

- Python 3.11+
- `ntn` installed and available on `PATH` for live execution

On Windows, the official Notion docs currently support:

```powershell
winget install Notion.ntn
```

Or with npm:

```powershell
npm install --global ntn
```

## Install

```bash
python -m pip install -e .[dev]
```

## Authenticate

Interactive login:

```bash
ntn login
```

Or provide a token for scripts:

```bash
set NOTION_API_TOKEN=ntn_xxx
```

## Configure

Copy one of the examples:

- `config/examples/minimal.toml`
- `config/examples/youtube.toml`
- `notion-cli.example.toml`

Then create your local private config:

```bash
cp notion-cli.example.toml notion-cli.toml
```

`notion-cli.toml` is intentionally ignored and should contain your private IDs,
workspace-specific aliases, and local defaults. Do not commit real Notion IDs,
tokens, or personal workspace mappings to the repository.

## Examples

Resolve a datasource alias:

```bash
notion-cli resolve datasource items
```

Inspect a safe API call without executing it:

```bash
notion-cli api --dry-run v1/users/me
```

Run a config-backed datasource query:

```bash
notion-cli datasource query items --dry-run
```

Run a YouTube preset:

```bash
notion-cli preset run add_youtube --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

## Agent Skill

This repository now includes a real Codex skill layer for agent-safe usage:

- `skills/notion-cli-agent/SKILL.md`
- `skills/notion-cli-agent/agents/openai.yaml`
- `skills/notion-cli-agent/references/`
- `docs/skill.md`
- `docs/agent-cli.md`

Use the skill when an agent should resolve datasource aliases, inspect `ntn`
commands with `--dry-run`, or run read-only Notion queries without hardcoding
workspace-specific IDs in prompts.

## Development

Run the full local quality gate:

```bash
pytest -q
ruff check .
mypy src
```

## Releases

- `CHANGELOG.md` is the source of truth for release notes.
- Git tags use the `vX.Y.Z` format.
- GitHub Actions builds release artifacts from tags and publishes release notes from the changelog.
