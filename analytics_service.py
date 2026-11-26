"""Deterministic, zero-API-call analytics and chart builders grounded in transcript & metadata."""
from __future__ import annotations

from collections import Counter
import re
from transcript_service import format_timestamp, timestamp_to_seconds
from youtube_service import duration_to_seconds, format_duration, seconds_to_iso_duration

STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "your", "have", "for", "are", "was", "were",
    "you", "they", "their", "them", "what", "when", "where", "which", "while", "will", "would",
    "could", "should", "about", "into", "over", "after", "before", "under", "again", "further",
    "then", "once", "here", "there", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "only", "own", "same", "than", "too", "very", "can", "just", "dont", "going",
    "like", "really", "actually", "because", "know", "think", "make", "made", "want", "need",
    "look", "using", "used", "also", "been", "being", "does", "did", "doing", "its", "it's",
    "we're", "you're", "that's", "there's", "don't", "can't", "won't", "isn't", "aren't", "let",
    "lets", "thing", "things", "something", "everything", "nothing", "right", "well", "okay",
    "yeah", "kind", "sort", "way", "ways", "much", "many", "even", "still", "back", "take",
    "come", "coming", "getting", "got", "give", "given", "talk", "talking", "video", "today",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def _format_span(seconds: int) -> str:
    seconds = max(1, int(round(seconds)))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes and secs:
        return f"{minutes}m {secs}s"
    if minutes:
        return f"{minutes}m"
    return f"{secs}s"


def _infer_duration_seconds(metadata: dict, segments: list[dict]) -> int:
    meta_sec = int(metadata.get("duration_seconds") or 0)
    if not meta_sec and metadata.get("duration"):
        meta_sec = duration_to_seconds(metadata["duration"])
    seg_end = 0
    if segments:
        seg_end = int(round(max(float(s["start"]) + max(1.0, float(s.get("duration", 2.0))) for s in segments)))
    return max(meta_sec, seg_end, 1)


