from __future__ import annotations

from notion_cli.config import ProjectConfig
from notion_cli.resolver import resolve_datasource, resolve_preset


def build_config() -> ProjectConfig:
    return ProjectConfig.model_validate(
        {
            "notion": {"default_workspace": "personal"},
            "workspaces": {"personal": {"workspace_id": "workspace-123"}},
            "datasources": {
                "items": {
                    "id": "ds-123",
                    "title_property": "Name",
                    "properties": {
                        "title": "Name",
                        "link": "Link",
                        "length": "Time",
                    },
                }
            },
            "bundles": {"default_item": {"properties": ["title", "link", "length"]}},
            "presets": {
                "add_youtube": {
                    "kind": "page_create",
                    "datasource": "items",
                    "bundle": "default_item",
                    "youtube": True,
                }
            },
        }
    )


def test_resolve_datasource_returns_named_entry() -> None:
    resolved = resolve_datasource(build_config(), "items")
    assert resolved.id == "ds-123"


def test_resolve_preset_returns_property_mapping() -> None:
    resolved = resolve_preset(build_config(), "add_youtube")
    assert resolved.datasource_id == "ds-123"
    assert resolved.property_names == ["title", "link", "length"]
    assert resolved.property_map["length"] == "Time"


def test_resolve_preset_keeps_workspace_optional() -> None:
    config = ProjectConfig.model_validate(
        {
            "notion": {"default_workspace": "personal"},
            "workspaces": {"personal": {}},
            "datasources": {
                "items": {
                    "id": "ds-123",
                    "title_property": "Name",
                    "properties": {"title": "Name"},
                }
            },
            "bundles": {"default_item": {"properties": ["title"]}},
            "presets": {
                "add_item": {
                    "kind": "page_create",
                    "datasource": "items",
                    "bundle": "default_item",
                }
            },
        }
    )

    resolved = resolve_preset(config, "add_item")
    assert resolved.workspace_id is None
