from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import typer

from notion_cli.config import ProjectConfig, load_config, resolve_config_path
from notion_cli.errors import ConfigError, NotionCliError, RuntimeCommandError
from notion_cli.exec import run_command
from notion_cli.render import (
    RenderedCommand,
    render_api_passthrough,
    render_database_query,
    render_datasource_query,
    render_doctor,
    render_exec_passthrough,
    render_login,
    render_page_create,
    render_page_update,
)
from notion_cli.resolver import resolve_datasource, resolve_page, resolve_preset
from notion_cli.youtube import fetch_youtube_metadata

app = typer.Typer(help="Config-driven wrapper around the official Notion CLI.")
resolve_app = typer.Typer(help="Resolve config aliases.")
datasource_app = typer.Typer(help="Run datasource operations.")
preset_app = typer.Typer(help="Run named presets.")
item_app = typer.Typer(help="Run first-class item workflows.")
app.add_typer(resolve_app, name="resolve")
app.add_typer(datasource_app, name="datasource")
app.add_typer(preset_app, name="preset")
app.add_typer(item_app, name="item")
CONFIG_OPTION = typer.Option(None, "--config")
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


def _command_text(rendered: RenderedCommand) -> str:
    return run_command(rendered, dry_run=True)


def _require_json_output(rendered: RenderedCommand) -> dict[str, Any]:
    output = run_command(rendered)
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeCommandError("expected JSON response from Notion API") from exc
    if not isinstance(payload, dict):
        raise RuntimeCommandError("expected JSON object response from Notion API")
    return payload


def _render_optional_title(field_name: str, property_name: str, value: str) -> list[str]:
    if field_name == "title":
        return [f"properties[{property_name}][title][0][text][content]={value}"]
    return [f"properties[{property_name}][rich_text][0][text][content]={value}"]


def _property_inputs(property_map: dict[str, str], values: dict[str, object]) -> list[str]:
    encoders: dict[str, Any] = {
        "title": lambda prop, value: [f"properties[{prop}][title][0][text][content]={value}"],
        "link": lambda prop, value: [f"properties[{prop}][url]={value}"],
        "length": lambda prop, value: _render_optional_title("length", prop, str(value)),
        "author": lambda prop, value: _render_optional_title("author", prop, str(value)),
        "score": lambda prop, value: [f"properties[{prop}][select][name]={value}"],
        "type": lambda prop, value: [f"properties[{prop}][select][name]={value}"],
        "status": lambda prop, value: [f"properties[{prop}][status][name]={value}"],
        "date": lambda prop, value: [f"properties[{prop}][date][start]={value}"],
        "project": lambda prop, value: [f"properties[{prop}][relation][0][id]={value}"],
        "tags": lambda prop, value: [
            f"properties[{prop}][multi_select][{index}][name]={tag}"
            for index, tag in enumerate(value)
        ],
    }
    inputs: list[str] = []
    for field_name, value in values.items():
        property_name = property_map.get(field_name)
        if property_name is None:
            continue
        encoder = encoders.get(field_name)
        if encoder is None:
            continue
        inputs.extend(encoder(property_name, value))
    return inputs


def _score_value(score: int | None) -> str | None:
    if score is None:
        return None
    if score < 1 or score > 5:
        raise typer.BadParameter("--score must be between 1 and 5")
    return "⭐️" * score


def _resolve_date(value: str | None, *, done: bool) -> str | None:
    if value is None:
        if done:
            return date.today().isoformat()
        return None
    if value == "today":
        return date.today().isoformat()
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise typer.BadParameter("--date must be YYYY-MM-DD or 'today'") from exc


def _split_tags(value: str | None) -> list[str]:
    if value is None:
        return []
    tags = [tag.strip() for tag in value.split(",")]
    return [tag for tag in tags if tag]


