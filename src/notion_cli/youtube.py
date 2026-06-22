from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

from notion_cli.config import YoutubeConfig
from notion_cli.errors import EnvironmentError, RuntimeCommandError

YOUTUBE_API_KEY_ENV_VAR = "YOUTUBE_API_KEY"
_ISO_8601_DURATION = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


@dataclass(frozen=True)
class YoutubeMetadata:
    url: str
    title: str
    length: str
    author: str


def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        video_id = parsed.path.lstrip("/")
        return video_id or None
    if parsed.netloc.endswith("youtube.com"):
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        return video_id or None
    return None


def normalize_youtube_url(url: str) -> str:
    video_id = extract_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def parse_duration(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


def parse_iso8601_duration(value: str) -> str:
    match = _ISO_8601_DURATION.fullmatch(value)
    if match is None:
        raise RuntimeCommandError(f"unsupported YouTube duration format: {value}")
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return parse_duration((hours * 3600) + (minutes * 60) + seconds)


def _youtube_api_key(env: Mapping[str, str]) -> str | None:
    api_key = env.get(YOUTUBE_API_KEY_ENV_VAR)
    if api_key is None:
        return None
    stripped = api_key.strip()
    return stripped or None


def _fetch_with_yt_dlp(canonical: str, config: YoutubeConfig) -> YoutubeMetadata:
    try:
        from yt_dlp import YoutubeDL  # type: ignore[import-untyped]
    except ModuleNotFoundError as exc:
        raise EnvironmentError(
            "yt-dlp is required for the default YouTube provider; "
            "install dev dependencies or set youtube.provider='api_key'"
        ) from exc

    options = {
        "quiet": True,
        "skip_download": True,
        "socket_timeout": config.timeout_seconds,
    }
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(canonical, download=False)
        except Exception as exc:
            raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}") from exc

    return YoutubeMetadata(
        url=canonical,
        title=str(info["title"]),
        length=parse_duration(int(info["duration"])),
        author=str(info.get("channel") or info.get("uploader") or ""),
    )


def _fetch_with_api_key(
    canonical: str,
    config: YoutubeConfig,
    env: Mapping[str, str],
) -> YoutubeMetadata:
    api_key = _youtube_api_key(env)
    if api_key is None:
        raise EnvironmentError(
            "YOUTUBE_API_KEY is required when youtube.provider='api_key' or fallback is needed"
        )

    video_id = extract_video_id(canonical)
    if video_id is None:
        raise RuntimeCommandError(f"could not determine a YouTube video id from {canonical}")

    query = urlencode(
        {
            "part": "snippet,contentDetails",
            "id": video_id,
            "key": api_key,
        }
    )
    request_url = f"https://www.googleapis.com/youtube/v3/videos?{query}"

    try:
        with urlopen(request_url, timeout=config.timeout_seconds) as response:
            payload = json.load(response)
    except Exception as exc:
        raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}") from exc

    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}")

    first_item = items[0]
    if not isinstance(first_item, dict):
        raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}")

    snippet = first_item.get("snippet")
    content_details = first_item.get("contentDetails")
    if not isinstance(snippet, dict) or not isinstance(content_details, dict):
        raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}")

    title = snippet.get("title")
    duration = content_details.get("duration")
    if not isinstance(title, str) or not isinstance(duration, str):
        raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}")

    author = snippet.get("channelTitle")
    return YoutubeMetadata(
        url=canonical,
        title=title,
        length=parse_iso8601_duration(duration),
        author=author if isinstance(author, str) else "",
    )


def fetch_youtube_metadata(
    url: str,
    config: YoutubeConfig | None = None,
    env: Mapping[str, str] | None = None,
) -> YoutubeMetadata:
    active_config = config or YoutubeConfig()
    active_env = env or os.environ
    canonical = normalize_youtube_url(url)

    if active_config.provider == "api_key":
        return _fetch_with_api_key(canonical, active_config, active_env)

    try:
        return _fetch_with_yt_dlp(canonical, active_config)
    except (EnvironmentError, RuntimeCommandError):
        if _youtube_api_key(active_env) is None:
            raise
        return _fetch_with_api_key(canonical, active_config, active_env)
