"""YouTube URL validation and video metadata lookup (with zero-key oEmbed fallback)."""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

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
    """Standard metadata lookup via YouTube Data API v3."""
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
    thumbnail = next(
        (thumbnails.get(size, {}).get("url") for size in ("maxres", "standard", "high", "medium", "default") if thumbnails.get(size, {}).get("url")),
        None,
    )
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


def fetch_video_metadata_oembed(video_id: str) -> dict:
    """Zero-API-key metadata lookup using YouTube's public oEmbed endpoint."""
    if not VIDEO_ID.fullmatch(video_id):
        raise YouTubeError("Invalid video ID.")
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    oembed_url = f"https://www.youtube.com/oembed?url={quote(watch_url, safe='')}&format=json"
    req = Request(oembed_url, headers={"User-Agent": "VideoAnalyzer/2.0"})
    try:
        with urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise YouTubeError("Video not found or embedding is disabled. It may be private or unavailable.") from exc
        raise YouTubeError("YouTube could not retrieve this video via oEmbed. Try again or configure YT_KEY.") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise YouTubeError("Could not connect to YouTube to retrieve video details.") from exc

    return {
        "id": video_id,
        "title": payload.get("title") or "Untitled video",
        "channel": payload.get("author_name") or "Unknown channel",
        "description": "",
        "published_at": "",
        "thumbnail": payload.get("thumbnail_url") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "duration": "",
        "duration_seconds": 0,
        "view_count": None,
        "like_count": None,
        "comment_count": None,
        "metadata_source": "oembed",
        "url": watch_url,
    }


def fetch_video_metadata_smart(video_id: str, api_key: str = "") -> tuple[dict, int]:
    """Fetch enriched metadata in 1 API call if YT_KEY is set, or 0 API calls via oEmbed."""
    if not VIDEO_ID.fullmatch(video_id):
        raise YouTubeError("Invalid video ID.")
    clean_key = (api_key or "").strip()
    if not clean_key:
        return fetch_video_metadata_oembed(video_id), 0

    try:
        youtube = build("youtube", "v3", developerKey=clean_key, cache_discovery=False)
        response = youtube.videos().list(part="snippet,contentDetails,statistics", id=video_id).execute()
    except HttpError as exc:
        status = getattr(exc.resp, "status", None)
        if status in (400, 401, 403):
            raise YouTubeError("YouTube could not authorize the request. Check your YT_KEY, or leave YT_KEY blank to use zero-key mode.") from exc
        raise YouTubeError("YouTube could not retrieve this video. Please try again later.") from exc
    except Exception as exc:
        raise YouTubeError("Could not connect to YouTube. Check your connection and try again.") from exc

    items = response.get("items", [])
    if not items:
        raise YouTubeError("Video not found. It may be private, deleted, or unavailable.")
    item = items[0]
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    thumbnails = snippet.get("thumbnails", {})
    thumbnail = next(
        (thumbnails.get(size, {}).get("url") for size in ("maxres", "standard", "high", "medium", "default") if thumbnails.get(size, {}).get("url")),
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    )
    iso_duration = item.get("contentDetails", {}).get("duration") or ""

    def _safe_int(val) -> int | None:
        try:
            return int(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "id": video_id,
        "title": snippet.get("title") or "Untitled video",
        "channel": snippet.get("channelTitle") or "Unknown channel",
        "description": snippet.get("description") or "",
        "published_at": snippet.get("publishedAt") or "",
        "thumbnail": thumbnail,
        "duration": iso_duration,
        "duration_seconds": duration_to_seconds(iso_duration),
        "view_count": _safe_int(stats.get("viewCount")),
        "like_count": _safe_int(stats.get("likeCount")),
        "comment_count": _safe_int(stats.get("commentCount")),
        "metadata_source": "youtube_api",
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }, 1


def duration_to_seconds(duration: str) -> int:
    """Parse YouTube's ISO 8601 video duration into integer seconds."""
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration or "")
    if not match or not any(match.groups()):
        return 0
    days, hours, minutes, seconds = (int(value or 0) for value in match.groups())
    return (((days * 24) + hours) * 60 + minutes) * 60 + seconds


def seconds_to_iso_duration(total_seconds: float) -> str:
    """Convert raw seconds into ISO 8601 duration (e.g., PT12M34S)."""
    secs = max(0, int(round(total_seconds)))
    if secs == 0:
        return ""
    hours, rem = divmod(secs, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = ["PT"]
    if hours:
        parts.append(f"{hours}H")
    if minutes:
        parts.append(f"{minutes}M")
    if seconds or (not hours and not minutes):
        parts.append(f"{seconds}S")
    return "".join(parts)


def format_duration(duration: str) -> str:
    """Format YouTube's ISO 8601 video duration, including day-long videos."""
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration or "")
    if not match or not any(match.groups()):
        return "Unknown"
    days, hours, minutes, seconds = (int(value or 0) for value in match.groups())
    hours += days * 24
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
