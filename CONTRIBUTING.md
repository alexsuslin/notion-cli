# Contributing

## Development Setup

1. Install Python 3.12+.
2. Install the project in editable mode:

```bash
python -m pip install -e .[dev]
```

3. Install the official Notion CLI (`ntn`) if you want live execution tests.

## Project Rules

- Keep project-specific IDs in `notion-cli.toml`, not in Python code.
- Keep secrets out of tracked files.
- Prefer extending config resolution over adding one-off command logic.
- Treat live Notion calls as opt-in and keep them read-only unless explicitly requested.
- Update `skills/notion-cli-agent/` and `docs/agent-cli.md` when agent-facing commands or config behavior change.

## Quality Gates

Run all checks before opening a PR:

```bash
pytest -q
ruff check .
mypy src
```

## Branching

- Use short-lived branches from `main`.
- Prefer names like `feat/add-query-limit` or `fix/windows-ntn-shim`.

## Pull Requests

- Keep PRs focused.
- Include a short summary of user-visible changes.
- List the verification commands you ran.

## Releases

- Update `CHANGELOG.md`.
- Use semantic versioning.
- Tag releases as `vX.Y.Z`.
