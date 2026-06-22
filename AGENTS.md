## Working Rules

- Keep project-specific IDs in `notion-cli.toml`, not in Python code.
- Keep the tracked repository public-safe: only commit `notion-cli.example.toml`, never live IDs.
- Use `ntn` for authentication and API execution instead of direct token storage.
- Run `pytest -v`, `ruff check .`, and `mypy src` before claiming completion.
- Prefer dry-run coverage for new CLI features before live execution support.
- Keep `skills/notion-cli-agent/`, `docs/agent-cli.md`, and `README.md` in sync when agent-facing CLI behavior changes.
