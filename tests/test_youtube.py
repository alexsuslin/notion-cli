from __future__ import annotations

from notion_cli.config import YoutubeConfig
from notion_cli.errors import RuntimeCommandError
from notion_cli.youtube import (
    YoutubeMetadata,
    fetch_youtube_metadata,
    normalize_youtube_url,
    parse_duration,
    parse_iso8601_duration,
)


def test_normalize_youtube_url_converts_short_url() -> None:
    assert (
        normalize_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_parse_duration_formats_seconds() -> None:
    assert parse_duration(3723) == "1:02:03"


def test_parse_iso8601_duration_formats_api_value() -> None:
    assert parse_iso8601_duration("PT1H2M3S") == "1:02:03"


def test_youtube_metadata_supports_author_field() -> None:
    metadata = YoutubeMetadata(
        url="https://www.youtube.com/watch?v=abc",
        title="Video Title",
        length="3:21",
        author="Channel Name",
    )
    assert metadata.author == "Channel Name"


def test_fetch_youtube_metadata_falls_back_to_api_key(monkeypatch) -> None:
    import notion_cli.youtube as youtube

    def fail_ytdlp(canonical: str, config: YoutubeConfig) -> YoutubeMetadata:
        raise RuntimeCommandError(
            f"yt-dlp blocked for {canonical} with provider={config.provider}"
        )

    def fake_api_key(
        canonical: str,
        config: YoutubeConfig,
        env: dict[str, str],
    ) -> YoutubeMetadata:
        assert canonical == "https://www.youtube.com/watch?v=abc"
        assert config.provider == "no_key"
        assert env["YOUTUBE_API_KEY"] == "test-key"
        return YoutubeMetadata(
            url=canonical,
            title="API Title",
            length="3:21",
            author="API Channel",
        )

    monkeypatch.setattr(youtube, "_fetch_with_yt_dlp", fail_ytdlp)
    monkeypatch.setattr(youtube, "_fetch_with_api_key", fake_api_key)

    metadata = fetch_youtube_metadata(
        "https://youtu.be/abc",
        YoutubeConfig(provider="no_key", timeout_seconds=10),
        {"YOUTUBE_API_KEY": "test-key"},
    )

    assert metadata.title == "API Title"
    assert metadata.author == "API Channel"


def test_fetch_youtube_metadata_honors_api_key_provider(monkeypatch) -> None:
    import notion_cli.youtube as youtube

    called = {"yt_dlp": False}

    def fail_if_called(canonical: str, config: YoutubeConfig) -> YoutubeMetadata:
        called["yt_dlp"] = True
        raise AssertionError(f"yt-dlp should not be used for {canonical} with {config.provider}")

    def fake_api_key(
        canonical: str,
        config: YoutubeConfig,
        env: dict[str, str],
    ) -> YoutubeMetadata:
        assert env["YOUTUBE_API_KEY"] == "test-key"
        return YoutubeMetadata(
            url=canonical,
            title="API Title",
            length="3:21",
            author="API Channel",
        )

    monkeypatch.setattr(youtube, "_fetch_with_yt_dlp", fail_if_called)
    monkeypatch.setattr(youtube, "_fetch_with_api_key", fake_api_key)

    metadata = fetch_youtube_metadata(
        "https://youtu.be/abc",
        YoutubeConfig(provider="api_key", timeout_seconds=10),
        {"YOUTUBE_API_KEY": "test-key"},
    )

    assert metadata.title == "API Title"
    assert called["yt_dlp"] is False
