# Agent CLI Guide

This is the canonical guide for agents that use `notion-cli-agent`.

## Purpose

Use the local `notion-cli` wrapper instead of embedding raw Notion datasource IDs,
workspace IDs, or ad hoc `ntn` argument strings into prompts. The CLI keeps local
configuration in `notion-cli.toml` and exposes a small set of repeatable commands.

## Configuration Sources

The CLI reads project structure from a TOML file.

Preferred usage:

```bash
notion-cli --config notion-cli.toml <command>
```

Default behavior:

- if `--config` is omitted, the CLI checks `NOTION_CLI_CONFIG`
- then it looks for `./notion-cli.toml`
- otherwise it falls back to `$XDG_CONFIG_HOME/notion-cli/notion-cli.toml` or `~/.config/notion-cli/notion-cli.toml`
- `notion-cli.toml` is local and ignored
- `notion-cli.example.toml` is the public template that should stay safe to commit

Authentication for live `ntn api` calls can come from:

- `ntn login`
- `NOTION_API_TOKEN` in the environment

## Execution Mode

Prefer `--dry-run` first:

```bash
notion-cli datasource query items --dry-run
notion-cli preset run add_youtube --url https://youtu.be/example --dry-run
notion-cli item add-youtube https://youtu.be/example --score 4 --upsert --dry-run
```

`--dry-run` prints the resolved `ntn` argument values for inspection. This text
is not shell-escaped and does not display environment overrides. To execute a
reviewed operation, rerun the wrapper command without `--dry-run`.
`item set --dry-run` does no network or subprocess work. YouTube workflows still
fetch metadata during preview.

For legacy database aliases, `datasource query` and preset-backed write flows also
pin `--notion-version 2022-06-28` in the rendered command unless the datasource
config opts into `query_endpoint = "data_source"`.

Treat these commands as read-only by default:

- `doctor`
- `api v1/users/me`
- `datasource query <alias>`
- `datasource schema <alias>` (including `--check`)

Treat `preset run <name>` as a write operation because it renders a `v1/pages`
creation request.

## Commands

### `login`

Starts standard `ntn` authentication.

```bash
notion-cli login
```

### `doctor`

Checks the local Notion CLI installation.

```bash
notion-cli doctor
notion-cli doctor --dry-run
```

### `api`

Passes raw `ntn api` arguments through the wrapper.

```bash
notion-cli api --dry-run v1/users/me
notion-cli api v1/users/me
```

Use this for safe read-only endpoints when there is no higher-level wrapper command yet.

### `exec`

Passes raw `ntn` subcommands through the wrapper.

```bash
notion-cli exec --dry-run whoami
```

Use sparingly; prefer dedicated wrapper commands when available.

### `resolve datasource`

Returns the concrete datasource ID for a named alias.

```bash
notion-cli resolve datasource items
```

The output is the ID only.

### `resolve preset`

Returns the preset's resolved datasource ID when present.

```bash
notion-cli resolve preset add_item
```

### `resolve page`

Returns the concrete page ID for a named alias.

```bash
notion-cli resolve page sci_pop
```

### `datasource query`

Runs a query against a configured datasource alias.

- `--filter JSON`: a Notion filter object using actual property names and types.
- `--sort FIELD:asc|desc`: repeatable, in priority order. Logical config field
  names are resolved; other names are sent as literal Notion property names.
- `--page-size N`: 1–100 results per request; omitted leaves the API default.
- `--start-cursor CURSOR`: resume from a response's `next_cursor`.
- `--all`: fetch every available page and combine `results` into one list response.

Every page preserves the filter, sorts, and page size. Output is emitted only
when all pages succeed; a failure never produces a partial success response.
Cursor cycles/missing cursors and malformed/incomplete API responses fail with
exit code 1. API result caps still apply; narrow filters for oversized queries.
Without `--all`, the response and cursor pass through unchanged.

```bash
notion-cli datasource query items --dry-run
notion-cli datasource query items
```

### `datasource schema`

```bash
notion-cli datasource schema items
notion-cli datasource schema items --check
notion-cli --dry-run-json datasource schema items --check
```

Retrieves schema via GET from the configured legacy database or modern data source.
`--check` compares each configured property mapping to its remote name and type,
using the same defaults/overrides as writes. Output is
`{"datasource":"items","valid":true,"issues":[]}`. Mismatches set `valid` to
false, list `field`, `property`, `expected`, and `actual`, and exit with code 1.
A missing property has `actual: null`; inspect access permissions as well as names.
The check does not modify schema or local config and does not run automatically
before writes. Dry-run only previews the GET, without claiming a successful check.

### Global execution options

These options go **before** the subcommand and apply to commands that invoke `ntn`:

```bash
notion-cli --timeout 20 --dry-run-json datasource query items --all
notion-cli --dry-run-json item add-youtube https://youtu.be/example --upsert
```

