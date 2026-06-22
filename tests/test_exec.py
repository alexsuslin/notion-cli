from __future__ import annotations

import subprocess

from notion_cli.exec import run_command
from notion_cli.render import RenderedCommand


def test_run_command_resolves_executable_path(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_run(args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr("notion_cli.exec.shutil.which", lambda name: "C:\\tools\\ntn.CMD")
    monkeypatch.setattr("notion_cli.exec.subprocess.run", fake_run)

    output = run_command(RenderedCommand(args=["ntn", "--version"]))

    assert output == "ok"
    assert calls["args"] == ["C:\\tools\\ntn.CMD", "--version"]
