from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Any

from notion_cli.config import DatasourceConfig
from notion_cli.errors import ConfigError, RuntimeCommandError
from notion_cli.render import RenderedCommand


def query_inputs(
    datasource: DatasourceConfig,
    filter_json: str | None,
    sorts: Sequence[str],
    page_size: int | None,
    start_cursor: str | None,
) -> list[str]:
    body: dict[str, object] = {}
    if filter_json is not None:
        try:
            query_filter = json.loads(filter_json)
            if not isinstance(query_filter, dict):
                raise ValueError("expected an object")
            # Notion JSON does not accept NaN or Infinity, even nested inside filters.
            json.dumps(query_filter, allow_nan=False)
        except ValueError as exc:
            raise ConfigError("--filter must be a valid JSON object") from exc
        body["filter"] = query_filter

    sort_values = []
    for sort in sorts:
        field_name, separator, direction = sort.rpartition(":")
        if not separator or not field_name.strip() or direction not in {"asc", "desc"}:
            raise ConfigError("--sort must be PROPERTY:asc or PROPERTY:desc")
        sort_values.append(
            {
                "property": datasource.properties.get(field_name, field_name),
                "direction": "ascending" if direction == "asc" else "descending",
            }
        )
    if sort_values:
        body["sorts"] = sort_values
    if page_size is not None:
        if not 1 <= page_size <= 100:
            raise ConfigError("--page-size must be between 1 and 100")
        body["page_size"] = page_size
    if start_cursor is not None:
        if not start_cursor.strip():
            raise ConfigError("--start-cursor must not be empty")
        body["start_cursor"] = start_cursor
    return [
        f"{key}:={json.dumps(value, ensure_ascii=False, separators=(',', ':'))}"
        for key, value in body.items()
    ]


def query_all(
    command: RenderedCommand,
    read_page: Callable[[RenderedCommand], dict[str, Any]],
    start_cursor: str | None = None,
) -> dict[str, Any]:
    """Follow cursors and emit a complete result only after every page is validated."""
    seen = {start_cursor} if start_cursor is not None else set()
    results: list[dict[str, Any]] = []
    combined: dict[str, Any] | None = None
    base_args = [arg for arg in command.args if not arg.startswith("start_cursor:=")]
    while True:
        page = read_page(command)
        entries = page.get("results")
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise RuntimeCommandError("query response must include a results list of objects")
        has_more = page.get("has_more")
        if not isinstance(has_more, bool):
            raise RuntimeCommandError("query response must include a boolean has_more")
        status = page.get("request_status")
        if status is not None and (
            not isinstance(status, dict)
            or status.get("type") != "complete"
            or status.get("incomplete_reason")
        ):
            raise RuntimeCommandError("query results are incomplete; narrow the filter and retry")
        if combined is None:
            combined = dict(page)
        results.extend(entries)
        if not has_more:
            combined.update(object="list", results=results, has_more=False, next_cursor=None)
            return combined

        cursor = page.get("next_cursor")
        if not isinstance(cursor, str) or not cursor.strip() or cursor in seen:
            raise RuntimeCommandError("query returned a missing or repeated next_cursor")
        seen.add(cursor)
        command = replace(
            command,
            args=[
                *base_args,
                f"start_cursor:={json.dumps(cursor, ensure_ascii=False)}",
            ],
        )
