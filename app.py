"""Streamlit interface for transcript-grounded, single-video analysis."""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from youtube_service import YouTubeError, extract_video_id, fetch_video_metadata, format_duration
from transcript_service import TranscriptError, format_timestamp, get_transcript
from llm_service import AnalysisError, DEFAULT_MODEL, analyze_video

load_dotenv()
st.set_page_config(page_title="Video Analyzer", page_icon="▶", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"] {background:#0d0f12;color:#e9ebef;}
[data-testid="stHeader"] {background:#0d0f12;}
.block-container {max-width:1100px;padding-top:2.4rem;padding-bottom:5rem;}
h1,h2,h3 {font-family:'Manrope',sans-serif;letter-spacing:-.035em;}
h1 {font-size:3.3rem!important;font-weight:800!important;line-height:1.1!important;margin:0!important;}
h2 {font-size:1.35rem!important;font-weight:700!important;}
h3 {font-size:1rem!important;}
p,li {line-height:1.7;}
a {color:#d5f782!important;}
.brand {font-family:'Manrope',sans-serif;font-size:.82rem;font-weight:800;letter-spacing:.01em;color:#f3f4f1;display:flex;align-items:center;gap:10px;}
.brand-icon {display:inline-grid;place-items:center;width:28px;height:28px;border-radius:8px;background:#d4f781;color:#141b0c;font-size:12px;}
.topline {display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #292d31;padding-bottom:22px;margin-bottom:62px;}
.topnote {color:#89918e;font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700;}
.eyebrow {color:#d4f781;text-transform:uppercase;letter-spacing:.14em;font-size:.69rem;font-weight:700;margin-bottom:17px;}
.subtitle {font-size:1.08rem;color:#9da5a3;max-width:610px;line-height:1.65;margin:16px 0 29px;}
.section-rule {border:0;border-top:1px solid #292d31;margin:35px 0 27px;}
.section-label {font-size:.68rem;text-transform:uppercase;letter-spacing:.14em;color:#8c9691;font-weight:700;margin-bottom:10px;}
.muted {font-size:.83rem;color:#8c9691;line-height:1.6;}
.video-title {font-family:'Manrope',sans-serif;font-size:1.4rem;font-weight:700;line-height:1.35;margin:5px 0 10px;}
.meta-line {font-size:.88rem;color:#aab2af;margin-bottom:12px;}
.pill {display:inline-block;border:1px solid #343b35;border-radius:20px;color:#c3d3b5;padding:4px 10px;font-size:.72rem;margin:4px 6px 0 0;}
.empty {border-top:1px solid #292d31;margin-top:55px;padding-top:30px;}
.empty-number {color:#d4f781;font-size:.72rem;font-weight:700;letter-spacing:.1em;}
.empty-title {font-family:'Manrope',sans-serif;font-weight:700;font-size:.95rem;margin:9px 0 5px;}
div[data-testid="stTextInput"] input {background:#171b1d;border:1px solid #393f3e;border-radius:8px;color:#f0f3ef;padding:.8rem 1rem;}
div.stButton > button, div.stFormSubmitButton > button {background:#d4f781;color:#10170a;border:0;border-radius:8px;font-weight:700;min-height:48px;width:100%;}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {background:#e4ff9e;color:#10170a;border:0;}
div[data-testid="stForm"] {border:0;padding:0;}
div[data-testid="stImage"] img {border-radius:8px;}
div[data-testid="stExpander"] {border:1px solid #303633;border-radius:8px;}
[data-testid="stDataFrame"] {border-radius:8px;}
</style>
""", unsafe_allow_html=True)


def setting(name: str, default: str = "") -> str:
    """Prefer deployment secrets, falling back to environment / local .env."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name) or default).strip()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_metadata(video_id: str, key: str) -> dict:
    return fetch_video_metadata(video_id, key)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_transcript(video_id: str) -> dict:
    return get_transcript(video_id)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_analysis(metadata: dict, transcript: dict, key: str, model: str) -> dict:
    return analyze_video(metadata, transcript, key, model)


def published_date(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except (ValueError, AttributeError):
        return "Unknown date"


def timestamp_seconds(value: str) -> int:
    parts = [int(p) for p in value.split(":")]
    return sum(n * 60 ** i for i, n in enumerate(reversed(parts)))


def render_metadata(meta: dict):
    st.markdown('<div class="section-label">The video</div>', unsafe_allow_html=True)
    left, right = st.columns([1.12, 1.5], gap="large")
    with left:
        if meta["thumbnail"]:
            st.image(meta["thumbnail"], use_container_width=True)
        else:
            st.caption("Thumbnail unavailable")
    with right:
        st.subheader(meta["title"])
        st.write(meta["channel"])
        st.caption(f"{published_date(meta['published_at'])}  ·  {format_duration(meta['duration'])}")
        st.link_button("Watch on YouTube ↗", meta["url"])
    with st.expander("Video description"):
        st.text(meta["description"] or "No description available.")


def render_list(items: list[str], empty: str = "Not mentioned in the transcript."):
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption(empty)


def render_results(meta: dict, transcript: dict, analysis: dict):
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    render_metadata(meta)
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">The breakdown</div>', unsafe_allow_html=True)
    st.header("Summary")
    st.write(analysis["summary"])
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        st.header("Key takeaways")
        render_list(analysis["key_takeaways"])
    with right:
        st.header("Topics & concepts")
        render_list(analysis["topics"])
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        st.header("Important moments")
        if analysis["timestamps"]:
            for item in analysis["timestamps"]:
                seconds = timestamp_seconds(item["time"])
                st.markdown(f"[{item['time']}]({meta['url']}&t={seconds}s) — {item['explanation']}")
        else:
            st.caption("No reliable timestamps were identified.")
    with right:
        st.header("Action items")
        render_list(analysis["action_items"])
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        st.header("Who should watch")
        st.write(analysis["audience"])
        st.header("In conclusion")
        st.write(analysis["conclusion"])
    with right:
        st.header("Terms, explained")
        if analysis["terminology"]:
            for term in analysis["terminology"]:
                st.markdown(f"**{term['term']}** — {term['explanation']}")
        else:
            st.caption("No specific terminology was identified.")
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    st.header("Transcript")
    caption_type = "auto-generated" if transcript["is_generated"] else "provided"
    st.caption(f"{transcript['language']} · {caption_type} captions · AI analysis may contain mistakes; check the transcript for context.")
    with st.expander("View full transcript", expanded=False):
        df = pd.DataFrame([{"Time": format_timestamp(s["start"]), "Transcript": s["text"]} for s in transcript["segments"]])
        st.dataframe(df, hide_index=True, use_container_width=True)


st.markdown('<div class="topline"><div class="brand"><span class="brand-icon">▶</span> VIDEO ANALYZER</div><div class="topnote">A little more insight, a lot less watching</div></div>', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">Understand more, faster</div>', unsafe_allow_html=True)
st.title("Get to the good part.")
st.markdown('<p class="subtitle">Turn a YouTube video into clear ideas, key moments, and practical takeaways. All grounded in what was actually said.</p>', unsafe_allow_html=True)

with st.form("analyze_form"):
    st.markdown('<div class="section-label">YouTube video URL</div>', unsafe_allow_html=True)
    input_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
    with input_col:
        url = st.text_input("YouTube video URL", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
    with button_col:
        submitted = st.form_submit_button("Analyze video  ↗", use_container_width=True)
st.caption("Works with public videos that have available captions.")

if submitted:
    st.session_state.pop("result", None)
    st.session_state.pop("metadata", None)
    st.session_state.pop("error", None)
    try:
        video_id = extract_video_id(url)
        yt_key = setting("YT_KEY")
        gemini_key = setting("GEMINI_API_KEY")
        if not yt_key or not gemini_key:
            raise ValueError("Add YT_KEY and GEMINI_API_KEY to your .env file or Streamlit secrets before analyzing. See the README for setup.")
        with st.spinner("Fetching video details and captions, then preparing your analysis. Longer videos may take a few minutes…"):
            metadata = cached_metadata(video_id, yt_key)
            st.session_state["metadata"] = metadata
            transcript = cached_transcript(video_id)
            analysis = cached_analysis(metadata, transcript, gemini_key, setting("GEMINI_MODEL", DEFAULT_MODEL))
            st.session_state["result"] = (metadata, transcript, analysis)
    except (ValueError, YouTubeError, TranscriptError, AnalysisError) as exc:
        st.session_state["error"] = str(exc)

if "error" in st.session_state:
    st.error(st.session_state["error"])
    if "metadata" in st.session_state:
        st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
        render_metadata(st.session_state["metadata"])
elif "result" in st.session_state:
    render_results(*st.session_state["result"])
else:
    st.markdown('''<div class="empty"><div class="section-label">How it works</div></div>''', unsafe_allow_html=True)
    columns = st.columns(3, gap="large")
    for col, number, title, detail in zip(columns, ("01", "02", "03"), ("Paste a link", "We read the transcript", "Get the essentials"), ("Choose a single YouTube video you want to understand.", "Available captions are prepared and analyzed with AI.", "Explore the main ideas, key moments, and next steps.")):
        with col:
            st.markdown(f'<div class="empty-number">{number} /</div><div class="empty-title">{title}</div><div class="muted">{detail}</div>', unsafe_allow_html=True)
