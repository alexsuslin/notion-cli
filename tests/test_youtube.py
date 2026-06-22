from __future__ import annotations

from notion_cli.youtube import YoutubeMetadata, normalize_youtube_url, parse_duration


def test_normalize_youtube_url_converts_short_url() -> None:
    assert (
        normalize_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_parse_duration_formats_seconds() -> None:
    assert parse_duration(3723) == "1:02:03"


def test_youtube_metadata_supports_author_field() -> None:
    metadata = YoutubeMetadata(
        url="https://www.youtube.com/watch?v=abc",
        title="Video Title",
        length="3:21",
        author="Channel Name",
    )
    assert metadata.author == "Channel Name"
