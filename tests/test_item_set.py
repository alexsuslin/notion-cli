from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from test_cli import write_full_config
from typer.testing import CliRunner

from notion_cli.cli import app

runner = CliRunner()
PAGE_ID = "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    path = tmp_path / "notion-cli.toml"
    write_full_config(path)
    return path


def test_set_author_only_is_offline_and_resolves_alias(config_path: Path) -> None:
    with (
        patch("notion_cli.cli.fetch_youtube_metadata", side_effect=AssertionError("network")),
        patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")),
    ):
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "set",
                "sci_pop",
                "--author",
                "Matt Pocock",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == (
        "ntn api --notion-version 2022-06-28 -X PATCH v1/pages/page-456 "
        'properties[Author][multi_select][0][name]:="Matt Pocock"'
    )


@pytest.mark.parametrize(
    "target",
    [
        PAGE_ID,
        "00000000000040008000000000000001",
        "https://www.notion.so/Video-00000000000040008000000000000001?pvs=4",
    ],
)
def test_set_accepts_page_ids_and_notion_urls(config_path: Path, target: str) -> None:
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_path),
            "item",
            "set",
            target,
            "--status",
            "In progress",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert f"v1/pages/{PAGE_ID}" in result.stdout
    assert 'properties[Status][select][name]:="In progress"' in result.stdout
    assert "properties[Date]" not in result.stdout


def test_set_multiple_explicit_fields_and_clear_tags(config_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_path),
            "item",
            "set",
            "sci_pop",
            "--title",
            'Нова "назва"',
            "--score",
            "4",
            "--date",
            "2026-09-15",
            "--project",
            "sci_pop",
            "--tags",
            "",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert 'properties[Name][title][0][text][content]:="Нова \\"назва\\""' in result.stdout
    assert 'properties[Score /5][select][name]:="⭐️⭐️⭐️⭐️"' in result.stdout
    assert 'properties[Date][date][start]:="2026-09-15"' in result.stdout
    assert 'properties[Project][relation][0][id]:="page-456"' in result.stdout
    assert "properties[Tags][multi_select]:=[]" in result.stdout
    assert "properties[Author]" not in result.stdout


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ([], "at least one"),
        (["--score", "0"], "--score"),
        (["--date", "yesterday"], "--date"),
        (["--author", "   "], "--author"),
    ],
)
def test_set_rejects_invalid_input_without_execution(
    config_path: Path,
    options: list[str],
    message: str,
) -> None:
    with patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")):
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "set",
                "sci_pop",
                *options,
            ],
        )
    assert result.exit_code != 0
    assert message in result.stderr


def test_set_rejects_unmapped_field(config_path: Path) -> None:
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace('author = "Author"', ""),
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_path),
            "item",
            "set",
            "sci_pop",
            "--author",
            "Matt Pocock",
            "--dry-run",
        ],
    )
    assert result.exit_code == 1
    assert "author" in result.stderr
    assert "mapping" in result.stderr
    assert result.stdout == ""


def test_set_live_sends_one_patch_with_configured_environment(config_path: Path) -> None:
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, stdout='{"id":"updated"}', stderr="")

    with (
        patch("notion_cli.exec.shutil.which", return_value="ntn"),
        patch("notion_cli.exec.subprocess.run", side_effect=fake_run),
    ):
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "set",
                "sci_pop",
                "--author",
                "Matt Pocock",
            ],
        )
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == '{"id":"updated"}'
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == [
        "ntn",
        "api",
        "--notion-version",
        "2022-06-28",
        "-X",
        "PATCH",
        "v1/pages/page-456",
        'properties[Author][multi_select][0][name]:="Matt Pocock"',
    ]
    assert kwargs["env"]["NOTION_WORKSPACE_ID"] == "workspace-123"


def test_add_youtube_author_override(config_path: Path) -> None:
    with patch("notion_cli.cli.fetch_youtube_metadata") as fetch:
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video"
        fetch.return_value.length = "3:21"
        fetch.return_value.author = "Inferred channel"
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "add-youtube",
                "https://youtu.be/abc",
                "--author",
                "Matt Pocock",
                "--upsert",
                "--dry-run",
            ],
        )
    assert result.exit_code == 0, result.output
    assert result.stdout.count('properties[Author][multi_select][0][name]:="Matt Pocock"') == 2
    assert "Inferred channel" not in result.stdout


@pytest.mark.parametrize(
    "target",
    [
        "missing-alias",
        "https://[notion.so/page",
        "https://example.com/00000000000040008000000000000001",
        "https://notion.so.evil.test/00000000000040008000000000000001",
        "https://www.notion.so/missing-id",
        "https://www.notion.so/00000000000040008000000000000001/extra",
    ],
)
def test_set_rejects_invalid_target_before_execution(config_path: Path, target: str) -> None:
    with patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")):
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "set",
                target,
                "--author",
                "Author",
            ],
        )
    assert result.exit_code == 1
    assert "Error:" in result.stderr
    assert result.stdout == ""


def test_set_uses_selected_datasource_and_rich_text_author(config_path: Path) -> None:
    content = config_path.read_text(encoding="utf-8")
    content = content.replace("datasources.items", "datasources.reading")
    content = content.replace('author = "multi_select"', 'author = "rich_text"')
    content = content.replace('id = "ds-123"', 'id = "ds-123"\nquery_endpoint = "data_source"')
    config_path.write_text(content, encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_path),
            "item",
            "set",
            "sci_pop",
            "--datasource",
            "reading",
            "--author",
            "Author",
            "--tags",
            "reading, reading,work",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert result.stdout.startswith("ntn api -X PATCH v1/pages/page-456 ")
    assert 'properties[Author][rich_text][0][text][content]:="Author"' in result.stdout
    assert 'properties[Tags][multi_select][0][name]:="reading"' in result.stdout
    assert 'properties[Tags][multi_select][1][name]:="work"' in result.stdout
    assert "[multi_select][2]" not in result.stdout


def test_set_reports_ntn_failure(config_path: Path) -> None:
    with (
        patch("notion_cli.exec.shutil.which", return_value="ntn"),
        patch(
            "notion_cli.exec.subprocess.run",
            return_value=subprocess.CompletedProcess(
                ["ntn"],
                1,
                stdout="",
                stderr="object_not_found: page unavailable",
            ),
        ),
    ):
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "set",
                "sci_pop",
                "--author",
                "Author",
            ],
        )
    assert result.exit_code == 1
    assert "page unavailable" in result.stderr
    assert result.stdout == ""


def test_set_uses_page_selected_in_database_url(config_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_path),
            "item",
            "set",
            "https://www.notion.so/00000000000040008000000000000002"
            "?v=00000000000040008000000000000003&p=00000000000040008000000000000001",
            "--author",
            "Author",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert f"v1/pages/{PAGE_ID}" in result.stdout


@pytest.mark.parametrize("query", ["p=bad", "p=", "p=bad&p=00000000000040008000000000000001"])
def test_set_rejects_invalid_selected_page(config_path: Path, query: str) -> None:
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_path),
            "item",
            "set",
            f"https://www.notion.so/{PAGE_ID}?{query}",
            "--author",
            "Author",
            "--dry-run",
        ],
    )
    assert result.exit_code == 1
    assert "page" in result.stderr
