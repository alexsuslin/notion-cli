# Notion CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python package that wraps the official Notion CLI with config-driven aliases, presets, dry-run support, and no-key YouTube metadata enrichment for title, length, and canonical URL.

**Architecture:** The package uses a thin orchestration layer over `ntn`. Project config in `notion-cli.toml` resolves workspace aliases, datasource IDs, and presets into concrete `ntn` invocations, while a small YouTube provider enriches preset inputs before command rendering.

**Tech Stack:** Python 3.11+, `typer`, `pydantic`, `pytest`, `ruff`, `mypy`, `yt-dlp`

---

## File Structure

- Create: `pyproject.toml` for packaging, dependencies, tooling, and CLI entrypoint.
- Create: `.gitignore` for Python, local Notion state, test artifacts, and auth spillover safety.
- Create: `.editorconfig` for consistent whitespace and line endings.
- Create: `README.md` for install, config, and usage guidance.
- Create: `AGENTS.md` for repo-specific coding, test, and release expectations.
- Create: `src/notion_cli/__init__.py` for package version export.
- Create: `src/notion_cli/cli.py` for Typer app and command wiring.
- Create: `src/notion_cli/config.py` for config models and loader.
- Create: `src/notion_cli/errors.py` for typed user-facing errors.
- Create: `src/notion_cli/resolver.py` for datasource, preset, and workspace resolution.
- Create: `src/notion_cli/render.py` for `ntn` argument and environment assembly.
- Create: `src/notion_cli/exec.py` for subprocess execution and dry-run support.
- Create: `src/notion_cli/youtube.py` for URL normalization and metadata extraction through `yt-dlp`.
- Create: `tests/test_config.py` for config validation coverage.
- Create: `tests/test_resolver.py` for alias and preset resolution coverage.
- Create: `tests/test_render.py` for `ntn` command rendering coverage.
- Create: `tests/test_youtube.py` for URL normalization and provider behavior coverage.
- Create: `tests/test_cli.py` for smoke-level CLI behavior checks.
- Create: `config/examples/minimal.toml` for base configuration.
- Create: `config/examples/youtube.toml` for YouTube-enabled preset examples.

### Task 1: Bootstrap The Python Project

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `src/notion_cli/__init__.py`

- [ ] **Step 1: Write the failing packaging smoke test**

```python
# tests/test_cli.py
from importlib.metadata import entry_points


def test_console_script_registered() -> None:
    scripts = entry_points(group="console_scripts")
    assert any(ep.name == "notion-cli" for ep in scripts)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_console_script_registered -v`
Expected: FAIL with `PackageNotFoundError` or no `notion-cli` entry point discovered because `pyproject.toml` does not exist yet.

- [ ] **Step 3: Write minimal project scaffold**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[project]
name = "notion-cli"
version = "0.1.0"
description = "Config-driven wrapper around the official Notion CLI"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Proprietary" }
authors = [{ name = "asuslin" }]
dependencies = [
  "pydantic>=2.11.0",
  "typer>=0.16.0",
  "yt-dlp>=2025.6.9",
]

[project.optional-dependencies]
dev = [
  "mypy>=1.16.0",
  "pytest>=8.4.0",
  "ruff>=0.12.0",
]

[project.scripts]
notion-cli = "notion_cli.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
strict = true
packages = ["notion_cli"]
```

```python
# src/notion_cli/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```python
# src/notion_cli/cli.py
import typer

app = typer.Typer(help="Config-driven wrapper around the official Notion CLI.")
```

```gitignore
# .gitignore
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
dist/
build/
*.pyc
.env
.notion-home/
auth.json
```

```ini
# .editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4
```

```markdown
# README.md

# notion-cli

Config-driven wrapper around the official Notion CLI (`ntn`).
```

```markdown
# AGENTS.md

## Working Rules

