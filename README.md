# notion-cli

`notion-cli` is a Python wrapper around the official Notion CLI, `ntn`.
It keeps datasource IDs, presets, and reusable field mappings in project
configuration instead of hardcoding them in PowerShell or ad hoc shell commands.

## What It Does

- wraps standard `ntn` commands like `api`, `doctor`, and `login`
- resolves named datasources from `notion-cli.toml`
- supports text dry-run and versioned JSON execution plans
- queries datasources with filters, sorting, cursor pagination, and an explicit `--all` mode
- inspects remote schemas and checks configured property mappings
- applies configurable timeouts to `ntn` calls
- pins legacy database queries to Notion API version `2022-06-28` unless you opt into `data_source` queries
- supports datasource-level property type overrides so local schemas can map fields like `Author` and `Status` correctly
- enriches YouTube presets with title, canonical URL, duration, and channel/author
- updates individual item properties with `item set`, using a page alias, UUID, or Notion URL
- provides a first-class `item add-youtube` workflow with score, tags, project aliases, and upsert dry-run support
- works with `NOTION_API_TOKEN` so read-only automation does not require local keychain setup

## Requirements

- Python 3.12+
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
mkdir -p ~/.config/notion-cli
cp notion-cli.example.toml ~/.config/notion-cli/notion-cli.toml
```

Config lookup order:

1. `--config <path>`
2. `NOTION_CLI_CONFIG`
3. `./notion-cli.toml`
4. `$XDG_CONFIG_HOME/notion-cli/notion-cli.toml` or `~/.config/notion-cli/notion-cli.toml`

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

Legacy database aliases now render with an explicit Notion version:

```bash
ntn api --notion-version 2022-06-28 -X POST v1/databases/<id>/query
```

Run a YouTube preset:

```bash
notion-cli preset run add_youtube --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

Run the first-class YouTube item workflow:

```bash
notion-cli item add-youtube https://youtu.be/dQw4w9WgXcQ --score 4 --project sci_pop --tags sci-pop,youtube --dry-run
```

Preview the upsert query and update/create plan:

```bash
notion-cli item add-youtube https://youtu.be/dQw4w9WgXcQ --score 4 --done --upsert --dry-run
```

The upsert query renders the Link filter as compact JSON, and create/update
property values render as `path:=json`, so canonical YouTube URLs with `?v=...`, titles with spaces, and unicode values do not break inline `ntn api` parsing.

## Correct an Existing Item

Update only the author, using your configured property name and type:

```bash
notion-cli item set saved_video --author "Matt Pocock" --dry-run
```

`saved_video` is an alias from `[pages]`. You can also supply a page UUID or an
HTTPS link on `notion.so` / `notion.site`; links with `?p=<page-id>` select that
page. Property mappings come from `--datasource items` by default. Use
`--datasource <alias>` for another configured schema.

Supported fields: `--author`, `--title`, `--status`, `--score` (1–5), `--tags`,
`--date` (YYYY-MM-DD or `today`), and `--project` (a configured page alias).
Only supplied fields change. Tags replace the existing list; `--tags ""` clears
it. Setting a status does not implicitly change the date. Missing property
mappings and empty updates are rejected before execution.

`item set --dry-run` is fully offline and never fetches YouTube metadata.
Remove `--dry-run` to execute one PATCH through `ntn`. Preview text shows the
argument values for inspection; it is not a shell-escaped command to copy/paste.

For new YouTube items, override an inferred author during creation or upsert:

```bash
notion-cli item add-youtube https://youtu.be/example --author "Matt Pocock" --dry-run
```

Datasources configured with `query_endpoint = "data_source"` now use a
`data_source_id` parent when creating pages. Legacy aliases retain `database_id`.

See [the comparison and remaining improvements](docs/project-review.md) for the
GitHub research behind these changes and the next priorities.

## Query, Inspect, and Preview

Filter by the actual Notion property name; sorts accept logical config fields or
actual property names. Repeat `--sort` to order by several fields:

```bash
notion-cli datasource query items --filter '{"property":"Status","select":{"equals":"Done"}}' --sort score:desc --sort title:asc --page-size 50 --all
notion-cli datasource query items --start-cursor CURSOR --page-size 25
```

Without `--all`, the CLI returns one unchanged `ntn` response with its cursor.
With `--all`, it follows cursors and emits one combined JSON list after every
page succeeds. Filters and sorts are preserved across pages. Repeated/missing
cursors, malformed pages, and API-reported incomplete results stop with an error.
`--all` cannot bypass Notion's query limits; narrow the filter for large datasets.

Inspect or validate configured names and property types without modifying Notion:

```bash
notion-cli datasource schema items
notion-cli datasource schema items --check
notion-cli datasource schema items --check --dry-run
```

`--check` prints JSON with `valid` and `issues`, and exits with code 1 on a
mismatch. Dry-run previews the schema request; it does not validate the remote schema.

Put global options **before the command**:

```bash
notion-cli --dry-run-json datasource query items --sort title:asc --all
notion-cli --dry-run-json item set saved_video --author "Matt Pocock"
notion-cli --timeout 20 datasource query items --all
```

`--dry-run-json` implies preview and never executes `ntn`. It includes the exact
argument array, allowlisted non-secret environment overrides, and the timeout.
Upsert plans include query, update, and create branches. YouTube previews still
fetch metadata, as text previews do.

The timeout applies separately to each `ntn` call (including each query page),
with precedence `--timeout` → `[notion].timeout_seconds` → 60 seconds. Use a
finite positive number; there are no automatic retries. YouTube metadata keeps
its separate `[youtube].timeout_seconds` setting.

```toml
[notion]
default_workspace = "personal"
timeout_seconds = 60
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

## YouTube Providers

Default behavior:

- `youtube.provider = "no_key"` uses `yt-dlp`
- if `yt-dlp` fails and `YOUTUBE_API_KEY` is present, the CLI falls back to the YouTube Data API
- `youtube.provider = "api_key"` forces the YouTube Data API path

## Schema Overrides

If your Notion database uses different property shapes than the defaults, add
logical type overrides in config:

```toml
[datasources.items.property_types]
author = "multi_select"
status = "select"
```

## Development

CI runs on Ubuntu and Windows with Python 3.12 and 3.14. Tests include a real
local subprocess that exercises Unicode, quotes, empty arguments, and timeouts.

Run the full local quality gate:

```bash
pytest -v
ruff check .
mypy src
```

## Releases

- `CHANGELOG.md` is the source of truth for release notes.
- Git tags use the `vX.Y.Z` format.
- GitHub Actions builds release artifacts from tags and publishes release notes from the changelog.
