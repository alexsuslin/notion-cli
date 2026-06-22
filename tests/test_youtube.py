from __future__ import annotations

from notion_cli.youtube import normalize_youtube_url, parse_duration


def test_normalize_youtube_url_converts_short_url() -> None:
    assert (
        normalize_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_parse_duration_formats_seconds() -> None:
    assert parse_duration(3723) == "1:02:03"
