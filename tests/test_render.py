from __future__ import annotations

from notion_cli.render import render_api_passthrough, render_datasource_query, render_page_create
from notion_cli.resolver import ResolvedPreset


def test_render_api_passthrough_preserves_args() -> None:
    rendered = render_api_passthrough(["v1/users/me"])
    assert rendered.args == ["ntn", "api", "v1/users/me"]


def test_render_datasource_query_uses_resolved_id() -> None:
    rendered = render_datasource_query("ds-123")
    assert rendered.args == ["notion-http", "POST", "/v1/databases/ds-123/query", "{}"]


def test_render_page_create_uses_configured_property_names() -> None:
    preset = ResolvedPreset(
        name="add_youtube",
        kind="page_create",
        workspace_id="workspace-123",
        datasource_name="items",
        datasource_id="ds-123",
        property_names=["title", "link", "length"],
        property_map={"title": "Name", "link": "Link", "length": "Time"},
        youtube_enabled=True,
    )

    rendered = render_page_create(
        preset,
        {"title": "Video Title", "link": "https://www.youtube.com/watch?v=abc", "length": "3:21"},
    )

    assert rendered.args[:3] == ["ntn", "api", "v1/pages"]
    assert "parent[database_id]=ds-123" in rendered.args
    assert "properties[Name][title][0][text][content]=Video Title" in rendered.args
