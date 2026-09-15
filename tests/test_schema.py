from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from notion_cli.cli import app


@pytest.fixture
def config(tmp_path: Path) -> Path:
    path = tmp_path / "notion-cli.toml"
    path.write_text(
        """[notion]
default_workspace = "personal"
[workspaces.personal]
[datasources.items]
id = "ds-placeholder"
[datasources.items.properties]
title = "Name"
author = "Author"
[datasources.items.property_types]
author = "multi_select"
""",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    ("modern", "path"),
    [
        (False, "v1/databases/ds-placeholder"),
        (True, "v1/data_sources/ds-placeholder"),
    ],
)
def test_schema_preview_uses_matching_endpoint(config: Path, modern: bool, path: str) -> None:
    if modern:
        config.write_text(
            config.read_text(encoding="utf-8").replace(
                "[datasources.items]",
                '[datasources.items]\nquery_endpoint = "data_source"',
            ),
            encoding="utf-8",
        )
    with patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "--dry-run-json",
                "datasource",
                "schema",
                "items",
                "--check",
            ],
        )
    assert result.exit_code == 0, result.output
    plan = json.loads(result.stdout)
    assert plan["args"][-3:] == ["-X", "GET", path]
    assert plan["check"] is True
    assert "valid" not in plan


def test_schema_check_matches_mapping_overrides(config: Path) -> None:
    payload = {"properties": {"Name": {"type": "title"}, "Author": {"type": "multi_select"}}}
    with patch("notion_cli.cli.run_command", return_value=json.dumps(payload)) as run:
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "schema",
                "items",
                "--check",
            ],
        )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"datasource": "items", "valid": True, "issues": []}
    assert run.call_count == 1
    assert "GET" in run.call_args.args[0].args


def test_schema_check_reports_missing_and_mismatched_fields(config: Path) -> None:
    with patch(
        "notion_cli.cli.run_command",
        return_value=json.dumps(
            {
                "properties": {"Author": {"type": "rich_text"}},
            }
        ),
    ):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "schema",
                "items",
                "--check",
            ],
        )
    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert report["issues"] == [
        {"field": "title", "property": "Name", "expected": "title", "actual": None},
        {
            "field": "author",
            "property": "Author",
            "expected": "multi_select",
            "actual": "rich_text",
        },
    ]


@pytest.mark.parametrize("payload", [{}, {"properties": []}, {"properties": {"Name": {}}}])
def test_schema_check_rejects_malformed_schema(config: Path, payload: object) -> None:
    with patch("notion_cli.cli.run_command", return_value=json.dumps(payload)):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "schema",
                "items",
                "--check",
            ],
        )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "schema" in result.stderr


def test_schema_without_check_preserves_response(config: Path) -> None:
    response = '{"properties":{"Name":{"type":"title"}}}'
    with patch("notion_cli.cli.run_command", return_value=response):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "schema",
                "items",
            ],
        )
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == response


def test_schema_text_dry_run_does_not_claim_validation(config: Path) -> None:
    with patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "schema",
                "items",
                "--check",
                "--dry-run",
            ],
        )
    assert result.exit_code == 0, result.output
    assert (
        result.stdout.strip()
        == "ntn api --notion-version 2022-06-28 -X GET v1/databases/ds-placeholder"
    )
