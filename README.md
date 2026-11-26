# Video Analyzer

A transcript-grounded AI assistant for understanding a **single YouTube video** without watching it all. Paste a URL to get a summary, topics, takeaways, important moments, action items, audience, terminology, and conclusion, alongside video metadata and the transcript. This is not a channel analytics tool.

## Requirements

- Python 3.10 or newer
- A YouTube Data API v3 key and an OpenRouter API key
- A public video with an accessible caption track

## Run locally

```bash
git clone https://github.com/anikhere/Video_analyzer.git
cd Video_analyzer
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Windows: copy .env.example .env
```

Edit `.env` with your own keys (do not commit or share this file):

```dotenv
YT_KEY=your_youtube_data_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
```

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project, enable **YouTube Data API v3**, and create an API key under APIs & Services → Credentials. Configure appropriate key restrictions for your deployment.
2. Create an API key at [OpenRouter](https://openrouter.ai/keys). The default `openrouter/free` routes to available free models, subject to availability and request limits. Free routing is not guaranteed to be available at all times.
3. Run:

```bash
streamlit run app.py
```

Enter a `youtube.com/watch?v=…`, `youtu.be/…`, `youtube.com/shorts/…`, or `youtube.com/embed/…` URL and select **Analyze video**. URL parameters such as `t` and `si` are supported. The app validates the URL before any API call.

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub, then create an app at [Streamlit Community Cloud](https://share.streamlit.io/) and select this repository, branch, and `app.py` as the entry point.
2. Under **Advanced settings → Secrets**, add the following TOML with your actual keys:

```toml
YT_KEY = "your_youtube_data_api_key"
OPENROUTER_API_KEY = "your_openrouter_api_key"
OPENROUTER_MODEL = "openrouter/free"
```

3. Deploy. Streamlit installs `requirements.txt` automatically. Secrets take precedence over environment variables; never commit `.env` or `.streamlit/secrets.toml`. You can also use environment variables on other hosting platforms.

## How it works & limitations

- YouTube Data API retrieves video metadata; `youtube-transcript-api` fetches available captions, preferring English (manual before generated) and otherwise choosing the first available language. Captions are not translated by the transcript service; OpenRouter is asked to analyze them in English.
- Captions are cleaned while retaining segment timestamps. Long transcripts are split into bounded chunks, summarized with timestamps, and hierarchically consolidated before final analysis. Very long videos consume more model requests and may reach free-model limits. An hour-long cache reduces repeat requests; the model, keys, transcript and metadata are included in the relevant cache keys. Cached data is shared across sessions on the server and expires after one hour.
- AI output is instructed to use only the transcript, and timestamps not present in the original transcript are discarded. AI and captions can still make mistakes or lose context, especially with automatic captions and multi-stage summarization. Check the transcript and video for important decisions; timestamp existence does not guarantee the explanation is correct.
- If captions are disabled, unavailable, empty, or blocked, no full analysis is generated. YouTube may block transcript requests from cloud IPs, including Streamlit Community Cloud. Try another network or run locally; an API key does not grant access to captions through this library. Private/deleted videos, restricted keys, exhausted YouTube or OpenRouter free-model limits, and unsupported model/region access also produce errors.
- API keys stay on the server. Do not deploy on an untrusted server or expose your secret files. Your video transcript is sent through OpenRouter to the selected model provider for analysis; review OpenRouter's and the selected provider's terms and privacy policies before processing sensitive material.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests mock external APIs and do not require keys. A live end-to-end run requires valid keys and network access to YouTube and OpenRouter.
