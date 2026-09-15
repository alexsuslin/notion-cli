# Report improvements implementation plan

**Goal:** Implement the five follow-ups in `docs/project-review.md`.

**Architecture:** Keep authentication and all API calls in `ntn`. Add query and
schema modules for request/response rules; retain CLI orchestration in `cli.py`.
Carry the execution timeout on `RenderedCommand`, with CLI/config precedence.

**Constraints:** Python 3.12+, preserve text previews, no retries, no live writes,
no private IDs, synchronize README and agent docs. Preserve prior uncommitted work.

## Execution and JSON preview

- [x] Test real subprocess argument transport, finite timeout, timeout errors,
  CLI/config/default precedence, and JSON preview without process execution.
- [x] Add `RenderedCommand.timeout_seconds` (60 by default), `[notion].timeout_seconds`,
  and global `--timeout SECONDS` / `--dry-run-json` (before subcommands).
- [x] JSON plans include version, kind, args, allowlisted env overrides, and timeout;
  upsert includes named query/update/create branches. Never serialize inherited env.

## Datasource query

- [x] Add tests for filter/sort/cursor rendering and multiple response pages.
- [x] Implement `--filter JSON`, repeatable `--sort field:asc|desc`, `--page-size 1..100`,
  `--start-cursor`, and `--all`. Map logical sort fields through config.
- [x] Preserve filters/sorts on each page, validate pagination envelopes and cursor
  progress, reject incomplete API results, emit one combined JSON list only on success.
- [x] Show a pagination plan in dry-run without fetching any pages.

## Schema inspection

- [x] Test legacy/modern GET paths, valid schemas, missing properties, type drift,
  malformed API responses, and offline dry-run.
- [x] Implement `datasource schema NAME [--check]`, with shared property-type defaults.
  Check configured mappings; report JSON issues and exit 1 on mismatch.

## CI and closeout

- [x] Expand CI to Ubuntu/Windows × Python 3.12/3.14 and run the subprocess stub test.
- [x] Update README, agent skill/reference docs, config example, changelog, and report.
- [x] Run `pytest -v`, `ruff check .`, `mypy src`, formatter checks, and independent review.

## Verification

119 tests passed on Windows/Python 3.14.6. Ruff, formatter checks, and Mypy
passed. Independent review found no actionable issues. JSON query CLI smoke
test passed using public placeholder configuration. GitHub CI is configured
but has not run for these unpublished changes. No live Notion writes.
