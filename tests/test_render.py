from __future__ import annotations

from notion_cli.render import (
    render_api_passthrough,
    render_database_query,
    render_datasource_query,
    render_page_create,
    render_page_update,
    render_query,
)
from notion_cli.resolver import ResolvedPreset


def test_render_api_passthrough_preserves_args() -> None:
    rendered = render_api_passthrough(["v1/users/me"])
    assert rendered.args == ["ntn", "api", "v1/users/me"]


def test_render_datasource_query_uses_resolved_id() -> None:
    rendered = render_datasource_query("ds-123", notion_version="2022-06-28")
    assert rendered.args == [
        "ntn",
        "api",
        "--notion-version",
        "2022-06-28",
        "-X",
        "POST",
        "v1/databases/ds-123/query",
    ]


def test_render_query_supports_data_source_endpoint() -> None:
    rendered = render_query("ds-123", query_endpoint="data_source")
    assert rendered.args == ["ntn", "api", "-X", "POST", "v1/data_sources/ds-123/query"]


def test_render_database_query_supports_inline_filters() -> None:
    rendered = render_database_query(
        "ds-123",
        ['filter:={"property":"Link","url":{"equals":"https://example.com"}}', "page_size:=1"],
    )
    assert rendered.args == [
        "ntn",
        "api",
        "-X",
        "POST",
        "v1/databases/ds-123/query",
        'filter:={"property":"Link","url":{"equals":"https://example.com"}}',
        "page_size:=1",
    ]


def test_render_page_create_uses_configured_property_names() -> None:
    preset = ResolvedPreset(
        name="add_youtube",
        kind="page_create",
        workspace_id="workspace-123",
        datasource_name="items",
        datasource_id="ds-123",
        query_endpoint="database",
        notion_version="2022-06-28",
        property_names=["title", "link", "length"],
        property_map={"title": "Name", "link": "Link", "length": "Time"},
        property_types={},
        youtube_enabled=True,
    )

    rendered = render_page_create(
        preset,
        {"title": "Video Title", "link": "https://www.youtube.com/watch?v=abc", "length": "3:21"},
        notion_version=preset.notion_version,
    )

    assert rendered.args[:5] == ["ntn", "api", "--notion-version", "2022-06-28", "v1/pages"]
    assert "parent[database_id]=ds-123" in rendered.args
    assert "properties[Name][title][0][text][content]=Video Title" in rendered.args


def test_render_page_update_uses_patch_method() -> None:
    rendered = render_page_update(
        "page-123",
        ["properties[Status][status][name]=Done", "properties[Date][date][start]=2026-06-22"],
        notion_version="2022-06-28",
    )
    assert rendered.args == [
        "ntn",
        "api",
        "--notion-version",
        "2022-06-28",
        "-X",
        "PATCH",
        "v1/pages/page-123",
        "properties[Status][status][name]=Done",
        "properties[Date][date][start]=2026-06-22",
    ]
