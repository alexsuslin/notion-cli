# Notion CLI Design

Date: 2026-06-21
Status: Draft approved in chat, written for review

## Summary

Build a Python-first project named `notion-cli` that wraps the standard Notion CLI (`ntn`) instead of replacing it. The project must keep all workspace-specific values out of code and move them into project configuration, including datasource IDs, page IDs, property bundles, and reusable presets. The first version should support config-aware orchestration of official `ntn` commands plus optional YouTube metadata enrichment for `title`, `length`, and canonical `url` without requiring a YouTube API key by default.

## Goals

- Use the official Notion CLI command surface as the execution backend.
- Avoid hardcoded IDs, bundles, and workspace-specific values in Python code.
- Preserve a simple command-line workflow while making it safer and more reproducible.
- Keep authentication aligned with current Notion CLI behavior.
- Support no-key YouTube metadata extraction for a small metadata subset.
- Favor configuration and composability over custom Notion API logic.

## Non-Goals

- Reimplement the full Notion API client in Python.
- Replace `ntn login`, `ntn doctor`, or other built-in Notion CLI auth and session flows.
- Build a broad YouTube ingestion pipeline.
- Depend on a YouTube API key for the default workflow.
- Commit secrets, tokens, or personal IDs to source control.

## Constraints And Source Guidance

The design is based on the current official Notion CLI documentation on `developers.notion.com`, specifically the overview and authentication guides. The project should assume the current standard workflow is centered on:

- `ntn login`
- `ntn api`
- `ntn doctor`
- Notion-managed `config.json` and `workspaces.json`
- Environment variables such as `NOTION_HOME`, `NOTION_API_TOKEN`, `NOTION_WORKSPACE_ID`, and `NOTION_KEYRING`

This project should orchestrate those features rather than duplicate them.

## Recommended Approach

Use a thin Python wrapper over `ntn`.

This is preferred over a mixed direct-HTTP model or a full custom Notion client because it:

- stays closest to the official CLI,
- reduces maintenance burden when Notion evolves the CLI,
- keeps authentication and workspace management in one place,
- and still allows project-specific aliases, presets, and config-driven shortcuts.

## User Experience

The tool should expose a single user-facing command, `notion-cli`, with two families of commands:

1. Native pass-through commands for standard `ntn` workflows.
2. Config-aware commands that resolve project aliases, saved IDs, and preset inputs before calling `ntn`.

Examples of intended usage:

```text
notion-cli login
notion-cli doctor
notion-cli api v1/users/me
notion-cli exec api v1/users/me
notion-cli datasource query items
notion-cli preset run add-item --title "Example"
notion-cli preset run add-youtube --url "https://youtu.be/..."
notion-cli resolve datasource items
```

The exact subcommand names can be refined during implementation, but the separation between passthrough and config-aware commands should remain stable.

## Architecture

The implementation should be split into focused units with clear responsibilities:

### CLI Layer

Parses arguments, handles help text, and dispatches to either passthrough execution or config-aware execution.

### Config Loader

Loads project configuration from a repo-local file, validates schema, applies defaults, and merges optional environment overrides.

### Resolver Layer

Resolves named datasources, pages, property bundles, workspace aliases, presets, and reusable request fragments into concrete values.

### YouTube Metadata Provider

Accepts a YouTube URL and returns normalized metadata:

- canonical URL
- title
- length

The default provider should work without an API key if possible. A future provider may use an API key for improved reliability, but the initial design should not require one.

### Command Renderer

Converts resolved configuration and user input into a concrete `ntn` command invocation.

### Executor

Runs `ntn`, streams or captures output, maps failures into user-friendly error categories, and supports dry-run inspection.

## Configuration Model

Primary configuration should live in a project file:

- `notion-cli.toml`

Optional supporting files:

- `config/examples/*.toml` for sample configurations
- `.env` for secrets or per-shell overrides only

Configuration should be organized by meaning rather than by command. A representative structure:

```toml
[notion]
default_workspace = "personal"
notion_home = ".notion-home"

[workspaces.personal]
workspace_id = "..."

[datasources.items]
id = "..."
title_property = "Name"

[pages.inbox]
id = "..."

[bundles.default_item]
properties = ["title", "status", "tags", "link"]

[presets.add_item]
kind = "page_create"
datasource = "items"
bundle = "default_item"

[presets.add_youtube]
kind = "page_create"
datasource = "items"
bundle = "default_item"
youtube = true

[youtube]
provider = "no_key"
timeout_seconds = 10
```

The code must treat configuration as the source of truth for user-specific IDs and reusable command intent.

## Authentication And Runtime Environment

Authentication remains owned by the Notion CLI.

Supported patterns:

- interactive login with `ntn login`
- PAT-based execution through `NOTION_API_TOKEN`
- per-command workspace override through `NOTION_WORKSPACE_ID`
- optional `NOTION_HOME` override to isolate local CLI state
- optional `NOTION_KEYRING=0` when file-backed auth is needed

The Python CLI should not implement its own token store. It should only prepare the execution environment for `ntn` when the project config asks for it.

## Command Categories

### Passthrough Commands

These forward directly to `ntn` with minimal processing:

- `login`
- `doctor`
- `api`
- `exec` for explicit `ntn` forwarding

This preserves access to the official CLI surface.

### Config-Aware Commands

These add value by resolving names and presets before execution:

- `datasource query <name>`
- `preset run <name>`
- `resolve datasource <name>`
- `resolve preset <name>`

These commands should make common workflows shorter without hiding what `ntn` is doing.

## YouTube Metadata Enrichment

YouTube support is intentionally narrow.

Input:

- a YouTube watch URL, short URL, or equivalent supported URL form

Output:

- normalized canonical watch URL
- video title
- video length

This metadata can then populate preset fields before the final `ntn` command is built.

The provider should not assume more than this small metadata contract. It should not fetch comments, channel data, thumbnails, or transcripts in v1.

## Data Flow

For a config-aware command, the expected flow is:

1. Parse CLI arguments.
2. Load `notion-cli.toml`.
3. Apply environment overrides where supported.
4. Resolve named workspace, datasource, page, bundle, and preset references.
5. If requested, enrich inputs from YouTube metadata.
6. Render the final `ntn` invocation and environment.
7. Execute `ntn`.
8. Return raw output or a lightly normalized summary.

This pipeline should be observable and debuggable.

## Error Handling

Errors should be grouped into three categories:

### Config Errors

Examples:

- missing preset name
- unknown datasource alias
- invalid config schema
- unresolved property mapping

### Environment Errors

Examples:

- `ntn` not installed
- missing auth
- invalid workspace selection
- missing executable on `PATH`

### Runtime Errors

Examples:

- `ntn` returned a non-zero exit code
- Notion API request failed
- YouTube metadata provider failed

Each error should explain what failed, where it failed, and the next likely fix.

## Debugging And Transparency

The CLI should include:

- `--dry-run` to print the resolved `ntn` command and environment decisions without executing
- `--verbose` to show which config entries were used
- resolver inspection commands for aliases and presets

The goal is to make the wrapper trustworthy rather than magical.

## Testing Strategy

Default automated tests should avoid live Notion dependencies.

High-value test areas:

- config parsing and validation
- alias and preset resolution
- command rendering
- environment assembly
- YouTube URL normalization
- YouTube metadata extraction with mocked or fixture-backed providers

Optional integration tests may be added later for:

- live `ntn` execution
- authenticated Notion workspace access

Integration tests should be opt-in and clearly documented because they depend on external state.

## Proposed Initial Repository Shape

```text
notion-cli/
  pyproject.toml
  README.md
  .gitignore
  .editorconfig
  AGENTS.md
  docs/
    superpowers/
      specs/
        2026-06-21-notion-cli-design.md
  src/
    notion_cli/
      __init__.py
      cli.py
      config.py
      resolver.py
      render.py
      exec.py
      youtube.py
      errors.py
  tests/
    test_config.py
    test_resolver.py
    test_render.py
    test_youtube.py
  config/
    examples/
      minimal.toml
      youtube.toml
```

This layout follows Python-first project conventions and leaves room for later packaging and CI setup.

## Security Notes

- No secrets should be stored in tracked project config.
- Tokens should come from `ntn login`, the OS keychain, or `NOTION_API_TOKEN`.
- If file-based auth is required through `NOTION_KEYRING=0`, the resulting auth files must be treated as sensitive local state.
- Repo examples should use placeholders only.

## Open Implementation Decisions

These are intentionally narrow and can be resolved during implementation without changing the approved design:

- exact CLI framework choice in Python
- exact output formatting for passthrough versus resolved commands
- exact no-key YouTube metadata backend
- whether `exec` is exposed as a visible user command or kept internal

None of these decisions should change the core architecture or config-first model.

## Implementation Readiness

This design is scoped for a single implementation plan. It is not trying to solve general Notion automation. The first milestone should produce:

- a Python package scaffold,
- a config schema and examples,
- passthrough execution for standard `ntn` commands,
- config-aware datasource and preset resolution,
- dry-run and verbose modes,
- and narrow no-key YouTube enrichment for `title`, `length`, and canonical `url`.

## Current Workspace Note

This design document was written in the target workspace, but the workspace is not currently initialized as a Git repository. If commit history is required for the spec and future scaffolding, repository initialization or the correct project root should be established before the implementation phase.