- Run `pytest`, `ruff check .`, and `mypy src` before claiming completion.
- Keep workspace-specific IDs out of code and out of tracked secrets.
- Prefer extending config and resolver logic over adding one-off command branches.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py::test_console_script_registered -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git init
git add pyproject.toml .gitignore .editorconfig README.md AGENTS.md src/notion_cli/__init__.py src/notion_cli/cli.py tests/test_cli.py
git commit -m "chore: bootstrap notion cli package"
```

### Task 2: Add Config Models And Loader

**Files:**
- Create: `src/notion_cli/config.py`
- Create: `src/notion_cli/errors.py`
- Create: `tests/test_config.py`
- Create: `config/examples/minimal.toml`

- [ ] **Step 1: Write the failing config tests**

```python
# tests/test_config.py
from pathlib import Path

import pytest

from notion_cli.config import load_config
from notion_cli.errors import ConfigError


def test_load_config_reads_named_datasource(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]
        workspace_id = "workspace-123"

        [datasources.items]
        id = "datasource-123"
        title_property = "Name"
        """.strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.notion.default_workspace == "personal"
    assert config.datasources["items"].id == "datasource-123"


def test_load_config_rejects_missing_workspace_reference(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "missing"
        """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="default workspace"):
        load_config(config_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError` for `notion_cli.config`.

- [ ] **Step 3: Write minimal config loader and example**

```python
# src/notion_cli/errors.py
class NotionCliError(Exception):
    """Base error for notion-cli."""


class ConfigError(NotionCliError):
    """Raised when project configuration is missing or invalid."""


class EnvironmentError(NotionCliError):
    """Raised when local tools or authentication are unavailable."""


class RuntimeCommandError(NotionCliError):
    """Raised when `ntn` returns a non-zero exit code."""
```

```python
# src/notion_cli/config.py
from __future__ import annotations

from pathlib import Path
from typing import Any

import tomllib
from pydantic import BaseModel, Field, model_validator

from notion_cli.errors import ConfigError


class NotionSettings(BaseModel):
    default_workspace: str
    notion_home: str | None = None


class WorkspaceConfig(BaseModel):
    workspace_id: str


class DatasourceConfig(BaseModel):
    id: str
    title_property: str = "Name"


class PageConfig(BaseModel):
    id: str


class BundleConfig(BaseModel):
    properties: list[str] = Field(default_factory=list)


class PresetConfig(BaseModel):
    kind: str
    datasource: str | None = None
    bundle: str | None = None
    youtube: bool = False


class YoutubeConfig(BaseModel):
    provider: str = "no_key"
    timeout_seconds: int = 10


class ProjectConfig(BaseModel):
    notion: NotionSettings
    workspaces: dict[str, WorkspaceConfig] = Field(default_factory=dict)
    datasources: dict[str, DatasourceConfig] = Field(default_factory=dict)
    pages: dict[str, PageConfig] = Field(default_factory=dict)
    bundles: dict[str, BundleConfig] = Field(default_factory=dict)
    presets: dict[str, PresetConfig] = Field(default_factory=dict)
    youtube: YoutubeConfig = Field(default_factory=YoutubeConfig)

    @model_validator(mode="after")
    def validate_references(self) -> "ProjectConfig":
        if self.notion.default_workspace not in self.workspaces:
            raise ConfigError(
                f"default workspace '{self.notion.default_workspace}' is not defined in [workspaces]"
            )
        return self


def load_config(path: Path) -> ProjectConfig:
    if not path.exists():
        raise ConfigError(f"configuration file not found: {path}")
    with path.open("rb") as handle:
        raw: dict[str, Any] = tomllib.load(handle)
    try:
        return ProjectConfig.model_validate(raw)
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"invalid configuration in {path}: {exc}") from exc
```

```toml
# config/examples/minimal.toml
[notion]
default_workspace = "personal"
notion_home = ".notion-home"

[workspaces.personal]
workspace_id = "workspace-id-here"

[datasources.items]
id = "datasource-id-here"
title_property = "Name"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/notion_cli/config.py src/notion_cli/errors.py tests/test_config.py config/examples/minimal.toml
git commit -m "feat: add project config loader"
```

### Task 3: Add Resolver Logic For Workspaces, Datasources, And Presets

**Files:**
- Create: `src/notion_cli/resolver.py`
- Create: `tests/test_resolver.py`

- [ ] **Step 1: Write the failing resolver tests**

```python
# tests/test_resolver.py
from notion_cli.config import ProjectConfig
from notion_cli.resolver import resolve_datasource, resolve_preset


