from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from notion_cli.config import DatasourceConfig, PageConfig, ProjectConfig, PropertyValueType
from notion_cli.errors import ConfigError


@dataclass(frozen=True)
class ResolvedPreset:
    name: str
    kind: str
    workspace_id: str | None
    datasource_name: str | None
    datasource_id: str | None
    query_endpoint: str
    notion_version: str | None
    property_names: list[str]
    property_map: dict[str, str]
    property_types: Mapping[str, PropertyValueType]
    youtube_enabled: bool


def resolve_workspace_id(config: ProjectConfig, alias: str | None = None) -> str | None:
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


def resolve_page(config: ProjectConfig, name: str) -> PageConfig:
    try:
        return config.pages[name]
    except KeyError as exc:
        raise ConfigError(f"unknown page alias: {name}") from exc


def resolve_preset(config: ProjectConfig, name: str) -> ResolvedPreset:
    try:
        preset = config.presets[name]
    except KeyError as exc:
        raise ConfigError(f"unknown preset alias: {name}") from exc

    datasource_id = None
    datasource_name = preset.datasource
    query_endpoint = "database"
    notion_version: str | None = None
    property_map: dict[str, str] = {}
    property_types: Mapping[str, PropertyValueType] = {}
    if datasource_name is not None:
        datasource = resolve_datasource(config, datasource_name)
        datasource_id = datasource.id
        query_endpoint = datasource.query_endpoint
        notion_version = datasource.effective_notion_version()
        property_map = datasource.properties
        property_types = datasource.property_types

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
        query_endpoint=query_endpoint,
        notion_version=notion_version,
        property_names=property_names,
        property_map=property_map,
        property_types=property_types,
        youtube_enabled=preset.youtube,
    )
