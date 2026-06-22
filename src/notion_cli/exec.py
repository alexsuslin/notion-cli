from __future__ import annotations

import os
import shutil
import subprocess

from notion_cli.errors import EnvironmentError, RuntimeCommandError
from notion_cli.http_api import run_notion_http
from notion_cli.render import RenderedCommand


def run_command(rendered: RenderedCommand, dry_run: bool = False) -> str:
    if dry_run:
        return " ".join(rendered.args)

    if rendered.args[0] == "notion-http":
        method = rendered.args[1]
        path = rendered.args[2]
        body = rendered.args[3] if len(rendered.args) > 3 else "{}"
        env = os.environ.copy()
        env.update(rendered.env)
        old_env = os.environ.copy()
        try:
            os.environ.clear()
            os.environ.update(env)
            return run_notion_http(method, path, body)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    env = os.environ.copy()
    env.update(rendered.env)
    executable = shutil.which(rendered.args[0])
    if executable is None:
        raise EnvironmentError(f"`{rendered.args[0]}` is not installed or not on PATH")
    args = [executable, *rendered.args[1:]]

    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError as exc:
        raise EnvironmentError(f"`{rendered.args[0]}` is not installed or not on PATH") from exc

    if result.returncode != 0:
        raise RuntimeCommandError(result.stderr.strip() or "ntn command failed")
    return result.stdout.strip()
