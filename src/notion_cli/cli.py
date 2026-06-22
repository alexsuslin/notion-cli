from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer

from notion_cli.config import ProjectConfig, load_config
from notion_cli.errors import NotionCliError
from notion_cli.exec import run_command
from notion_cli.render import (
    RenderedCommand,
    render_api_passthrough,
    render_datasource_query,
    render_doctor,
    render_exec_passthrough,
    render_login,
    render_page_create,
)
from notion_cli.resolver import resolve_datasource, resolve_preset
from notion_cli.youtube import fetch_youtube_metadata

app = typer.Typer(help="Config-driven wrapper around the official Notion CLI.")
resolve_app = typer.Typer(help="Resolve config aliases.")
datasource_app = typer.Typer(help="Run datasource operations.")
preset_app = typer.Typer(help="Run named presets.")
app.add_typer(resolve_app, name="resolve")
app.add_typer(datasource_app, name="datasource")
app.add_typer(preset_app, name="preset")
CONFIG_OPTION = typer.Option(Path("notion-cli.toml"), "--config")
VERBOSE_OPTION = typer.Option(False, "--verbose")


@dataclass
class AppState:
    config_path: Path
    verbose: bool = False


def _command_env(config: ProjectConfig, workspace_id: str | None = None) -> dict[str, str]:
    env: dict[str, str] = {}
    if config.notion.notion_home:
        env["NOTION_HOME"] = config.notion.notion_home
    if workspace_id:
        env["NOTION_WORKSPACE_ID"] = workspace_id
    return env


def _config_from_context(ctx: typer.Context) -> ProjectConfig:
    state = ctx.obj
    if not isinstance(state, AppState):
        raise RuntimeError("application state was not initialized")
    return load_config(state.config_path)


def _optional_config_from_context(ctx: typer.Context) -> ProjectConfig | None:
    state = ctx.obj
    if not isinstance(state, AppState):
        raise RuntimeError("application state was not initialized")
    if not state.config_path.exists():
        return None
    return load_config(state.config_path)


def _run(rendered: RenderedCommand, dry_run: bool) -> None:
    try:
        typer.echo(run_command(rendered, dry_run=dry_run))
    except NotionCliError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = CONFIG_OPTION,
    verbose: bool = VERBOSE_OPTION,
) -> None:
    ctx.obj = AppState(config_path=config, verbose=verbose)


@app.command()
def login(ctx: typer.Context, dry_run: bool = False) -> None:
    config = _optional_config_from_context(ctx)
    env = _command_env(config) if config is not None else {}
    _run(render_login(env), dry_run=dry_run)


@app.command()
def doctor(ctx: typer.Context, dry_run: bool = False) -> None:
    config = _optional_config_from_context(ctx)
    env = _command_env(config) if config is not None else {}
    _run(render_doctor(env), dry_run=dry_run)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def api(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    _run(render_api_passthrough(list(ctx.args)), dry_run=dry_run)


@app.command("exec", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def exec_command(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    _run(render_exec_passthrough(list(ctx.args)), dry_run=dry_run)


@resolve_app.command("datasource")
def resolve_datasource_command(ctx: typer.Context, name: str) -> None:
    project = _config_from_context(ctx)
    typer.echo(resolve_datasource(project, name).id)


@resolve_app.command("preset")
def resolve_preset_command(ctx: typer.Context, name: str) -> None:
    project = _config_from_context(ctx)
    preset = resolve_preset(project, name)
    typer.echo(preset.datasource_id or "")


@datasource_app.command("query")
def datasource_query(
    ctx: typer.Context,
    name: str,
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    project = _config_from_context(ctx)
    datasource = resolve_datasource(project, name)
    env = _command_env(project)
    _run(render_datasource_query(datasource.id, env=env), dry_run=dry_run)


@preset_app.command("run")
def preset_run(
    ctx: typer.Context,
    name: str,
    url: str | None = typer.Option(None, "--url"),
    title: str | None = typer.Option(None, "--title"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    project = _config_from_context(ctx)
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

    env = _command_env(project, workspace_id=preset.workspace_id)
    _run(render_page_create(preset, fields, env=env), dry_run=dry_run)
