# Handoff

Current continuation point for notion-cli. Use [README](../README.md) for setup,
[AGENTS.md](../AGENTS.md) for working rules, and [the project review](project-review.md)
for feature history and larger follow-ups.

## Outcome and acceptance

- Current goal: pilot project-scaffolding 0.3.0 additive adoption in this repository.
- Acceptance: preserve existing guidance and application behavior; add one populated
  handoff, link it from AGENTS.md, and record adoption provenance in .scaffold.json.
- Scope: documentation and provenance in notion-cli only. On 2026-11-11 the owner
  authorized committing adoption and pushing the current branch. Other projects,
  merging to main, releases and live Notion data are outside scope.

## Current state

- Last substantive update: 2026-11-11.
- Base revision: c0bb809def0f9ad80089719f3bebe3b5dff12954 on
  codex/fix-ci-colored-errors; one registered worktree, clean before adoption.
- Local main was 5511a7ae70dd88ef4e8b9174b0f09ee924f2ce24 at inspection.
  No fetch was performed; remote branch, PR and CI status are not established here.
- Existing behavior: a Python wrapper around ntn, with configuration-driven item
  updates, query pagination, schema checks and JSON dry runs. See the project review.
  The base commit adjusts regression assertions for colored CLI validation errors.
- Implemented in this working tree: docs/HANDOFF.md and .scaffold.json added;
  AGENTS.md retains its existing rules and gains a link to this document.
- Verification: the initial doctor reported only missing_handoff; adopt preview
  succeeded. Post-adoption checks are recorded below.
- Delivery: prepared for the authorized commit and push to
  codex/fix-ci-colored-errors. Resolve the commit containing this handoff and check
  its remote branch / CI status for delivery evidence; this text precedes the push.
  Integration into main and release publication are not part of this task.
- Live integration: no Notion API calls, authentication changes or deployment.

## Verification commands

Use the existing Python 3.12+ development environment; local checks use the existing
Python 3.14 virtual environment. Run from the repository root:

- Tests: `python -m pytest -v`.
- Lint: `python -m ruff check .`.
- Types: `python -m mypy src`.

These gates come from AGENTS.md, CONTRIBUTING.md and .github/workflows/ci.yml.
Doctor infers pytest and Ruff candidates but does not discover the required Mypy gate.
The configured CI matrix is Ubuntu/Windows with Python 3.12/3.14; configuration
alone is not evidence of a successful remote run.

## Evidence

| Working state | Check / environment | Result |
| --- | --- | --- |
| Base revision | doctor and adopt --preview, scaffold 0.3.0 | Missing handoff; preview passed |
| Adoption working tree | pytest -v, Windows / Python 3.14 | 123 passed, no skips |
| Adoption working tree | Ruff check / Mypy src | Passed; 10 source files type-checked |
| Adoption working tree | doctor, scaffold 0.3.0 | Exit 0; only informational working_changes |
| Adoption working tree | Repeated adopt --preview | Already adopted; no additions proposed |
| Pre-commit adoption review | Diff and provenance review | Only the three intended files; index and HEAD preserved before staging |

Checks above ran on 2026-11-11. Test temporary files and Mypy cache were isolated
in a temporary directory; pytest and Ruff caches were disabled. No tests were
added for these documentation changes. No live service or additional Python/OS
matrix checks are claimed.

## Remaining work

- Next action after the authorized push: review the adoption commit on the current
  branch and any reported CI results. A merge, release or product change requires
  its own task scope.
- Adoption does not configure Copier updates. The manifest hashes describe the
  original generated files; customizing this handoff does not require changing them.
- Product follow-ups remain in the project review; adoption does not implement them.
- Who can continue: the owner or a session explicitly authorized for notion-cli.
