from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from notion_cli.errors import RuntimeCommandError

NOTION_API_BASE_URL = "https://api.notion.com"
DEFAULT_NOTION_VERSION = "2022-06-28"


def run_notion_http(method: str, path: str, body: str = "{}") -> str:
    token = os.environ.get("NOTION_API_TOKEN") or os.environ.get("NOTION_API_KEY")
    if not token:
        raise RuntimeCommandError("NOTION_API_TOKEN is not set")

    version = os.environ.get("NOTION_API_VERSION", DEFAULT_NOTION_VERSION)
    data = body.encode("utf-8") if body else None
    request = urllib.request.Request(
        f"{NOTION_API_BASE_URL}{path}",
        data=data,
        method=method.upper(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
            "Notion-Version": version,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload: str = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeCommandError(
            f"Notion HTTP request failed ({exc.code} {exc.reason}): {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeCommandError(f"Notion HTTP request failed: {exc.reason}") from exc

    # Normalize JSON output so downstream tools/tests can consume predictable JSON.
    try:
        normalized: str = json.dumps(json.loads(payload), ensure_ascii=False, separators=(",", ":"))
        return normalized
    except json.JSONDecodeError:
        return payload
