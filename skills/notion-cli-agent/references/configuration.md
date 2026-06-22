# Configuration Reference

Use this file when the task depends on the repository's local config schema.

## Public vs Private Files

- `notion-cli.example.toml` is the tracked public template
- `notion-cli.toml` is the ignored local file for private IDs and defaults

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

### `[datasources.<alias>]`

```toml
[datasources.items]
id = "data-source-id-here"
title_property = "Name"
```

- `id`: required live datasource ID
- `title_property`: logical title field name, default `Name`

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

### `[youtube]`

```toml
[youtube]
provider = "no_key"
timeout_seconds = 10
```

The current implementation uses `yt-dlp` and does not require API credentials.

## Maintenance Notes

- extend config sections before adding hardcoded CLI arguments
- keep examples safe and placeholder-based
- when adding new rendered property types, update both this reference and
  `references/agent-cli.md`