def _upsert_plan(
    query_command: RenderedCommand,
    update_command: RenderedCommand,
    create_command: RenderedCommand,
) -> str:
    return "\n".join(
        [
            _command_text(query_command),
            f"# if existing page found: {_command_text(update_command)}",
            f"# otherwise create: {_command_text(create_command)}",
        ]
    )


def _page_summary(payload: dict[str, Any]) -> str:
    page_id = payload.get("id", "")
    page_url = payload.get("url", "")
    return f"{page_id} {page_url}".strip()


@app.callback()
def main(
    ctx: typer.Context,
    config: Path | None = CONFIG_OPTION,
    verbose: bool = VERBOSE_OPTION,
) -> None:
    ctx.obj = AppState(config_path=resolve_config_path(config), verbose=verbose)


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


@resolve_app.command("page")
def resolve_page_command(ctx: typer.Context, name: str) -> None:
    project = _config_from_context(ctx)
    typer.echo(resolve_page(project, name).id)


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


@item_app.command("add-youtube")
def item_add_youtube(
    ctx: typer.Context,
    url: str,
    score: int | None = typer.Option(None, "--score"),
    project: str | None = typer.Option(None, "--project"),
    tags: str | None = typer.Option(None, "--tags"),
    upsert: bool = typer.Option(False, "--upsert"),
    done: bool = typer.Option(False, "--done"),
    completed_date: str | None = typer.Option(None, "--date"),
    preset_name: str = typer.Option("add_youtube", "--preset"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    project_config = _config_from_context(ctx)
    preset = resolve_preset(project_config, preset_name)
    if not preset.youtube_enabled:
        raise ConfigError(f"preset '{preset_name}' is not configured for YouTube enrichment")
    if preset.datasource_id is None:
        raise ConfigError(f"preset '{preset_name}' does not resolve to a datasource")

    metadata = fetch_youtube_metadata(url)
    property_values: dict[str, object] = {
        "title": metadata.title,
        "link": metadata.url,
        "length": metadata.length,
        "author": metadata.author,
        "type": "Video",
    }
    if score_value := _score_value(score):
        property_values["score"] = score_value
    if project is not None:
        property_values["project"] = resolve_page(project_config, project).id
    merged_tags = ["youtube", *_split_tags(tags)]
    deduped_tags = list(dict.fromkeys(merged_tags))
    if deduped_tags:
        property_values["tags"] = deduped_tags
    resolved_date = _resolve_date(completed_date, done=done)
    if done:
        property_values["status"] = "Done"
    if resolved_date is not None:
        property_values["date"] = resolved_date

    env = _command_env(project_config, workspace_id=preset.workspace_id)
    property_inputs = _property_inputs(preset.property_map, property_values)
    create_command = render_page_create(preset, {}, env=env, property_inputs=property_inputs)

    if not upsert:
        _run(create_command, dry_run=dry_run)
        return

    link_property = preset.property_map.get("link")
    if link_property is None:
        raise ConfigError(f"preset '{preset_name}' does not define a link property mapping")
    query_inputs = [
        f"filter[property]={link_property}",
        f"filter[url][equals]={metadata.url}",
        "page_size:=1",
    ]
    query_command = render_database_query(preset.datasource_id, query_inputs, env=env)
    update_command = render_page_update("<page_id>", property_inputs, env=env)
    if dry_run:
        typer.echo(_upsert_plan(query_command, update_command, create_command))
        return

    query_result = _require_json_output(query_command)
    raw_results = query_result.get("results", [])
    results = raw_results if isinstance(raw_results, list) else []
    if results:
        first_result = results[0]
        if not isinstance(first_result, dict):
            raise RuntimeCommandError("unexpected page query result payload")
        page_id = first_result.get("id")
        if not isinstance(page_id, str) or not page_id:
            raise RuntimeCommandError("page query result did not include an id")
        update_result = _require_json_output(render_page_update(page_id, property_inputs, env=env))
        typer.echo(_page_summary(update_result))
        return

    create_result = _require_json_output(create_command)
    typer.echo(_page_summary(create_result))
