from __future__ import annotations

from pathlib import Path

import pytest

from notion_cli.config import CONFIG_ENV_VAR, load_config, resolve_config_path, user_config_path
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

        [datasources.items.property_types]
        status = "select"
        """.strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.notion.default_workspace == "personal"
    assert config.datasources["items"].id == "datasource-123"
    assert config.datasources["items"].properties["length"] == "Time"
    assert config.datasources["items"].property_types["status"] == "select"


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


def test_resolve_config_path_prefers_explicit_path(tmp_path: Path) -> None:
    explicit = tmp_path / "custom.toml"
    resolved = resolve_config_path(explicit, {}, cwd=tmp_path, home=tmp_path)
    assert resolved == explicit


def test_resolve_config_path_uses_environment_override(tmp_path: Path) -> None:
    override = tmp_path / "env.toml"
    resolved = resolve_config_path(
        None,
        {CONFIG_ENV_VAR: str(override)},
        cwd=tmp_path,
        home=tmp_path,
    )
    assert resolved == override


def test_resolve_config_path_prefers_local_file_before_user_config(tmp_path: Path) -> None:
    local_config = tmp_path / "notion-cli.toml"
    local_config.write_text("", encoding="utf-8")
    resolved = resolve_config_path(None, {}, cwd=tmp_path, home=tmp_path)
    assert resolved == local_config


def test_resolve_config_path_falls_back_to_xdg_user_config(tmp_path: Path) -> None:
    xdg_home = tmp_path / "xdg"
    resolved = resolve_config_path(
        None,
        {"XDG_CONFIG_HOME": str(xdg_home)},
        cwd=tmp_path,
        home=tmp_path,
    )
    assert resolved == xdg_home / "notion-cli" / "notion-cli.toml"


def test_user_config_path_uses_windows_appdata_when_available(tmp_path: Path) -> None:
    appdata = tmp_path / "appdata"
    resolved = user_config_path(
        {"APPDATA": str(appdata)},
        home=tmp_path,
        platform="win32",
    )
    assert resolved == appdata / "notion-cli" / "notion-cli.toml"
