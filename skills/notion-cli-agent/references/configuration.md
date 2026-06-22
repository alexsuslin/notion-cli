# Configuration Reference

Use this file when the task depends on the repository's local config schema.

## Public vs Private Files

- `notion-cli.example.toml` is the tracked public template
- `notion-cli.toml` is the ignored local file for private IDs and defaults

Config lookup order:

1. `--config <path>`
2. `NOTION_CLI_CONFIG`
3. `./notion-cli.toml`
4. `$XDG_CONFIG_HOME/notion-cli/notion-cli.toml` or `~/.config/notion-cli/notion-cli.toml`

Never commit real:

- workspace IDs
- datasource IDs
- page IDs
- personal workspace aliases tied to a private account

## Top-Level Sections

### `[notion]`

```toml
[notion]
default_workspace = "personal"
notion_home = ".notion-home"
```

- `default_workspace`: required alias that must exist under `[workspaces]`
- `notion_home`: optional local `NOTION_HOME` override for the wrapped `ntn` command

### `[workspaces.<alias>]`

```toml
[workspaces.personal]
workspace_id = "workspace-id-here"
```

- `workspace_id` is optional
- omit it when not needed
- keep real values only in local config

### `[pages.<alias>]`

Use page aliases for relation targets such as project pages.

```toml
[pages.sci_pop]
id = "page-id-here"
```

### `[datasources.<alias>]`

```toml
[datasources.items]
id = "data-source-id-here"
title_property = "Name"
query_endpoint = "database"
notion_version = "2022-06-28"
```

- `id`: required live datasource ID
- `title_property`: logical title field name, default `Name`
- `query_endpoint`: `database` for legacy `v1/databases/.../query` or `data_source` for `v1/data_sources/.../query`
- `notion_version`: optional explicit Notion API version; legacy database queries default to `2022-06-28`

### `[datasources.<alias>.properties]`

Maps logical field names used by presets to real Notion property names.

```toml
[datasources.items.properties]
title = "Name"
link = "Link"
length = "Time"
```

Current built-in rendered field types:

- `title`
- `link`
- `length`
- `author`
- `type`
- `score`
- `status`
- `date`
- `tags`
- `project`

### `[datasources.<alias>.property_types]`

Overrides the default rendered Notion property shape for a logical field.

```toml
[datasources.items.property_types]
author = "multi_select"
status = "select"
```

Supported override values:

- `title`
- `rich_text`
- `url`
- `select`
- `status`
- `date`
- `relation`
- `multi_select`

Use this when your local database schema differs from the wrapper defaults, for
example when `Author` is a `multi_select` instead of `rich_text`, or `Status`
is a `select` instead of a Notion status property.

### `[bundles.<alias>]`

Defines reusable ordered property sets.

```toml
[bundles.youtube_item]
properties = ["title", "link", "length"]
```

### `[presets.<alias>]`

Defines named write presets.

```toml
[presets.add_youtube]
kind = "page_create"
datasource = "items"
bundle = "youtube_item"
youtube = true
```

- `kind`: currently `page_create`
- `datasource`: datasource alias to resolve
- `bundle`: bundle alias defining which logical properties to render
- `youtube`: when `true`, require `--url` and enrich title, URL, and duration
- `youtube`: when `true`, require `--url` and enrich title, URL, duration, and author

### `[youtube]`

```toml
[youtube]
provider = "no_key"
timeout_seconds = 10
```

- `provider = "no_key"` uses `yt-dlp` first
- if `YOUTUBE_API_KEY` is present and `yt-dlp` fails, the CLI falls back to the YouTube Data API
- `provider = "api_key"` forces the YouTube Data API and requires `YOUTUBE_API_KEY`
- `timeout_seconds` applies to both provider paths

## Maintenance Notes

- extend config sections before adding hardcoded CLI arguments
- keep examples safe and placeholder-based
- when adding new rendered property types, update both this reference and
  `references/agent-cli.md`
