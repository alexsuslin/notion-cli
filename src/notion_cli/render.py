from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field

from notion_cli.errors import ConfigError
from notion_cli.resolver import ResolvedPreset


@dataclass(frozen=True)
class RenderedCommand:
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)


def _api_args(notion_version: str | None = None) -> list[str]:
    args = ["ntn", "api"]
    if notion_version:
        args.extend(["--notion-version", notion_version])
    return args


def _query_path(query_id: str, query_endpoint: str) -> str:
    if query_endpoint == "data_source":
        return f"v1/data_sources/{query_id}/query"
    return f"v1/databases/{query_id}/query"


def _json_input(path: str, value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return f"{path}:={encoded}"

def render_api_passthrough(args: list[str], env: dict[str, str] | None = None) -> RenderedCommand:
    return RenderedCommand(args=["ntn", "api", *args], env=env or {})


def render_exec_passthrough(args: list[str], env: dict[str, str] | None = None) -> RenderedCommand:
    return RenderedCommand(args=["ntn", *args], env=env or {})


def render_login(env: dict[str, str] | None = None) -> RenderedCommand:
    return RenderedCommand(args=["ntn", "login"], env=env or {})


def render_doctor(env: dict[str, str] | None = None) -> RenderedCommand:
    return RenderedCommand(args=["ntn", "doctor"], env=env or {})


def render_datasource_query(
    datasource_id: str,
    query_endpoint: str = "database",
    notion_version: str | None = None,
    env: dict[str, str] | None = None,
) -> RenderedCommand:
    return RenderedCommand(
        args=[*_api_args(notion_version), "-X", "POST", _query_path(datasource_id, query_endpoint)],
        env=env or {},
    )


def render_query(
    query_id: str,
    query_endpoint: str = "database",
    body_inputs: Sequence[str] | None = None,
    notion_version: str | None = None,
    env: dict[str, str] | None = None,
) -> RenderedCommand:
    return RenderedCommand(
        args=[
            *_api_args(notion_version),
            "-X",
            "POST",
            _query_path(query_id, query_endpoint),
            *(body_inputs or []),
        ],
        env=env or {},
    )


def render_database_query(
    database_id: str,
    body_inputs: Sequence[str] | None = None,
    notion_version: str | None = None,
    env: dict[str, str] | None = None,
) -> RenderedCommand:
    return render_query(
        database_id,
        query_endpoint="database",
        body_inputs=body_inputs,
        notion_version=notion_version,
        env=env,
    )


def render_page_update(
    page_id: str,
    property_inputs: Sequence[str],
    notion_version: str | None = None,
    env: dict[str, str] | None = None,
) -> RenderedCommand:
    return RenderedCommand(
        args=[*_api_args(notion_version), "-X", "PATCH", f"v1/pages/{page_id}", *property_inputs],
        env=env or {},
    )


def render_page_create(
    preset: ResolvedPreset,
    fields: dict[str, str],
    notion_version: str | None = None,
    env: dict[str, str] | None = None,
    property_inputs: Sequence[str] | None = None,
) -> RenderedCommand:
    if preset.datasource_id is None:
        raise ConfigError(f"preset '{preset.name}' does not resolve to a datasource")

    args = [*_api_args(notion_version), "v1/pages", f"parent[database_id]={preset.datasource_id}"]
    encoders = {
        "title": lambda prop, value: _json_input(
            f"properties[{prop}][title][0][text][content]",
            value,
        ),
        "link": lambda prop, value: _json_input(f"properties[{prop}][url]", value),
        "length": lambda prop, value: _json_input(
            f"properties[{prop}][rich_text][0][text][content]",
            value,
        ),
    }
    for field_name in preset.property_names:
        if field_name not in fields:
            continue
        prop_name = preset.property_map.get(field_name)
        encoder = encoders.get(field_name)
        if prop_name is None or encoder is None:
            continue
        args.append(encoder(prop_name, fields[field_name]))
    args.extend(property_inputs or [])

    return RenderedCommand(args=args, env=env or {})
