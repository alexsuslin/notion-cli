from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from test_cli import write_full_config
from typer.testing import CliRunner

from notion_cli.cli import app


@pytest.fixture
def config(tmp_path: Path) -> Path:
    path = tmp_path / "notion-cli.toml"
    write_full_config(path)
    return path


def test_query_preview_encodes_filter_sorts_cursor(config: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "--config",
            str(config),
            "--dry-run-json",
            "datasource",
            "query",
            "items",
            "--filter",
            '{"property":"Status","select":{"equals":"Done"}}',
            "--sort",
            "score:desc",
            "--sort",
            "Name:asc",
            "--page-size",
            "25",
            "--start-cursor",
            "first cursor",
            "--all",
        ],
    )
    assert result.exit_code == 0, result.output
    plan = json.loads(result.stdout)
    assert plan["kind"] == "query"
    assert plan["pagination"] == {"all": True, "cursor_field": "next_cursor"}
    assert plan["args"][-4:] == [
        'filter:={"property":"Status","select":{"equals":"Done"}}',
        'sorts:=[{"property":"Score /5","direction":"descending"},'
        '{"property":"Name","direction":"ascending"}]',
        "page_size:=25",
        'start_cursor:="first cursor"',
    ]


def test_query_all_preserves_options_on_every_page(config: Path) -> None:
    responses = [
        {"object": "list", "results": [{"id": "one"}], "has_more": True, "next_cursor": "second"},
        {"object": "list", "results": [{"id": "two"}], "has_more": False, "next_cursor": None},
    ]
    with patch("notion_cli.cli.run_command", side_effect=[json.dumps(x) for x in responses]) as run:
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "--timeout",
                "4",
                "datasource",
                "query",
                "items",
                "--filter",
                '{"property":"Tags","multi_select":{"contains":"test"}}',
                "--sort",
                "title:asc",
                "--page-size",
                "1",
                "--start-cursor",
                "first",
                "--all",
            ],
        )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {
        "object": "list",
        "results": [{"id": "one"}, {"id": "two"}],
        "has_more": False,
        "next_cursor": None,
    }
    assert run.call_count == 2
    first, second = [call.args[0] for call in run.call_args_list]
    assert first.timeout_seconds == second.timeout_seconds == 4
    assert first.args[:-1] == second.args[:-1]
    assert first.args[-1] == 'start_cursor:="first"'
    assert second.args[-1] == 'start_cursor:="second"'


@pytest.mark.parametrize(
    "payload",
    [
        {"results": [], "has_more": True, "next_cursor": None},
        {"results": [], "has_more": "false", "next_cursor": None},
        {"results": None, "has_more": False, "next_cursor": None},
        {"results": [1], "has_more": False, "next_cursor": None},
        {
            "results": [],
            "has_more": False,
            "next_cursor": None,
            "request_status": {
                "type": "incomplete",
                "incomplete_reason": "query_result_limit_reached",
            },
        },
    ],
)
def test_query_all_rejects_invalid_or_incomplete_pages(config: Path, payload: object) -> None:
    with patch("notion_cli.cli.run_command", return_value=json.dumps(payload)) as run:
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "query",
                "items",
                "--all",
            ],
        )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr
    assert run.call_count == 1


def test_query_all_rejects_cursor_cycles(config: Path) -> None:
    with patch(
        "notion_cli.cli.run_command",
        return_value=json.dumps(
            {
                "results": [],
                "has_more": True,
                "next_cursor": "same",
            }
        ),
    ) as run:
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "query",
                "items",
                "--all",
                "--start-cursor",
                "same",
            ],
        )
    assert result.exit_code == 1
    assert "cursor" in result.stderr
    assert run.call_count == 1


@pytest.mark.parametrize(
    "options",
    [
        ["--filter", "[]"],
        ["--filter", "{"],
        ["--sort", "title:sideways"],
        ["--page-size", "0"],
        ["--page-size", "101"],
        ["--start-cursor", ""],
    ],
)
def test_query_invalid_options_do_not_execute(config: Path, options: list[str]) -> None:
    with patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "query",
                "items",
                *options,
            ],
        )
    assert result.exit_code != 0
    assert result.stderr


def test_query_all_text_preview_is_offline(config: Path) -> None:
    with patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "query",
                "items",
                "--all",
                "--dry-run",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "next_cursor" in result.stdout


def test_query_all_discards_partial_output_on_later_failure(config: Path) -> None:
    with patch(
        "notion_cli.cli.run_command",
        side_effect=[
            json.dumps({"results": [{"id": "one"}], "has_more": True, "next_cursor": "next"}),
            "not valid JSON",
        ],
    ) as run:
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "query",
                "items",
                "--all",
            ],
        )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert run.call_count == 2


def test_single_page_preserves_cursor_and_raw_response(config: Path) -> None:
    response = '{"results":[],"has_more":true,"next_cursor":"next"}'
    with patch("notion_cli.cli.run_command", return_value=response) as run:
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "query",
                "items",
                "--page-size",
                "10",
            ],
        )
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == response
    assert run.call_count == 1


def test_modern_query_all_and_empty_pages(config: Path) -> None:
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "[datasources.items]",
            '[datasources.items]\nquery_endpoint = "data_source"',
        ),
        encoding="utf-8",
    )
    with patch(
        "notion_cli.cli.run_command",
        side_effect=[
            '{"results":[],"has_more":true,"next_cursor":"next"}',
            '{"results":[],"has_more":false,"next_cursor":null}',
        ],
    ) as run:
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "datasource",
                "query",
                "items",
                "--all",
            ],
        )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["results"] == []
    assert run.call_count == 2
    assert run.call_args_list[0].args[0].args == [
        "ntn",
        "api",
        "-X",
        "POST",
        "v1/data_sources/ds-123/query",
    ]


def test_query_filter_rejects_nonfinite_json(config: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "--config",
            str(config),
            "datasource",
            "query",
            "items",
            "--dry-run",
            "--filter",
            '{"number":{"equals":NaN}}',
        ],
    )
    assert result.exit_code == 1
    assert "--filter" in result.stderr
