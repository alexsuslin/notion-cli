from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from notion_cli.cli import app

runner = CliRunner()


def write_full_config(path: Path) -> None:
    path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]
        workspace_id = "workspace-123"

        [datasources.items]
        id = "ds-123"
        title_property = "Name"
        [datasources.items.properties]
        title = "Name"
        link = "Link"
        length = "Time"
        author = "Author"
        type = "Type"
        tags = "Tags"
        score = "Score /5"
        status = "Status"
        date = "Date"
        project = "Project"

        [datasources.items.property_types]
        author = "multi_select"
        status = "select"

        [pages.sci_pop]
        id = "page-456"

        [bundles.default_item]
        properties = ["title", "link", "length"]

        [bundles.youtube_item]
        properties = [
          "title",
          "link",
          "length",
          "author",
          "type",
          "tags",
          "score",
          "status",
          "date",
          "project",
        ]

        [presets.add_youtube]
        kind = "page_create"
        datasource = "items"
        bundle = "youtube_item"
        youtube = true
        """.strip(),
        encoding="utf-8",
    )


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
        [datasources.items.properties]
        title = "Name"
        """.strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--config", str(config_path), "resolve", "datasource", "items"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "ds-123"


def test_resolve_page_command_prints_id(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    write_full_config(config_path)

    result = runner.invoke(app, ["--config", str(config_path), "resolve", "page", "sci_pop"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "page-456"


def test_api_dry_run_prints_resolved_command() -> None:
    result = runner.invoke(app, ["api", "--dry-run", "v1/users/me"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ntn api v1/users/me"


def test_doctor_dry_run_works_without_config_file() -> None:
    result = runner.invoke(app, ["doctor", "--dry-run"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ntn doctor"


def test_datasource_query_dry_run_works_without_workspace_id(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]

        [datasources.items]
        id = "ds-123"
        title_property = "Name"
        [datasources.items.properties]
        title = "Name"
        """.strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["--config", str(config_path), "datasource", "query", "items", "--dry-run"],
    )

    assert result.exit_code == 0
    assert (
        result.stdout.strip()
        == "ntn api --notion-version 2022-06-28 -X POST v1/databases/ds-123/query"
    )


def test_datasource_query_dry_run_supports_data_source_endpoint(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]

        [datasources.items]
        id = "ds-123"
        query_endpoint = "data_source"
        title_property = "Name"
        [datasources.items.properties]
        title = "Name"
        """.strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["--config", str(config_path), "datasource", "query", "items", "--dry-run"],
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == "ntn api -X POST v1/data_sources/ds-123/query"


def test_preset_run_adds_youtube_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    write_full_config(config_path)

    with patch("notion_cli.cli.fetch_youtube_metadata") as fetch:
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video Title"
        fetch.return_value.length = "3:21"
        fetch.return_value.author = "Channel Name"
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
    assert "ntn api --notion-version 2022-06-28 v1/pages" in result.stdout
    assert "parent[database_id]=ds-123" in result.stdout
    assert "properties[Name][title][0][text][content]=Video Title" in result.stdout


def test_item_add_youtube_dry_run_supports_schema_type_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    write_full_config(config_path)

    with patch("notion_cli.cli.fetch_youtube_metadata") as fetch:
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video Title"
        fetch.return_value.length = "3:21"
        fetch.return_value.author = "Channel Name"
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "add-youtube",
                "https://youtu.be/abc",
                "--score",
                "4",
                "--project",
                "sci_pop",
                "--tags",
                "sci-pop,learning",
                "--done",
                "--date",
                "2026-06-22",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0
    assert "ntn api --notion-version 2022-06-28 v1/pages" in result.stdout
    assert "parent[database_id]=ds-123" in result.stdout
    assert "properties[Author][multi_select][0][name]=Channel Name" in result.stdout
    assert "properties[Type][select][name]=Video" in result.stdout
    assert "properties[Score /5][select][name]=⭐️⭐️⭐️⭐️" in result.stdout
    assert "properties[Tags][multi_select][0][name]=youtube" in result.stdout
    assert "properties[Tags][multi_select][1][name]=sci-pop" in result.stdout
    assert "properties[Project][relation][0][id]=page-456" in result.stdout
    assert "properties[Status][select][name]=Done" in result.stdout
    assert "properties[Date][date][start]=2026-06-22" in result.stdout


def test_item_add_youtube_upsert_dry_run_prints_query_update_and_create(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    write_full_config(config_path)

    with patch("notion_cli.cli.fetch_youtube_metadata") as fetch:
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video Title"
        fetch.return_value.length = "3:21"
        fetch.return_value.author = "Channel Name"
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "add-youtube",
                "https://youtu.be/abc",
                "--upsert",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert lines[0] == (
        "ntn api --notion-version 2022-06-28 -X POST v1/databases/ds-123/query "
        "filter:={\"property\":\"Link\",\"url\":{\"equals\":"
        "\"https://www.youtube.com/watch?v=abc\"}} "
        "page_size:=1"
    )
    assert lines[1].startswith(
        "# if existing page found: ntn api --notion-version 2022-06-28 -X PATCH v1/pages/<page_id>"
    )
    assert lines[2].startswith(
        "# otherwise create: ntn api --notion-version 2022-06-28 v1/pages "
        "parent[database_id]=ds-123"
    )


def test_readme_mentions_ntn_and_config_file() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "`ntn`" in readme
    assert "notion-cli.toml" in readme
