from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from notion_cli.errors import ConfigError


class NotionSettings(BaseModel):
    default_workspace: str
    notion_home: str | None = None


class WorkspaceConfig(BaseModel):
    workspace_id: str | None = None


class DatasourceConfig(BaseModel):
    id: str
    title_property: str = "Name"
    properties: dict[str, str] = Field(default_factory=dict)


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
    provider: str = "no_key"
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