- `--timeout SECONDS`: finite positive per-call limit. Overrides
  `[notion].timeout_seconds`, which defaults to 60. Each paginated request gets
  its own limit; the whole query has no aggregate deadline. No automatic retries.
  After a timed-out write, inspect remote state before deciding whether to retry.
- `--dry-run-json`: implies dry-run and returns JSON instead of text. It never
  invokes `ntn`; YouTube workflows still fetch enrichment metadata. `resolve`
  commands keep their ID-only output because they do not invoke `ntn`.

JSON plan version 1:

- Single command: `version`, `kind: "command"`, `args` (exact argument array),
  `env` (only explicit NOTION_HOME/NOTION_WORKSPACE_ID/NOTION_API_VERSION overrides),
  `timeout_seconds`. Inherited environment and token variables are never included.
- Query: same fields, `kind: "query"`, plus
  `pagination: {"all": true|false, "cursor_field": "next_cursor"}`.
- Schema: same fields, `kind: "schema"`, plus `check: true|false`.
- Upsert: `version`, `kind: "upsert"`, and `commands` with `query`, `update`, and
  `create` command plans. The update uses a `<page_id>` placeholder resolved by
  the query; the update and create branches are alternatives.

Do not execute a plan by joining its arguments into a shell string. Rerun the
wrapper without preview after authorization. Raw passthrough arguments appear
verbatim in previews, so keep authentication in `ntn` or its environment.

### `preset run`

Resolves a named preset into a `v1/pages` create call.

```bash
notion-cli preset run add_item --title "Inbox item" --dry-run
```

If the preset has `youtube = true`, `--url` is required and the CLI fills:

- title
- canonical YouTube URL
- duration

Example:

```bash
notion-cli preset run add_youtube --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

### `item set`

Make a focused property correction without enrichment or unrelated changes:

```bash
notion-cli item set saved_video --author "Matt Pocock" --dry-run
notion-cli item set saved_video --status "Done" --date today --dry-run
notion-cli item set saved_video --datasource reading --tags "learning,typescript" --dry-run
```

- Target: `[pages]` alias, page UUID (with or without hyphens), or HTTPS Notion URL.
- Accepted URL hosts: `notion.so`, `notion.site`, and their subdomains. A `p` query
  parameter selects the opened page; an invalid or repeated `p` is rejected.
- `--datasource` selects property mappings/types and API version; defaults to `items`.
- Fields: `--author`, `--title`, `--status`, `--score` (1–5), `--tags`, `--date`, `--project`.
- `--date` accepts YYYY-MM-DD or `today`; `--project` resolves a `[pages]` alias.
- Only supplied fields are sent. There are no implicit status/date/tag defaults.
- Tags replace the list and are deduplicated; an empty string clears tags.
- At least one field is required. Unmapped fields and blank author/title/status
  values fail before any `ntn` execution.
- Live execution performs one page PATCH and prints the `ntn` response.
- This is a write operation: use only when the user authorizes the correction.

### `item add-youtube`

Runs the first-class YouTube item workflow.

```bash
notion-cli item add-youtube https://youtu.be/dQw4w9WgXcQ --score 4 --project sci_pop --tags sci-pop,youtube --dry-run
```

Use `--author "Name"` to override the inferred author in both create and update
branches. To correct only an existing author, use `item set`.

With `--upsert`, the CLI first queries by canonical Link and then updates the existing page or creates a new one.
The Link filter and page create/update property values are rendered as JSON input, so canonical YouTube URLs with `?v=...`, titles with spaces, and unicode values do not break `ntn api` inline parsing.
With `--done`, the CLI sets `Status = Done` and defaults `Date` to today unless `--date` is provided.

Malformed query responses (missing or non-list `results`) stop upsert before any
write instead of being interpreted as no match. With `query_endpoint = "data_source"`,
new pages use `parent[data_source_id]`; legacy aliases use `parent[database_id]`.
Configuration and domain errors print `Error: ...` to stderr and exit with code 1.
CLI argument validation exits with code 2.

## YouTube Metadata

The repository intentionally prefers a no-key flow first, with a safe fallback.

- provider: `no_key`
- implementation: `yt-dlp`
- fallback: if `yt-dlp` fails and `YOUTUBE_API_KEY` is present, use the YouTube Data API
- alternate provider: `api_key`
- fields collected: title, canonical URL, duration, channel/author

No YouTube API key is required for the default enrichment path, but adding
`YOUTUBE_API_KEY` makes the workflow more resilient when YouTube blocks `yt-dlp`.

## Recommended Agent Behavior

- prefer datasource aliases and presets over raw IDs
- add `[datasources.<alias>.property_types]` overrides when the local schema uses different Notion property shapes for logical fields
- keep write operations explicit
- inspect `--dry-run` output before live mutation
- do not commit local `notion-cli.toml`
- if a needed wrapper command is missing, add it to the CLI instead of teaching the
  agent raw Notion payload shapes
