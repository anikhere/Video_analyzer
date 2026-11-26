# Video Analyzer — Single-Video Intelligence Dashboard

A fast, low-API, transcript-grounded executive dashboard for understanding a **single YouTube video** without watching it end-to-end. Built with **FastAPI + React + Tailwind CSS + Recharts** in a Dark Royal Blue & Crisp White design system.

## Key Highlights

- **Executive Summary ("What Is This Video All About?"):** Bold 1-sentence core thesis, full narrative overview, and 3-pillar breakdown (*Why It Matters*, *How It's Covered*, *Bottom-Line Verdict*).
- **Synced Video Player & Telemetry:** Embedded YouTube player synced to every timestamp, chart bar, chapter block, and transcript line—paired with duration, word count, speaking pace (WPM), time saved, and engagement stats.
- **Data-Grounded Interactive Graphs (0 Extra API Calls):**
  1. **Proportional Chapter & Key-Moments Timeline** (`00:00` → `End`) with clickable milestone pins.
  2. **Speaking Pace (WPM) & Information Density Over Time** area/line chart computed deterministically from caption segments.
  3. **Topic & Chapter Time Share** donut/bar chart showing exact duration and percentage spent per section.
  4. **Verified Concept & Term Prominence** horizontal bar chart counting grounded mentions across the transcript.
- **Low-API, High-Speed Architecture:**
  - **Zero YouTube API Key Required:** Automatically uses public YouTube oEmbed + transcript-derived duration when `YT_KEY` is omitted (only **1 LLM API key** needed!). Add `YT_KEY` optionally for view/like/comment statistics.
  - **Parallel Network Retrieval:** Fetches metadata and captions simultaneously.
  - **Single-Pass Extended Context:** Compacts micro-captions (~30% smaller prompt while preserving exact start timestamps) so videos up to ~95 minutes run in **1 single LLM API call** instead of 3–6 sequential calls.
  - **24-Hour Persistent SQLite + Memory Cache:** Repeat lookups return in milliseconds with **0 external API calls**.
- **Actionable Insights & Searchable Transcript:** Numbered takeaways, clickable topic pills, interactive action-item checklist, terminology glossary, Markdown export (`.md`), and chapter-filtered instant transcript search.

---

## Quick Start (FastAPI + React Dashboard)

### 1. Backend Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your **OpenRouter** key (or **Google Gemini** key)—or leave `.env` empty and enter your key directly inside the dashboard's **API Settings** modal:

```dotenv
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
# Optional (only for view/like counts):
# YT_KEY=your_youtube_data_api_key
```

### 2. Start the Dashboard Server (No Node.js Required!)

The production React UI is pre-built in `static/`, so you can launch the full dashboard immediately with Python alone:

```bash
# macOS / Linux
.venv/bin/uvicorn api:app --host 127.0.0.1 --port 8000

# Windows PowerShell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` to view the full dashboard (pre-loaded with instant zero-API sample reports so you can explore immediately).

### Optional: Rebuild Frontend After Editing React Source (`frontend/`)

If you modify files inside `frontend/src/` (requires Node.js 18+):

```bash
cd frontend
npm install
npm run build   # outputs updated bundle directly into ../static
cd ..
```

### Frontend Hot-Reload Development Mode

Run FastAPI on port `8000` and Vite dev server (proxying `/api` to `127.0.0.1:8000`) on port `5173`:

```bash
# Terminal 1
.venv/bin/uvicorn api:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2
cd frontend && npm run dev
```

---

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

All unit and API endpoint tests mock external network calls and run without live API keys.
