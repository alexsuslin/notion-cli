from __future__ import annotations

from dataclasses import dataclass, field

from notion_cli.resolver import ResolvedPreset


@dataclass(frozen=True)
class RenderedCommand:
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)


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
    env: dict[str, str] | None = None,
) -> RenderedCommand:
    return RenderedCommand(
        args=["notion-http", "POST", f"/v1/databases/{datasource_id}/query", "{}"],
        env=env or {},
    )


def render_page_create(
    preset: ResolvedPreset,
    fields: dict[str, str],
    env: dict[str, str] | None = None,
) -> RenderedCommand:
    args = ["ntn", "api", "v1/pages", f"parent[database_id]={preset.datasource_id}"]
    encoders = {
        "title": lambda prop, value: f"properties[{prop}][title][0][text][content]={value}",
        "link": lambda prop, value: f"properties[{prop}][url]={value}",
        "length": lambda prop, value: f"properties[{prop}][rich_text][0][text][content]={value}",
    }

    for field_name in preset.property_names:
        if field_name not in fields:
            continue
        prop_name = preset.property_map.get(field_name)
        encoder = encoders.get(field_name)
        if prop_name is None or encoder is None:
            continue
        args.append(encoder(prop_name, fields[field_name]))

    return RenderedCommand(args=args, env=env or {})
