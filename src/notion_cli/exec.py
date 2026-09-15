from __future__ import annotations

import os
import shutil
import subprocess

from notion_cli.errors import EnvironmentError, RuntimeCommandError
from notion_cli.render import RenderedCommand


def run_command(rendered: RenderedCommand, dry_run: bool = False) -> str:
    if dry_run:
        return " ".join(rendered.args)

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
            encoding="utf-8",
            timeout=rendered.timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeCommandError(
            f"ntn timed out after {rendered.timeout_seconds:g} seconds; "
            "the operation may have completed remotely, so check its state before retrying"
        ) from exc
    except FileNotFoundError as exc:
        raise EnvironmentError(f"`{rendered.args[0]}` is not installed or not on PATH") from exc

    if result.returncode != 0:
        raise RuntimeCommandError(result.stderr.strip() or "ntn command failed")
    return result.stdout.strip()
