from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from notion_cli.errors import EnvironmentError, RuntimeCommandError


@dataclass(frozen=True)
class YoutubeMetadata:
    url: str
    title: str
    length: str
    author: str


def normalize_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        video_id = parsed.path.lstrip("/")
        return f"https://www.youtube.com/watch?v={video_id}"
    if parsed.netloc.endswith("youtube.com"):
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    return url


def parse_duration(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


def fetch_youtube_metadata(url: str) -> YoutubeMetadata:
    try:
        from yt_dlp import YoutubeDL  # type: ignore[import-untyped]
    except ModuleNotFoundError as exc:
        raise EnvironmentError(
            "yt-dlp is required for YouTube metadata enrichment; install dev dependencies first"
        ) from exc

    canonical = normalize_youtube_url(url)
    options = {"quiet": True, "skip_download": True}

    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(canonical, download=False)
        except Exception as exc:
            raise RuntimeCommandError(f"failed to fetch YouTube metadata for {canonical}") from exc

    return YoutubeMetadata(
        url=canonical,
        title=info["title"],
        length=parse_duration(int(info["duration"])),
        author=str(info.get("channel") or info.get("uploader") or ""),
    )
