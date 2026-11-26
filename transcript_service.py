"""Retrieve, normalize and chunk caption segments without discarding timestamps."""
from __future__ import annotations

import html
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, RequestBlocked, IpBlocked


class TranscriptError(Exception):
    """A safe, user-facing caption retrieval error."""


def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def get_transcript(video_id: str) -> dict:
    """Prefer English manual/automatic captions; otherwise use the first available track."""
    try:
        api = YouTubeTranscriptApi()
        tracks = api.list(video_id)
        try:
            track = tracks.find_transcript(["en"])
        except NoTranscriptFound:
            track = next(iter(tracks), None)
        if track is None:
            raise TranscriptError("No caption tracks are available for this video. A full content analysis requires a transcript.")
        fetched = track.fetch()
        segments = []
        for snippet in fetched:
            text = re.sub(r"\s+", " ", html.unescape(snippet.text)).strip()
            if text:
                segments.append({"start": max(0.0, float(snippet.start)), "duration": max(0.0, float(snippet.duration)), "text": text})
        if not segments:
            raise TranscriptError("The available transcript is empty. A full content analysis requires a transcript.")
        return {"segments": segments, "language": track.language, "language_code": track.language_code, "is_generated": track.is_generated}
    except TranscriptError:
        raise
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exc:
        raise TranscriptError("Captions are unavailable for this video, so its content cannot be fully analyzed.") from exc
    except (RequestBlocked, IpBlocked) as exc:
        raise TranscriptError("YouTube blocked transcript access from this server. Try again later or run the app from a different network.") from exc
    except Exception as exc:
        raise TranscriptError("Could not retrieve the transcript. Captions may be unavailable or YouTube may be blocking access from this server.") from exc


def transcript_lines(segments: list[dict]) -> list[str]:
    return [f"[{format_timestamp(s['start'])}] {s['text']}" for s in segments]


def chunk_transcript(segments: list[dict], max_chars: int = 22000) -> list[str]:
    """Split on segment boundaries, splitting unusually large segments if necessary."""
    if max_chars < 32:
        raise ValueError("max_chars must be at least 32")
    lines = []
    for segment in segments:
        prefix = f"[{format_timestamp(segment['start'])}] "
        text = segment["text"]
        # A single long caption can otherwise exceed the request budget.
        while len(text) > max_chars - len(prefix):
            limit = max_chars - len(prefix)
            split = text.rfind(" ", 0, limit + 1)
            if split < limit // 2:
                split = limit
            lines.append(prefix + text[:split])
            text = text[split:].lstrip()
        if text:
            lines.append(prefix + text)
    chunks, current, length = [], [], 0
    for line in lines:
        if current and length + len(line) + 1 > max_chars:
            chunks.append("\n".join(current))
            current, length = [], 0
        current.append(line)
        length += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks
