from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from test_cli import write_full_config
from typer.testing import CliRunner

from notion_cli.cli import app


@pytest.mark.parametrize("payload", [{}, {"results": None}, {"results": {}}, {"results": "bad"}])
def test_upsert_rejects_invalid_results_before_writing(tmp_path: Path, payload: object) -> None:
    config_path = tmp_path / "notion-cli.toml"
    write_full_config(config_path)
    with (
        patch("notion_cli.cli.fetch_youtube_metadata") as fetch,
        patch("notion_cli.cli.run_command", return_value=json.dumps(payload)) as run,
    ):
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video"
        fetch.return_value.length = "3:21"
        fetch.return_value.author = "Author"
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "add-youtube",
                "https://youtu.be/abc",
                "--upsert",
            ],
        )
    assert result.exit_code == 1
    assert "results" in result.stderr
    assert run.call_count == 1
    assert "v1/databases/ds-123/query" in run.call_args.args[0].args


@pytest.mark.parametrize("results", [[], [{"id": "existing-page"}]])
def test_upsert_chooses_create_or_patch(tmp_path: Path, results: list[dict[str, str]]) -> None:
    config_path = tmp_path / "notion-cli.toml"
    write_full_config(config_path)
    with (
        patch("notion_cli.cli.fetch_youtube_metadata") as fetch,
        patch(
            "notion_cli.cli.run_command",
            side_effect=[
                json.dumps({"results": results}),
                '{"id":"saved-page","url":"https://notion.so/saved"}',
            ],
        ) as run,
    ):
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video"
        fetch.return_value.length = "3:21"
        fetch.return_value.author = "Author"
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config_path),
                "item",
                "add-youtube",
                "https://youtu.be/abc",
                "--upsert",
            ],
        )
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "saved-page https://notion.so/saved"
    assert run.call_count == 2
    write_args = run.call_args_list[1].args[0].args
    if results:
        assert "PATCH" in write_args
        assert "v1/pages/existing-page" in write_args
        assert "parent[database_id]=ds-123" not in write_args
    else:
        assert "v1/pages" in write_args
        assert "parent[database_id]=ds-123" in write_args
