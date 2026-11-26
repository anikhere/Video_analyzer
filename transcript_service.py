"""Retrieve, normalize, compact, and chunk caption segments without discarding timestamps."""
from __future__ import annotations

import html
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig


class TranscriptError(Exception):
    """A safe, user-facing caption retrieval error."""


class TranscriptBlockedError(TranscriptError):
    """Raised specifically when YouTube blocks caption scraping from a cloud datacenter IP."""


def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def timestamp_to_seconds(value: str) -> int:
    """Convert MM:SS or H:MM:SS into integer seconds safely."""
    try:
        parts = [int(p) for p in value.strip().strip("[]").split(":")]
        if len(parts) not in (2, 3) or any(p < 0 for p in parts):
            return 0
        return sum(n * (60 ** i) for i, n in enumerate(reversed(parts)))
    except (ValueError, AttributeError):
        return 0


def _optional_proxy_config():
    ws_user = (os.getenv("WEBSHARE_PROXY_USERNAME") or "").strip()
    ws_pass = (os.getenv("WEBSHARE_PROXY_PASSWORD") or "").strip()
    if ws_user and ws_pass:
        return WebshareProxyConfig(proxy_username=ws_user, proxy_password=ws_pass)
    proxy_url = (os.getenv("TRANSCRIPT_PROXY_URL") or "").strip()
    if proxy_url:
        return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
    return None


def get_transcript(video_id: str) -> dict:
    """Prefer English manual/automatic captions; otherwise use the first available track."""
    try:
        proxy_cfg = _optional_proxy_config()
        api = YouTubeTranscriptApi(proxy_config=proxy_cfg) if proxy_cfg else YouTubeTranscriptApi()
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
        return {
            "segments": segments,
            "language": track.language,
            "language_code": track.language_code,
            "is_generated": track.is_generated,
        }
    except TranscriptError:
        raise
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exc:
        raise TranscriptError("Captions are unavailable for this video, so its content cannot be fully analyzed.") from exc
    except (RequestBlocked, IpBlocked) as exc:
        raise TranscriptBlockedError(
            "YouTube blocked transcript access from this cloud server IP. Switch LLM_PROVIDER to 'gemini' (bypasses cloud IP blocks automatically) or paste the transcript below."
        ) from exc
    except Exception as exc:
        msg = str(exc).lower()
        if "blocked" in msg or "429" in msg or "too many requests" in msg:
            raise TranscriptBlockedError(
                "YouTube blocked transcript access from this cloud server IP. Switch LLM_PROVIDER to 'gemini' (bypasses cloud IP blocks automatically) or paste the transcript below."
            ) from exc
        raise TranscriptError("Could not retrieve the transcript. Captions may be unavailable or YouTube may be blocking access from this server.") from exc


TS_LINE_RE = re.compile(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(.*)$")


def parse_pasted_transcript(raw_text: str) -> dict:
    """Parse user-pasted YouTube transcript (supports inline `[01:23] text`, 2-line YouTube format, or plain text)."""
    cleaned = (raw_text or "").strip()
    if len(cleaned) < 20:
        raise TranscriptError("Pasted transcript is too short to analyze.")

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    segments: list[dict] = []
    idx = 0
    while idx < len(lines):
        m = TS_LINE_RE.match(lines[idx])
        if m:
            ts_str, rest = m.group(1), m.group(2).strip()
            sec = float(timestamp_to_seconds(ts_str))
            if rest:
                segments.append({"start": sec, "duration": 4.0, "text": rest})
                idx += 1
            elif idx + 1 < len(lines) and not TS_LINE_RE.match(lines[idx + 1]):
                segments.append({"start": sec, "duration": 4.0, "text": lines[idx + 1]})
                idx += 2
            else:
                idx += 1
        else:
            idx += 1

    # Fallback if plain text without timestamps was pasted
    if not segments:
        words = re.sub(r"\s+", " ", cleaned).split(" ")
        chunk_words = 32
        for i in range(0, len(words), chunk_words):
            piece = " ".join(words[i : i + chunk_words]).strip()
            if piece:
                est_start = float((i / 145.0) * 60.0)
                segments.append({"start": round(est_start, 1), "duration": 12.0, "text": piece})

    # Recompute segment durations from consecutive starts
    for i in range(len(segments) - 1):
        gap = segments[i + 1]["start"] - segments[i]["start"]
        if 0.5 <= gap <= 60.0:
            segments[i]["duration"] = round(gap, 1)

    return {
        "segments": segments,
        "language": "Provided",
        "language_code": "en",
        "is_generated": False,
    }


def compact_segments(segments: list[dict], window_seconds: float = 14.0, max_block_chars: int = 380) -> list[dict]:
    """Merge micro-caption fragments into readable ~14s blocks while preserving exact start timestamps."""
    if not segments:
        return []
    compacted: list[dict] = []
    cur_start = float(segments[0]["start"])
    cur_end = cur_start + float(segments[0].get("duration", 0.0))
    cur_texts = [segments[0]["text"]]
    cur_len = len(segments[0]["text"])

    for seg in segments[1:]:
        s_start = float(seg["start"])
        s_dur = float(seg.get("duration", 0.0))
        s_text = seg["text"]
        if (s_start - cur_start) <= window_seconds and (cur_len + 1 + len(s_text)) <= max_block_chars:
            cur_texts.append(s_text)
            cur_len += 1 + len(s_text)
            cur_end = max(cur_end, s_start + s_dur)
        else:
            compacted.append({"start": cur_start, "duration": max(0.0, cur_end - cur_start), "text": " ".join(cur_texts)})
            cur_start = s_start
            cur_end = s_start + s_dur
            cur_texts = [s_text]
            cur_len = len(s_text)

    compacted.append({"start": cur_start, "duration": max(0.0, cur_end - cur_start), "text": " ".join(cur_texts)})
    return compacted


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
