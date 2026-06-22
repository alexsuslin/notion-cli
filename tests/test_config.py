from __future__ import annotations

from pathlib import Path

import pytest

from notion_cli.config import load_config
from notion_cli.errors import ConfigError


def test_load_config_reads_named_datasource(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]
        workspace_id = "workspace-123"

        [datasources.items]
        id = "datasource-123"
        title_property = "Name"
        [datasources.items.properties]
        title = "Name"
        link = "Link"
        length = "Time"
        """.strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.notion.default_workspace == "personal"
    assert config.datasources["items"].id == "datasource-123"
    assert config.datasources["items"].properties["length"] == "Time"


def test_load_config_rejects_missing_workspace_reference(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "missing"
        """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="default workspace"):
        load_config(config_path)


def test_load_config_allows_workspace_alias_without_workspace_id(tmp_path: Path) -> None:
    config_path = tmp_path / "notion-cli.toml"
    config_path.write_text(
        """
        [notion]
        default_workspace = "personal"

        [workspaces.personal]

        [datasources.items]
        id = "datasource-123"
        title_property = "Name"
        [datasources.items.properties]
        title = "Name"
        link = "Link"
        length = "Time"
        """.strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.workspaces["personal"].workspace_id is None
