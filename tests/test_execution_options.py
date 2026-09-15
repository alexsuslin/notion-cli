from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from test_cli import write_full_config
from typer.testing import CliRunner

from notion_cli.cli import app
from notion_cli.errors import RuntimeCommandError
from notion_cli.exec import run_command
from notion_cli.render import RenderedCommand, command_plan


def test_real_subprocess_preserves_arguments_and_unicode(tmp_path: Path) -> None:
    stub = tmp_path / "argument stub.py"
    stub.write_text(
        "import json, os, sys\n"
        "print(json.dumps({'args': sys.argv[1:], 'env': os.environ['NOTION_HOME']}, "
        "ensure_ascii=False))\n",
        encoding="utf-8",
    )
    args = [
        'title:="Нова назва"',
        'filter:={"url":"https://example.com/?a=1&b=2"}',
        "",
        "a'quote",
        'a"quote',
        "trailing\\",
        "$(not-a-command)",
    ]
    result = run_command(
        RenderedCommand(
            args=[sys.executable, str(stub), *args],
            env={"NOTION_HOME": "тест with spaces", "PYTHONIOENCODING": "utf-8"},
        )
    )
    assert json.loads(result) == {"args": args, "env": "тест with spaces"}


def test_command_timeout_is_applied_without_retry() -> None:
    with (
        patch("notion_cli.exec.shutil.which", return_value="ntn"),
        patch(
            "notion_cli.exec.subprocess.run", side_effect=subprocess.TimeoutExpired("ntn", 2)
        ) as run,
    ):
        with pytest.raises(RuntimeCommandError, match="timed out"):
            run_command(RenderedCommand(args=["ntn", "api", "v1/pages"], timeout_seconds=2))
    assert run.call_count == 1
    assert run.call_args.kwargs["timeout"] == 2


@pytest.mark.parametrize(("override", "expected"), [([], 7), (["--timeout", "3"], 3)])
def test_preview_timeout_precedence_and_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: list[str],
    expected: int,
) -> None:
    config = tmp_path / "notion-cli.toml"
    write_full_config(config)
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "[notion]",
            '[notion]\ntimeout_seconds = 7\nnotion_home = "local home"',
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("NOTION_API_TOKEN", "secret-never-print")
    with patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                *override,
                "--dry-run-json",
                "item",
                "set",
                "sci_pop",
                "--author",
                "Ім’я автора",
            ],
        )
    assert result.exit_code == 0, result.output
    plan = json.loads(result.stdout)
    assert plan["version"] == 1
    assert plan["kind"] == "command"
    assert plan["timeout_seconds"] == expected
    assert plan["env"] == {"NOTION_HOME": "local home", "NOTION_WORKSPACE_ID": "workspace-123"}
    assert plan["args"][-1] == 'properties[Author][multi_select][0][name]:="Ім’я автора"'
    assert "secret-never-print" not in result.stdout


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_invalid_timeout_rejected_before_execution(timeout: str) -> None:
    result = CliRunner().invoke(app, ["--timeout", timeout, "--dry-run-json", "api", "v1/users/me"])
    assert result.exit_code == 2
    assert "timeout" in result.stderr


def test_json_preview_passthrough_needs_no_config(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "--config",
            str(tmp_path / "missing.toml"),
            "--dry-run-json",
            "api",
            "v1/users/me",
        ],
    )
    assert result.exit_code == 0, result.output
    plan = json.loads(result.stdout)
    assert plan["args"] == ["ntn", "api", "v1/users/me"]
    assert plan["timeout_seconds"] == 60


def test_json_upsert_preview_shows_all_branches_without_execution(tmp_path: Path) -> None:
    config = tmp_path / "notion-cli.toml"
    write_full_config(config)
    with (
        patch("notion_cli.cli.fetch_youtube_metadata") as fetch,
        patch("notion_cli.exec.subprocess.run", side_effect=AssertionError("execution")),
    ):
        fetch.return_value.url = "https://www.youtube.com/watch?v=abc"
        fetch.return_value.title = "Video"
        fetch.return_value.length = "1:23"
        fetch.return_value.author = "Author"
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                "--timeout",
                "9",
                "--dry-run-json",
                "item",
                "add-youtube",
                "https://youtu.be/abc",
                "--upsert",
            ],
        )
    assert result.exit_code == 0, result.output
    plan = json.loads(result.stdout)
    assert plan["kind"] == "upsert"
    assert set(plan["commands"]) == {"query", "update", "create"}
    assert "PATCH" in plan["commands"]["update"]["args"]
    assert "<page_id>" in " ".join(plan["commands"]["update"]["args"])
    assert all(command["timeout_seconds"] == 9 for command in plan["commands"].values())


def test_json_plan_omits_unapproved_environment_overrides() -> None:
    plan = command_plan(
        RenderedCommand(
            args=["ntn"],
            env={
                "NOTION_HOME": "local",
                "NOTION_API_TOKEN": "secret",
                "CUSTOM_PASSWORD": "secret",
            },
        )
    )
    assert plan["env"] == {"NOTION_HOME": "local"}
    assert "secret" not in json.dumps(plan)


def test_real_subprocess_timeout(tmp_path: Path) -> None:
    stub = tmp_path / "slow.py"
    stub.write_text("import time\ntime.sleep(10)\n", encoding="utf-8")
    with pytest.raises(RuntimeCommandError, match="timed out"):
        run_command(RenderedCommand(args=[sys.executable, str(stub)], timeout_seconds=0.2))


@pytest.mark.parametrize(("override", "expected"), [([], 7), (["--timeout", "3"], 3)])
def test_live_timeout_precedence(tmp_path: Path, override: list[str], expected: int) -> None:
    config = tmp_path / "notion-cli.toml"
    write_full_config(config)
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "[notion]",
            "[notion]\ntimeout_seconds = 7",
        ),
        encoding="utf-8",
    )
    with (
        patch("notion_cli.exec.shutil.which", return_value="ntn"),
        patch(
            "notion_cli.exec.subprocess.run",
            return_value=subprocess.CompletedProcess(
                ["ntn"],
                0,
                stdout="{}",
                stderr="",
            ),
        ) as run,
    ):
        result = CliRunner().invoke(
            app,
            [
                "--config",
                str(config),
                *override,
                "datasource",
                "query",
                "items",
            ],
        )
    assert result.exit_code == 0, result.output
    assert run.call_args.kwargs["timeout"] == expected


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_invalid_config_timeout_is_rejected(tmp_path: Path, timeout: str) -> None:
    config = tmp_path / "notion-cli.toml"
    write_full_config(config)
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "[notion]",
            f"[notion]\ntimeout_seconds = {timeout}",
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        app,
        [
            "--config",
            str(config),
            "--dry-run-json",
            "datasource",
            "query",
            "items",
        ],
    )
    assert result.exit_code == 1
    assert "timeout_seconds" in result.stderr
