from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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
        [datasources.items.properties]
        title = "Name"
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
    assert result.stdout.strip() == "notion-http POST /v1/databases/ds-123/query {}"


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
        title_property = "Name"
        [datasources.items.properties]
        title = "Name"
        link = "Link"
        length = "Time"

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
    assert "parent[database_id]=ds-123" in result.stdout
    assert "properties[Name][title][0][text][content]=Video Title" in result.stdout


def test_readme_mentions_ntn_and_config_file() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "`ntn`" in readme
    assert "notion-cli.toml" in readme