def build_config() -> ProjectConfig:
    return ProjectConfig.model_validate(
        {
            "notion": {"default_workspace": "personal"},
            "workspaces": {"personal": {"workspace_id": "workspace-123"}},
            "datasources": {"items": {"id": "ds-123", "title_property": "Name"}},
            "bundles": {"default_item": {"properties": ["title", "status", "link"]}},
            "presets": {
                "add_item": {
                    "kind": "page_create",
                    "datasource": "items",
                    "bundle": "default_item",
                }
            },
        }
    )


def test_resolve_datasource_returns_named_entry() -> None:
    resolved = resolve_datasource(build_config(), "items")
    assert resolved.id == "ds-123"


def test_resolve_preset_returns_bundle_properties() -> None:
    resolved = resolve_preset(build_config(), "add_item")
    assert resolved.datasource_id == "ds-123"
    assert resolved.property_names == ["title", "status", "link"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_resolver.py -v`
Expected: FAIL with `ModuleNotFoundError` for `notion_cli.resolver`.

- [ ] **Step 3: Write minimal resolver implementation**

```python
# src/notion_cli/resolver.py
from __future__ import annotations

from dataclasses import dataclass

from notion_cli.config import DatasourceConfig, ProjectConfig
from notion_cli.errors import ConfigError


@dataclass(frozen=True)
class ResolvedPreset:
    name: str
    kind: str
    workspace_id: str
    datasource_name: str | None
    datasource_id: str | None
    property_names: list[str]
    youtube_enabled: bool


def resolve_workspace_id(config: ProjectConfig, alias: str | None = None) -> str:
    name = alias or config.notion.default_workspace
    try:
        return config.workspaces[name].workspace_id
    except KeyError as exc:
        raise ConfigError(f"unknown workspace alias: {name}") from exc


def resolve_datasource(config: ProjectConfig, name: str) -> DatasourceConfig:
    try:
        return config.datasources[name]
    except KeyError as exc:
        raise ConfigError(f"unknown datasource alias: {name}") from exc


def resolve_preset(config: ProjectConfig, name: str) -> ResolvedPreset:
    try:
        preset = config.presets[name]
    except KeyError as exc:
        raise ConfigError(f"unknown preset alias: {name}") from exc

    datasource_id = None
    datasource_name = preset.datasource
    if datasource_name is not None:
        datasource_id = resolve_datasource(config, datasource_name).id

    property_names: list[str] = []
    if preset.bundle is not None:
        try:
            property_names = config.bundles[preset.bundle].properties
        except KeyError as exc:
            raise ConfigError(f"unknown bundle alias: {preset.bundle}") from exc

    return ResolvedPreset(
        name=name,
        kind=preset.kind,
        workspace_id=resolve_workspace_id(config),
        datasource_name=datasource_name,
        datasource_id=datasource_id,
        property_names=property_names,
        youtube_enabled=preset.youtube,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_resolver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/notion_cli/resolver.py tests/test_resolver.py
git commit -m "feat: resolve datasources and presets from config"
```

### Task 4: Render `ntn` Commands And Execution Environment

**Files:**
- Create: `src/notion_cli/render.py`
- Create: `src/notion_cli/exec.py`
- Create: `tests/test_render.py`

- [ ] **Step 1: Write the failing render tests**

```python
# tests/test_render.py
from notion_cli.render import RenderedCommand, render_api_passthrough, render_datasource_query
from notion_cli.resolver import ResolvedPreset


def test_render_api_passthrough_preserves_args() -> None:
    rendered = render_api_passthrough(["v1/users/me"])
    assert rendered.args == ["ntn", "api", "v1/users/me"]


def test_render_datasource_query_uses_resolved_id() -> None:
    rendered = render_datasource_query("ds-123")
    assert rendered.args == ["ntn", "api", "v1/data-sources/ds-123/query"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_render.py -v`
Expected: FAIL with `ModuleNotFoundError` for `notion_cli.render`.

- [ ] **Step 3: Write command rendering and execution helpers**

```python
# src/notion_cli/render.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RenderedCommand:
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)


def render_api_passthrough(args: list[str]) -> RenderedCommand:
    return RenderedCommand(args=["ntn", "api", *args])


def render_login() -> RenderedCommand:
    return RenderedCommand(args=["ntn", "login"])


def render_doctor() -> RenderedCommand:
    return RenderedCommand(args=["ntn", "doctor"])


def render_datasource_query(datasource_id: str) -> RenderedCommand:
    return RenderedCommand(args=["ntn", "api", f"v1/data-sources/{datasource_id}/query"])
```

```python
# src/notion_cli/exec.py
from __future__ import annotations

import os
import subprocess

from notion_cli.errors import EnvironmentError, RuntimeCommandError
from notion_cli.render import RenderedCommand


def run_command(rendered: RenderedCommand, dry_run: bool = False) -> str:
    if dry_run:
        return " ".join(rendered.args)

    env = os.environ.copy()
    env.update(rendered.env)

    try:
        result = subprocess.run(
            rendered.args,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError as exc:
        raise EnvironmentError("`ntn` is not installed or not on PATH") from exc

    if result.returncode != 0:
        raise RuntimeCommandError(result.stderr.strip() or "ntn command failed")
    return result.stdout
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_render.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/notion_cli/render.py src/notion_cli/exec.py tests/test_render.py
git commit -m "feat: render and execute notion cli commands"
```

### Task 5: Add YouTube URL Normalization And Metadata Lookup

**Files:**
- Create: `src/notion_cli/youtube.py`
- Create: `tests/test_youtube.py`
- Create: `config/examples/youtube.toml`

- [ ] **Step 1: Write the failing YouTube tests**

```python
# tests/test_youtube.py
from notion_cli.youtube import normalize_youtube_url, parse_duration


def test_normalize_youtube_url_converts_short_url() -> None:
    assert (
        normalize_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_parse_duration_formats_seconds() -> None:
    assert parse_duration(3723) == "1:02:03"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_youtube.py -v`
Expected: FAIL with `ModuleNotFoundError` for `notion_cli.youtube`.

- [ ] **Step 3: Write minimal YouTube provider and example config**

```python
# src/notion_cli/youtube.py
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL

from notion_cli.errors import RuntimeCommandError


@dataclass(frozen=True)
class YoutubeMetadata:
    url: str
    title: str
    length: str


def normalize_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc in {"youtu.be"}:
        video_id = parsed.path.lstrip("/")
        return f"https://www.youtube.com/watch?v={video_id}"
    if parsed.netloc.endswith("youtube.com"):
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    return url


def parse_duration(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


def fetch_youtube_metadata(url: str) -> YoutubeMetadata:
    canonical = normalize_youtube_url(url)
    options = {"quiet": True, "skip_download": True}
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(canonical, download=False)
        except Exception as exc:
            raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}") from exc

    return YoutubeMetadata(
        url=canonical,
        title=info["title"],
        length=parse_duration(int(info["duration"])),
    )
```

```toml
# config/examples/youtube.toml
[notion]
default_workspace = "personal"
notion_home = ".notion-home"

[workspaces.personal]
workspace_id = "workspace-id-here"

[datasources.items]
id = "datasource-id-here"
title_property = "Name"

[bundles.default_item]
properties = ["title", "link", "length"]

[presets.add_youtube]
kind = "page_create"
datasource = "items"
bundle = "default_item"
youtube = true

[youtube]
provider = "no_key"
timeout_seconds = 10
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_youtube.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/notion_cli/youtube.py tests/test_youtube.py config/examples/youtube.toml
git commit -m "feat: add youtube metadata provider"
```

### Task 6: Wire The CLI Commands And Dry-Run Behavior

**Files:**
- Modify: `src/notion_cli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI behavior tests**

```python
# tests/test_cli.py
from pathlib import Path

from typer.testing import CliRunner

from notion_cli.cli import app

runner = CliRunner()


def test_resolve_datasource_command_prints_id(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]
        workspace_id = "workspace-123"

        [datasources.items]
        id = "ds-123"
        title_property = "Name"
        """.strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--config", str(config_path), "resolve", "datasource", "items"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "ds-123"


def test_api_dry_run_prints_resolved_command() -> None:
    result = runner.invoke(app, ["api", "--dry-run", "v1/users/me"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ntn api v1/users/me"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL because the Typer app does not expose the required commands yet.

- [ ] **Step 3: Write the CLI wiring**

```python
# src/notion_cli/cli.py
from __future__ import annotations

from pathlib import Path

import typer

from notion_cli.config import load_config
from notion_cli.exec import run_command
from notion_cli.render import render_api_passthrough, render_datasource_query, render_doctor, render_login
from notion_cli.resolver import resolve_datasource

app = typer.Typer(help="Config-driven wrapper around the official Notion CLI.")
resolve_app = typer.Typer(help="Resolve config aliases.")
app.add_typer(resolve_app, name="resolve")


@app.callback()
def main() -> None:
    """CLI entrypoint."""


@app.command()
def login(dry_run: bool = False) -> None:
    typer.echo(run_command(render_login(), dry_run=dry_run))


@app.command()
def doctor(dry_run: bool = False) -> None:
    typer.echo(run_command(render_doctor(), dry_run=dry_run))


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def api(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    typer.echo(run_command(render_api_passthrough(list(ctx.args)), dry_run=dry_run))


@resolve_app.command("datasource")
def resolve_datasource_command(
    name: str,
    config: Path = typer.Option(Path("notion-cli.toml"), "--config"),
) -> None:
    project = load_config(config)
    typer.echo(resolve_datasource(project, name).id)


@app.command("datasource-query")
def datasource_query(
    name: str,
    config: Path = typer.Option(Path("notion-cli.toml"), "--config"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    project = load_config(config)
    datasource = resolve_datasource(project, name)
    typer.echo(run_command(render_datasource_query(datasource.id), dry_run=dry_run))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/notion_cli/cli.py tests/test_cli.py
git commit -m "feat: wire cli commands and dry run support"
```

### Task 7: Add Preset Execution With YouTube Enrichment

**Files:**
- Modify: `src/notion_cli/render.py`
- Modify: `src/notion_cli/cli.py`
- Modify: `tests/test_render.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing preset tests**

```python
# tests/test_render.py
from notion_cli.render import render_page_create
from notion_cli.resolver import ResolvedPreset
from notion_cli.youtube import YoutubeMetadata


def test_render_page_create_uses_inline_api_assignments() -> None:
    preset = ResolvedPreset(
        name="add_youtube",
        kind="page_create",
        workspace_id="workspace-123",
        datasource_name="items",
        datasource_id="ds-123",
        property_names=["title", "link", "length"],
        youtube_enabled=True,
    )
    rendered = render_page_create(
        preset,
        {"title": "Video Title", "link": "https://www.youtube.com/watch?v=abc", "length": "3:21"},
    )
    assert rendered.args[:3] == ["ntn", "api", "v1/pages"]
    assert "parent[data_source_id]=ds-123" in rendered.args
```

```python
# tests/test_cli.py
from unittest.mock import patch


def test_preset_run_adds_youtube_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]
        workspace_id = "workspace-123"

        [datasources.items]
        id = "ds-123"

        [bundles.default_item]
        properties = ["title", "link", "length"]

        [presets.add_youtube]
        kind = "page_create"
        datasource = "items"
        bundle = "default_item"
        youtube = true
        """.strip(),
        encoding="utf-8",
    )

    with patch("notion_cli.cli.fetch_youtube_metadata") as fetch:
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video Title"
        fetch.return_value.length = "3:21"
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "preset",
                "run",
                "add_youtube",
                "--url",
                "https://youtu.be/abc",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0
    assert "parent[data_source_id]=ds-123" in result.stdout
    assert "properties[Name][title][0][text][content]=Video Title" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_render.py::test_render_page_create_uses_inline_api_assignments tests/test_cli.py::test_preset_run_adds_youtube_fields -v`
Expected: FAIL because page-create rendering and preset execution do not exist yet.

- [ ] **Step 3: Write preset rendering and command**

```python
# src/notion_cli/render.py
from notion_cli.resolver import ResolvedPreset


def render_page_create(preset: ResolvedPreset, fields: dict[str, str]) -> RenderedCommand:
    args = ["ntn", "api", "v1/pages", f"parent[data_source_id]={preset.datasource_id}"]
    if "title" in fields:
        args.append(f"properties[Name][title][0][text][content]={fields['title']}")
    if "link" in fields:
        args.append(f"properties[Link][url]={fields['link']}")
    if "length" in fields:
        args.append(f"properties[Time][rich_text][0][text][content]={fields['length']}")
    return RenderedCommand(args=args)
```

```python
# src/notion_cli/cli.py
from notion_cli.resolver import resolve_preset
from notion_cli.youtube import fetch_youtube_metadata

preset_app = typer.Typer(help="Run named presets.")
app.add_typer(preset_app, name="preset")


@preset_app.command("run")
def preset_run(
    name: str,
    url: str | None = typer.Option(None, "--url"),
    title: str | None = typer.Option(None, "--title"),
    config: Path = typer.Option(Path("notion-cli.toml"), "--config"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    project = load_config(config)
    preset = resolve_preset(project, name)
    fields: dict[str, str] = {}

    if preset.youtube_enabled:
        if url is None:
            raise typer.BadParameter("--url is required for YouTube-enabled presets")
        metadata = fetch_youtube_metadata(url)
        fields["link"] = metadata.url
        fields["title"] = metadata.title
        fields["length"] = metadata.length

    if title is not None:
        fields["title"] = title

    typer.echo(run_command(render_page_create(preset, fields), dry_run=dry_run))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_render.py::test_render_page_create_uses_inline_api_assignments tests/test_cli.py::test_preset_run_adds_youtube_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/notion_cli/render.py src/notion_cli/cli.py tests/test_render.py tests/test_cli.py
git commit -m "feat: add preset execution with youtube enrichment"
```

### Task 8: Finish Docs And Quality Gates

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Write the failing documentation checks**

```python
# tests/test_cli.py
from pathlib import Path


def test_readme_mentions_ntn_and_config_file() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "`ntn`" in readme
    assert "notion-cli.toml" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_readme_mentions_ntn_and_config_file -v`
Expected: FAIL because the README does not yet document usage and config.

- [ ] **Step 3: Write final docs**

```markdown
# README.md

# notion-cli

`notion-cli` is a Python wrapper around the official Notion CLI, `ntn`.

## Requirements

- Python 3.11+
- `ntn` installed and available on `PATH`

## Install

```bash
python -m pip install -e .[dev]
```

## Authenticate

Use the official Notion CLI for auth:

```bash
ntn login
```

## Configure

Create `notion-cli.toml` from `config/examples/minimal.toml` or `config/examples/youtube.toml`.

## Examples

```bash
notion-cli api --dry-run v1/users/me
notion-cli resolve datasource items
notion-cli datasource-query items --dry-run
notion-cli preset run add_youtube --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

## Quality Checks

```bash
pytest -v
ruff check .
mypy src
```
```

```markdown
# AGENTS.md

## Working Rules

- Keep project-specific IDs in `notion-cli.toml`, not in Python code.
- Use `ntn` for authentication and API execution instead of direct token storage.
- Run `pytest -v`, `ruff check .`, and `mypy src` after each substantial task batch.
- Prefer dry-run coverage for new CLI features before live execution support.
```

- [ ] **Step 4: Run final verification**

Run: `pytest -v`
Expected: PASS

Run: `ruff check .`
Expected: PASS

Run: `mypy src`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md AGENTS.md tests/test_cli.py
git commit -m "docs: document notion cli workflow"
```

## Self-Review

### Spec Coverage

- Official `ntn` passthrough: covered in Tasks 4 and 6.
- Config-driven aliases and presets: covered in Tasks 2, 3, 6, and 7.
- No hardcoded IDs in code: enforced by config loader and resolver tasks.
- Dry-run support and transparency: covered in Tasks 4 and 6.
- No-key YouTube metadata for title, length, and URL: covered in Task 5 and integrated in Task 7.
- Python-first repo scaffold and docs: covered in Tasks 1 and 8.

### Placeholder Scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Every task includes explicit files, test commands, implementation snippets, and commit commands.

### Type Consistency

- `ProjectConfig`, `ResolvedPreset`, `RenderedCommand`, and `YoutubeMetadata` are introduced before later tasks use them.
- CLI command names are consistent across tests, implementation snippets, and README examples.