def _choose_bucket_size(total_seconds: int) -> int:
    """Pick clean time bucket width yielding roughly 12-22 points on the chart."""
    if total_seconds <= 120:
        return max(5, total_seconds // 12 or 5)
    for candidate in (15, 20, 30, 45, 60, 90, 120, 180, 240, 300, 600):
        count = total_seconds / candidate
        if 11 <= count <= 22:
            return candidate
    return max(10, int(round(total_seconds / 16)))


def _build_concept_patterns(analysis: dict, segments: list[dict]) -> list[tuple[str, re.Pattern]]:
    candidates: list[str] = []
    seen_lower: set[str] = set()

    for term_obj in analysis.get("terminology", []):
        label = (term_obj.get("term") or "").strip()
        clean = re.sub(r"\s*\(.*?\)\s*", "", label).strip()
        if 2 <= len(clean) <= 36 and clean.lower() not in seen_lower:
            seen_lower.add(clean.lower())
            candidates.append(clean)

    for topic in analysis.get("topics", []):
        clean = re.sub(r"\s*\(.*?\)\s*", "", (topic or "").strip()).strip()
        if 2 <= len(clean) <= 36 and clean.lower() not in seen_lower:
            seen_lower.add(clean.lower())
            candidates.append(clean)

    # Supplement with salient transcript keywords so frequency chart always has grounded signals
    word_counts: Counter[str] = Counter()
    for seg in segments:
        for tok in _tokenize(seg["text"]):
            clean_tok = tok.strip("'")
            if len(clean_tok) >= 4 and clean_tok not in STOPWORDS and not clean_tok.isdigit():
                word_counts[clean_tok] += 1

    for word, _ in word_counts.most_common(16):
        if word not in seen_lower:
            seen_lower.add(word)
            candidates.append(word.title())

    patterns: list[tuple[str, re.Pattern]] = []
    for label in candidates:
        escaped = re.escape(label.lower())
        # Also match key root if multi-word topic didn't appear verbatim
        pat = re.compile(rf"\b{escaped}s?\b", re.IGNORECASE)
        patterns.append((label, pat))
    return patterns


def build_dashboard_analytics(metadata: dict, transcript: dict, analysis: dict) -> dict:
    """Compute all dashboard KPIs, timeline tracks, and chart datasets deterministically."""
    segments = transcript.get("segments", [])
    total_seconds = _infer_duration_seconds(metadata, segments)

    # Ensure metadata duration is populated even in zero-YT-key oEmbed mode
    if not metadata.get("duration"):
        metadata["duration"] = seconds_to_iso_duration(total_seconds)
    metadata["duration_seconds"] = total_seconds

    total_words = 0
    all_content_words: list[str] = []
    seg_records = []
    for seg in segments:
        tokens = _tokenize(seg["text"])
        wc = len(tokens)
        total_words += wc
        c_words = [w.strip("'") for w in tokens if len(w.strip("'")) >= 4 and w.strip("'") not in STOPWORDS]
        all_content_words.extend(c_words)
        seg_records.append(
            {
                "start": float(seg["start"]),
                "end": float(seg["start"]) + max(1.0, float(seg.get("duration", 2.0))),
                "text": seg["text"],
                "words": wc,
                "content_words": c_words,
            }
        )

    duration_minutes = max(total_seconds / 60.0, 0.1)
    avg_wpm = int(round(total_words / duration_minutes)) if total_words else 0
    if avg_wpm >= 165:
        pace_category = "Fast-Paced"
    elif avg_wpm >= 120:
        pace_category = "Conversational"
    else:
        pace_category = "Measured"

    brief_text = " ".join(
        [
            analysis.get("tldr", ""),
            analysis.get("summary", ""),
            analysis.get("premise", ""),
            analysis.get("core_breakdown", ""),
            analysis.get("conclusion", ""),
            " ".join(analysis.get("key_takeaways", [])),
            " ".join(analysis.get("action_items", [])),
        ]
    )
    brief_words = max(120, len(_tokenize(brief_text)))
    brief_read_minutes = round(max(1.0, brief_words / 220.0), 1)
    transcript_read_minutes = round(max(0.5, total_words / 230.0), 1)
    video_minutes = round(total_seconds / 60.0, 1)
    time_saved_minutes = round(max(0.0, video_minutes - brief_read_minutes), 1)
    time_saved_pct = int(round((time_saved_minutes / video_minutes) * 100)) if video_minutes > 0 else 0

    lexical_richness_pct = (
        int(round((len(set(all_content_words)) / len(all_content_words)) * 100))
        if all_content_words
        else 0
    )

    views = metadata.get("view_count")
    likes = metadata.get("like_count")
    comments = metadata.get("comment_count")
    engagement_rate = None
    if views and views > 0 and (likes is not None or comments is not None):
        engagement_rate = round((((likes or 0) + (comments or 0)) / views) * 100, 2)

    concept_patterns = _build_concept_patterns(analysis, segments)

    # 1. Pace & Information Density Time-Series
    bucket_size = _choose_bucket_size(total_seconds)
    pace_series = []
    raw_densities = []
    num_buckets = max(1, (total_seconds + bucket_size - 1) // bucket_size)

    for b_idx in range(num_buckets):
        b_start = b_idx * bucket_size
        b_end = min(total_seconds, (b_idx + 1) * bucket_size)
        span_sec = max(5, b_end - b_start)
        in_bucket = [r for r in seg_records if b_start <= r["start"] < b_end]
        if not in_bucket and b_idx == num_buckets - 1:
            in_bucket = [r for r in seg_records if r["start"] >= b_start]

        b_words = sum(r["words"] for r in in_bucket)
        b_wpm = int(round((b_words / span_sec) * 60))
        b_text = " ".join(r["text"] for r in in_bucket)
        b_cwords = [cw for r in in_bucket for cw in r["content_words"]]
        unique_cwords = len(set(b_cwords))

        hits = sum(len(pat.findall(b_text)) for _, pat in concept_patterns[:12]) if b_text else 0
        raw_density = (b_wpm * 0.45) + (unique_cwords * 2.2) + (hits * 9.0)
        raw_densities.append(raw_density)

        excerpt = b_text[:110].strip()
        if len(b_text) > 110:
            excerpt = excerpt.rsplit(" ", 1)[0] + "…"

        pace_series.append(
            {
                "index": b_idx,
                "time": format_timestamp(b_start),
                "end_time": format_timestamp(b_end),
                "start_seconds": b_start,
                "end_seconds": b_end,
                "wpm": b_wpm,
                "concept_hits": hits,
                "density": 0,  # normalized below
                "excerpt": excerpt or "Instrumental / pause segment",
            }
        )

    max_raw = max(raw_densities, default=1.0) or 1.0
    for item, rd in zip(pace_series, raw_densities):
        item["density"] = min(100, max(8 if item["wpm"] > 0 else 0, int(round((rd / max_raw) * 96))))

    # 2. Grounded Chapter Allocation & Segmented Timeline
    raw_chapters = list(analysis.get("chapters") or [])
    normalized_chapters = []
    for ch in raw_chapters:
        sec = timestamp_to_seconds(ch["start_time"])
        if 0 <= sec < total_seconds:
            normalized_chapters.append(
                {
                    "start_seconds": sec,
                    "start_time": format_timestamp(sec),
                    "title": ch["title"],
                    "summary": ch.get("summary", ""),
                }
            )
    normalized_chapters.sort(key=lambda c: c["start_seconds"])

    # Fallback if fewer than 2 chapters exist so timeline & allocation chart are always rich
    if len(normalized_chapters) < 2:
        ts_items = analysis.get("timestamps", [])
        if len(ts_items) >= 2:
            normalized_chapters = [
                {
                    "start_seconds": timestamp_to_seconds(t["time"]),
                    "start_time": t["time"],
                    "title": t["explanation"][:42] + ("…" if len(t["explanation"]) > 42 else ""),
                    "summary": t["explanation"],
                }
                for t in ts_items[:6]
            ]
        elif seg_records:
            step = max(1, len(seg_records) // 3)
            labels = ["Opening & Context", "Core Walkthrough", "Synthesis & Wrap-Up"]
            normalized_chapters = []
            for idx, lbl in enumerate(labels):
                s_idx = min(len(seg_records) - 1, idx * step)
                sec = int(seg_records[s_idx]["start"])
                if not normalized_chapters or sec > normalized_chapters[-1]["start_seconds"]:
                    normalized_chapters.append(
                        {
                            "start_seconds": sec,
                            "start_time": format_timestamp(sec),
                            "title": lbl,
                            "summary": seg_records[s_idx]["text"][:100],
                        }
                    )

    if normalized_chapters and normalized_chapters[0]["start_seconds"] > max(20, int(total_seconds * 0.06)):
        first_seg_sec = int(seg_records[0]["start"]) if seg_records else 0
        normalized_chapters.insert(
            0,
            {
                "start_seconds": first_seg_sec,
                "start_time": format_timestamp(first_seg_sec),
                "title": "Introduction & Framing",
                "summary": "Opening context and setup before the main breakdown.",
            },
        )

    chapters_out = []
    for idx, ch in enumerate(normalized_chapters):
        start_s = ch["start_seconds"]
        end_s = normalized_chapters[idx + 1]["start_seconds"] if idx + 1 < len(normalized_chapters) else total_seconds
        dur_s = max(1, end_s - start_s)
        ch_segs = [r for r in seg_records if start_s <= r["start"] < end_s]
        ch_words = sum(r["words"] for r in ch_segs)
        ch_wpm = int(round((ch_words / dur_s) * 60)) if dur_s > 0 else 0
        chapters_out.append(
            {
                "index": idx + 1,
                "title": ch["title"],
                "summary": ch["summary"],
                "start_time": ch["start_time"],
                "end_time": format_timestamp(end_s),
                "start_seconds": start_s,
                "end_seconds": end_s,
                "duration_seconds": dur_s,
                "duration_minutes": round(dur_s / 60.0, 2),
                "duration_label": _format_span(dur_s),
                "share_pct": round((dur_s / total_seconds) * 100, 1),
                "word_count": ch_words,
                "wpm": ch_wpm,
            }
        )

    # 3. Concept & Terminology Mention Frequency
    concept_freq = []
    seen_labels = set()
    for label, pat in concept_patterns:
        total_mentions = 0
        first_sec = None
        hit_positions: list[float] = []
        for r in seg_records:
            matches = len(pat.findall(r["text"]))
            if matches:
                total_mentions += matches
                if first_sec is None:
                    first_sec = int(r["start"])
                hit_positions.append(r["start"] / total_seconds)
        if total_mentions > 0 and label.lower() not in seen_labels:
            seen_labels.add(label.lower())
            if len(hit_positions) >= 3 and (max(hit_positions) - min(hit_positions)) >= 0.45:
                spread = "Throughout"
            else:
                avg_pos = sum(hit_positions) / len(hit_positions)
                spread = "Early" if avg_pos < 0.34 else ("Mid" if avg_pos < 0.68 else "Late")
            concept_freq.append(
                {
                    "concept": label[:28] + ("…" if len(label) > 28 else ""),
                    "full_concept": label,
                    "mentions": total_mentions,
                    "first_time": format_timestamp(first_sec or 0),
                    "first_seconds": first_sec or 0,
                    "spread": spread,
                }
            )

    concept_freq.sort(key=lambda x: (-x["mentions"], x["first_seconds"]))
    concept_freq = concept_freq[:8]

    # 4. Enriched Important Moment Pins
    moment_pins = []
    for idx, ts in enumerate(analysis.get("timestamps", []), 1):
        sec = timestamp_to_seconds(ts["time"])
        pos_pct = round(min(99.5, max(0.5, (sec / total_seconds) * 100)), 1)
        chap_match = next(
            (c["title"] for c in chapters_out if c["start_seconds"] <= sec < c["end_seconds"]),
            chapters_out[-1]["title"] if chapters_out else "Video",
        )
        moment_pins.append(
            {
                "index": idx,
                "time": ts["time"],
                "seconds": sec,
                "position_pct": pos_pct,
                "explanation": ts["explanation"],
                "chapter": chap_match,
            }
        )

    return {
        "kpis": {
            "duration_seconds": total_seconds,
            "duration_label": format_duration(metadata["duration"]),
            "word_count": total_words,
            "segment_count": len(segments),
            "avg_wpm": avg_wpm,
            "pace_category": pace_category,
            "brief_read_minutes": brief_read_minutes,
            "transcript_read_minutes": transcript_read_minutes,
            "time_saved_minutes": time_saved_minutes,
            "time_saved_pct": time_saved_pct,
            "lexical_richness_pct": lexical_richness_pct,
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
            "engagement_rate": engagement_rate,
        },
        "pace_series": pace_series,
        "chapters": chapters_out,
        "concept_frequency": concept_freq,
        "moment_pins": moment_pins,
    }
