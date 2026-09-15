# Project review — 2026-09-15

## GitHub comparison

This project is a small config-driven wrapper around `ntn`. The most useful
additions preserve that model and reuse its authentication and API execution.
The changes below are original implementations informed by public command interfaces.

| Project | Useful idea | Application here |
| --- | --- | --- |
| [4ier/notion-cli](https://github.com/4ier/notion-cli) | Property editing, URL inputs, schema-aware fields, filters | Added focused `item set`, Notion URL resolution, and existing config type mappings |
| [jjovalle99/notion-cli (notionctl)](https://github.com/jjovalle99/notion-cli) | Page updates and predictable agent output/errors | Added sparse PATCH updates and consistent domain errors on stderr |
| [Balneario-de-Cofrentes/notion-cli-agent](https://github.com/Balneario-de-Cofrentes/notion-cli-agent) | Schema inspection, batch preview, Markdown operations | Candidates after reliable single-item commands |

## Implemented

- [Issue #14](https://github.com/alexsuslin/notion-cli/issues/14): correct only
  explicitly supplied item properties without re-enriching a YouTube item.
- Explicit author override for YouTube creation/upsert.
- Page alias/UUID/Notion URL inputs, including the selected page in `?p=` links.
- Modern datasource parents in page creation, following Notion's
  [API upgrade guide](https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03).
- Reject malformed upsert query results rather than creating a potential duplicate.
- Display configuration and domain failures on stderr with exit code 1.

The property update contract follows the official
[Update page API](https://developers.notion.com/reference/patch-page): send only
properties being changed. IDs remain in local configuration; execution uses `ntn`.

## Follow-ups implemented

1. **Query controls and pagination:** `datasource query` now has `--filter`,
   repeatable `--sort`, `--page-size`, `--start-cursor`, and `--all`. It preserves
   parameters and rejects cursor cycles, malformed pages, and API-reported
   incomplete results without printing a partial success response.
2. **Machine-readable preview:** global `--dry-run-json` returns a versioned
   argument array, allowlisted non-secret environment overrides, and timeout.
   Upsert plans include alternative create/update branches. No `ntn` execution.
3. **Execution time bounds:** global `--timeout` overrides `[notion].timeout_seconds`
   (default 60). Each `ntn` call has its own limit and a clear timeout error.
   No automatic retries; a timed-out write may already have completed remotely.
4. **Schema checks:** `datasource schema --check` uses the configured legacy or
   modern GET endpoint, compares mapped names/types, and returns JSON mismatches
   with exit code 1. It does not mutate remote schema or local config.
5. **Cross-platform CI:** Ubuntu/Windows × Python 3.12/3.14 matrix. A real local
   executable stub verifies argument transport and UTF-8 output; another test
   verifies subprocess timeout. Tests do not require a Notion token.

## Remaining larger work

- Markdown sync, bulk mutation, and backup workflows still need separate contracts.
- `--all` cannot bypass the upstream query cap and holds aggregated results in
  memory. A future export/streaming workflow should define resumable output.
- Schema checking validates property names and types, not select options,
  relation destinations, or write permissions.
- Timeouts apply per call, not to the whole pagination/enrichment workflow.

## Validation boundary

The implementation has dry-run regression tests, mocked `ntn` API tests, and
real local subprocess transport/timeout tests. The CI matrix is configured;
remote GitHub Actions results require publishing the changes.
No live Notion pages were modified by this review. Live API permissions and remote
schema correctness therefore remain integration checks for an authorized workspace.
