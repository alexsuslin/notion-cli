from __future__ import annotations

import os
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from notion_cli.errors import ConfigError

CONFIG_ENV_VAR = "NOTION_CLI_CONFIG"
CONFIG_FILENAME = "notion-cli.toml"
CONFIG_DIRNAME = "notion-cli"
LEGACY_DATABASE_NOTION_VERSION = "2022-06-28"


class NotionSettings(BaseModel):
    default_workspace: str
    notion_home: str | None = None


class WorkspaceConfig(BaseModel):
    workspace_id: str | None = None


class DatasourceConfig(BaseModel):
    id: str
    title_property: str = "Name"
    query_endpoint: Literal["database", "data_source"] = "database"
    notion_version: str | None = None
    properties: dict[str, str] = Field(default_factory=dict)

    def effective_notion_version(self) -> str | None:
        if self.notion_version is not None:
            return self.notion_version
        if self.query_endpoint == "database":
            return LEGACY_DATABASE_NOTION_VERSION
        return None


class PageConfig(BaseModel):
    id: str


class BundleConfig(BaseModel):
    properties: list[str] = Field(default_factory=list)


class PresetConfig(BaseModel):
    kind: str
    datasource: str | None = None
    bundle: str | None = None
    youtube: bool = False


class YoutubeConfig(BaseModel):
    provider: Literal["no_key", "api_key"] = "no_key"
    timeout_seconds: int = 10


class ProjectConfig(BaseModel):
    notion: NotionSettings
    workspaces: dict[str, WorkspaceConfig] = Field(default_factory=dict)
    datasources: dict[str, DatasourceConfig] = Field(default_factory=dict)
    pages: dict[str, PageConfig] = Field(default_factory=dict)
    bundles: dict[str, BundleConfig] = Field(default_factory=dict)
    presets: dict[str, PresetConfig] = Field(default_factory=dict)
    youtube: YoutubeConfig = Field(default_factory=YoutubeConfig)

    @model_validator(mode="after")
    def validate_references(self) -> ProjectConfig:
        if self.notion.default_workspace not in self.workspaces:
            raise ConfigError(
                "default workspace "
                f"'{self.notion.default_workspace}' is not defined in [workspaces]"
            )
        return self


def load_config(path: Path) -> ProjectConfig:
    if not path.exists():
        raise ConfigError(f"configuration file not found: {path}")

    with path.open("rb") as handle:
        raw: dict[str, Any] = tomllib.load(handle)

    try:
        return ProjectConfig.model_validate(raw)
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"invalid configuration in {path}: {exc}") from exc


def user_config_path(
    env: Mapping[str, str] | None = None,
    *,
    home: Path | None = None,
    platform: str | None = None,
) -> Path:
    active_env = env or os.environ
    active_platform = platform or sys.platform
    if xdg_config_home := active_env.get("XDG_CONFIG_HOME"):
        return Path(xdg_config_home).expanduser() / CONFIG_DIRNAME / CONFIG_FILENAME
    if active_platform.startswith("win"):
        if appdata := active_env.get("APPDATA"):
            return Path(appdata).expanduser() / CONFIG_DIRNAME / CONFIG_FILENAME
        base_home = (home or Path.home()).expanduser()
        return base_home / "AppData" / "Roaming" / CONFIG_DIRNAME / CONFIG_FILENAME
    base_home = (home or Path.home()).expanduser()
    return base_home / ".config" / CONFIG_DIRNAME / CONFIG_FILENAME


def resolve_config_path(
    explicit: Path | None,
    env: Mapping[str, str] | None = None,
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    platform: str | None = None,
) -> Path:
    if explicit is not None:
        return explicit.expanduser()

    active_env = env or os.environ
    if env_path := active_env.get(CONFIG_ENV_VAR):
        return Path(env_path).expanduser()

    project_root = (cwd or Path.cwd()).expanduser()
    local_path = project_root / CONFIG_FILENAME
    if local_path.exists():
        return local_path

    return user_config_path(active_env, home=home, platform=platform)
