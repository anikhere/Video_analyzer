"""FastAPI backend for the Single-Video Intelligence Dashboard (low-API, parallel, cached)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from analytics_service import build_dashboard_analytics
from llm_service import (
    AnalysisError,
    DEFAULT_MODEL,
    GEMINI_DEFAULT_MODEL,
    analyze_video_dashboard,
    analyze_youtube_url_via_gemini,
)
from sample_data import SAMPLES
from transcript_service import (
    TranscriptBlockedError,
    TranscriptError,
    format_timestamp,
    get_transcript,
    parse_pasted_transcript,
)
from youtube_service import YouTubeError, extract_video_id, fetch_video_metadata_smart

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"
DIST_DIR = ROOT_DIR / "frontend" / "dist"
CACHE_DIR = ROOT_DIR / ".cache"
CACHE_DB = CACHE_DIR / "video_dashboard_cache.sqlite"
CACHE_TTL_SECONDS = 86400  # 24h persistent cache to eliminate redundant API calls

PLACEHOLDERS = {
    "your_youtube_data_api_key",
    "your_openrouter_api_key",
    "your_google_ai_studio_key",
    "changeme",
}


def _env_setting(name: str, default: str = "") -> str:
    val = (os.getenv(name) or default).strip()
    return "" if val.lower() in PLACEHOLDERS else val


class AnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=500)
    provider: str | None = Field(default=None, description="openrouter or gemini")
    model: str | None = Field(default=None, max_length=200)
    api_key: str | None = Field(default=None, max_length=500, description="Optional runtime LLM API key override")
    yt_key: str | None = Field(default=None, max_length=500, description="Optional YouTube Data API v3 key")
    manual_transcript: str | None = Field(default=None, max_length=400000, description="Optional pasted transcript when cloud IP is blocked")
    force_refresh: bool = Field(default=False)


class PersistentCache:
    """Lightweight SQLite + memory TTL cache so repeat video lookups use 0 API calls."""

    def __init__(self, db_path: Path, ttl: int = CACHE_TTL_SECONDS):
        self.db_path = db_path
        self.ttl = ttl
        self._mem: dict[str, tuple[float, dict]] = {}
        self._init_db()

    def _init_db(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS analysis_cache ("
                    "cache_key TEXT PRIMARY KEY, "
                    "created_at REAL NOT NULL, "
                    "payload TEXT NOT NULL)"
                )
        except Exception:
            pass

    def get(self, key: str) -> dict | None:
        now = time.time()
        cached = self._mem.get(key)
        if cached and (now - cached[0]) < self.ttl:
            return cached[1]
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT created_at, payload FROM analysis_cache WHERE cache_key = ?",
                    (key,),
                ).fetchone()
                if row and (now - float(row[0])) < self.ttl:
                    data = json.loads(row[1])
                    self._mem[key] = (float(row[0]), data)
                    return data
        except Exception:
            return None
        return None

    def set(self, key: str, value: dict) -> None:
        now = time.time()
        self._mem[key] = (now, value)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO analysis_cache (cache_key, created_at, payload) VALUES (?, ?, ?)",
                    (key, now, json.dumps(value, ensure_ascii=False)),
                )
        except Exception:
            pass


cache = PersistentCache(CACHE_DB)

app = FastAPI(
    title="Video Analyzer Executive Dashboard API",
    version="2.0.0",
    description="Low-API, transcript-grounded single-video intelligence service.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/config")
def get_config() -> dict:
    provider = _env_setting("LLM_PROVIDER", "openrouter").lower()
    if provider not in {"openrouter", "gemini"}:
        provider = "openrouter"
    has_or = bool(_env_setting("OPENROUTER_API_KEY"))
    has_gem = bool(_env_setting("GEMINI_API_KEY"))
    has_yt = bool(_env_setting("YT_KEY"))
    if not has_or and has_gem and not os.getenv("LLM_PROVIDER"):
        provider = "gemini"
    return {
        "provider": provider,
        "openrouter_model": _env_setting("OPENROUTER_MODEL") or DEFAULT_MODEL,
        "gemini_model": _env_setting("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL,
        "has_openrouter_key": has_or,
        "has_gemini_key": has_gem,
        "has_yt_key": has_yt,
        "zero_yt_key_supported": True,
    }


@app.get("/api/samples")
def list_samples() -> dict:
    items = [
        {
            "id": sid,
            "label": payload["label"],
            "video_id": payload["metadata"]["id"],
            "title": payload["metadata"]["title"],
            "channel": payload["metadata"]["channel"],
            "duration": payload["analytics"]["kpis"]["duration_label"],
            "thumbnail": payload["metadata"]["thumbnail"],
        }
        for sid, payload in SAMPLES.items()
    ]
    default_id = next(iter(SAMPLES))
    return {"samples": items, "default_sample": SAMPLES[default_id]}


@app.get("/api/samples/{sample_id}")
def get_sample(sample_id: str) -> dict:
    if sample_id not in SAMPLES:
        raise HTTPException(status_code=404, detail="Sample analysis not found.")
    return SAMPLES[sample_id]


@app.post("/api/analyze")
def analyze_endpoint(req: AnalyzeRequest) -> dict:
    t0 = time.perf_counter()
    try:
        video_id = extract_video_id(req.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    provider = (req.provider or _env_setting("LLM_PROVIDER", "openrouter")).strip().lower()
    if provider not in {"openrouter", "gemini"}:
        raise HTTPException(status_code=400, detail="Provider must be 'openrouter' or 'gemini'.")

    default_model = DEFAULT_MODEL if provider == "openrouter" else GEMINI_DEFAULT_MODEL
    env_model_var = "OPENROUTER_MODEL" if provider == "openrouter" else "GEMINI_MODEL"
    model = (req.model or _env_setting(env_model_var) or default_model).strip()

    env_key_var = "OPENROUTER_API_KEY" if provider == "openrouter" else "GEMINI_API_KEY"
    llm_key = (req.api_key or "").strip() or _env_setting(env_key_var)
    yt_key = (req.yt_key or "").strip() or _env_setting("YT_KEY")

    if not llm_key:
        key_label = "OPENROUTER_API_KEY" if provider == "openrouter" else "GEMINI_API_KEY"
        raise HTTPException(
            status_code=400,
            detail=f"Missing {key_label}. Add it in API Settings (top right) or in your .env file. (Note: YT_KEY is optional!)",
        )

    key_fingerprint = hashlib.sha256(f"{provider}:{model}:{bool(yt_key)}".encode("utf-8")).hexdigest()[:16]
    cache_key = f"v2:{video_id}:{key_fingerprint}"

    if not req.force_refresh:
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            elapsed_ms = int(round((time.perf_counter() - t0) * 1000))
            response_copy = dict(cached_payload)
            response_copy["telemetry"] = {
                **cached_payload.get("telemetry", {}),
                "elapsed_ms": elapsed_ms,
                "cached": True,
                "llm_calls": 0,
                "youtube_api_calls": 0,
            }
            return response_copy

    # Fetch metadata and transcript in parallel (with Cloud-IP Gemini Direct fallback & manual paste support)
    pasted = (req.manual_transcript or "").strip()
    raw_transcript = None
    analysis = None
    llm_calls = 0

    try:
        if pasted:
            metadata, yt_calls = fetch_video_metadata_smart(video_id, yt_key)
            raw_transcript = parse_pasted_transcript(pasted)
        else:
            with ThreadPoolExecutor(max_workers=2) as pool:
                meta_future = pool.submit(fetch_video_metadata_smart, video_id, yt_key)
                transcript_future = pool.submit(get_transcript, video_id)
                metadata, yt_calls = meta_future.result()
                try:
                    raw_transcript = transcript_future.result()
                except TranscriptBlockedError as blocked_exc:
                    # Cloud-IP bypass: if Gemini key is active, let Google Gemini ingest the YouTube URL directly!
                    fallback_gemini_key = llm_key if provider == "gemini" else _env_setting("GEMINI_API_KEY")
                    if not fallback_gemini_key:
                        raise blocked_exc
                    gemini_model = model if provider == "gemini" else (_env_setting("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL)
                    analysis, raw_transcript, llm_calls = analyze_youtube_url_via_gemini(
                        metadata=metadata,
                        video_id=video_id,
                        api_key=fallback_gemini_key,
                        model=gemini_model,
                    )
                    provider = "gemini"
                    model = gemini_model
    except YouTubeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TranscriptBlockedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TranscriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnalysisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if analysis is None:
        try:
            analysis, llm_calls = analyze_video_dashboard(
                metadata=metadata,
                transcript=raw_transcript,
                api_key=llm_key,
                model=model,
                provider=provider,
            )
        except AnalysisError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    analytics = build_dashboard_analytics(metadata, raw_transcript, analysis)
    formatted_segments = [
        {
            "start": seg["start"],
            "duration": seg["duration"],
            "text": seg["text"],
            "formatted_time": format_timestamp(seg["start"]),
        }
        for seg in raw_transcript["segments"]
    ]

    elapsed_ms = int(round((time.perf_counter() - t0) * 1000))
    payload = {
        "metadata": metadata,
        "analysis": analysis,
        "analytics": analytics,
        "transcript": {
            "language": raw_transcript["language"],
            "language_code": raw_transcript["language_code"],
            "is_generated": raw_transcript["is_generated"],
            "segments": formatted_segments,
        },
        "telemetry": {
            "elapsed_ms": elapsed_ms,
            "cached": False,
            "sample": False,
            "llm_calls": llm_calls,
            "youtube_api_calls": yt_calls,
            "provider": provider,
            "model": model,
        },
    }
    cache.set(cache_key, payload)
    return payload


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found.")
    ui_dir = STATIC_DIR if (STATIC_DIR / "index.html").is_file() else DIST_DIR
    if not ui_dir.exists():
        raise HTTPException(status_code=404, detail="Frontend assets not found.")
    candidate = (ui_dir / full_path).resolve()
    if full_path and candidate.is_file() and str(candidate).startswith(str(ui_dir)):
        return FileResponse(str(candidate))
    index_file = ui_dir / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="Frontend build not found.")
