"""YouTube URL validation and video metadata lookup."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
SHORT_HOSTS = {"youtu.be", "www.youtu.be"}


class YouTubeError(Exception):
    """A safe, user-facing YouTube lookup error."""


def extract_video_id(url: str) -> str:
    """Parse only supported YouTube video URLs, rejecting lookalike hosts."""
    url = url.strip()
    if not url:
        raise ValueError("Enter a YouTube video URL.")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme.lower() not in {"http", "https"} or parsed.username or parsed.password or parsed.port not in (None, 80, 443):
            raise ValueError
        parts = [p for p in parsed.path.split("/") if p]
        if host in SHORT_HOSTS and len(parts) == 1:
            candidate = parts[0]
        elif host in YOUTUBE_HOSTS and parsed.path.rstrip("/") == "/watch":
            values = parse_qs(parsed.query).get("v", [])
            candidate = values[0] if len(values) == 1 else ""
        elif host in YOUTUBE_HOSTS and len(parts) == 2 and parts[0] in {"shorts", "embed"}:
            candidate = parts[1]
        else:
            candidate = ""
        if not VIDEO_ID.fullmatch(candidate):
            raise ValueError
        return candidate
    except ValueError as exc:
        raise ValueError("Enter a valid YouTube video URL with an 11-character video ID.") from exc


def fetch_video_metadata(video_id: str, api_key: str) -> dict:
    if not VIDEO_ID.fullmatch(video_id):
        raise YouTubeError("Invalid video ID.")
    try:
        youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
        response = youtube.videos().list(part="snippet,contentDetails", id=video_id).execute()
    except HttpError as exc:
        status = getattr(exc.resp, "status", None)
        if status in (400, 401, 403):
            raise YouTubeError("YouTube could not authorize the request. Check your YT_KEY, API access and quota.") from exc
        raise YouTubeError("YouTube could not retrieve this video. Please try again later.") from exc
    except Exception as exc:
        raise YouTubeError("Could not connect to YouTube. Check your connection and try again.") from exc
    items = response.get("items", [])
    if not items:
        raise YouTubeError("Video not found. It may be private, deleted, or unavailable.")
    item = items[0]
    snippet = item.get("snippet", {})
    thumbnails = snippet.get("thumbnails", {})
    thumbnail = next((thumbnails.get(size, {}).get("url") for size in ("maxres", "standard", "high", "medium", "default") if thumbnails.get(size, {}).get("url")), None)
    return {
        "id": video_id,
        "title": snippet.get("title") or "Untitled video",
        "channel": snippet.get("channelTitle") or "Unknown channel",
        "description": snippet.get("description") or "",
        "published_at": snippet.get("publishedAt") or "",
        "thumbnail": thumbnail,
        "duration": item.get("contentDetails", {}).get("duration") or "",
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


def format_duration(duration: str) -> str:
    """Format YouTube's ISO 8601 video duration, including day-long videos."""
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration or "")
    if not match or not any(match.groups()):
        return "Unknown"
    days, hours, minutes, seconds = (int(value or 0) for value in match.groups())
    hours += days * 24
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
