import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Download,
  Loader2,
  Play,
  SlidersHorizontal,
  Sparkles,
  Youtube,
  Zap,
} from 'lucide-react';
import { AnalyticsCharts } from './components/AnalyticsCharts';
import { ExecutiveSummaryCard } from './components/ExecutiveSummaryCard';
import { InsightsSections } from './components/InsightsSections';
import { InteractiveTimeline } from './components/InteractiveTimeline';
import { SettingsModal } from './components/SettingsModal';
import { TranscriptExplorer } from './components/TranscriptExplorer';
import { VideoOverviewCard } from './components/VideoOverviewCard';
import {
  DashboardPayload,
  RuntimeSettings,
  SampleSummary,
  ServerConfig,
} from './types';
import { buildMarkdownReport } from './utils/exportMarkdown';

const STORAGE_KEY = 'video_analyzer_runtime_settings_v2';

// Retired Gemini models that 404 for new keys — auto-migrate saved settings.
const RETIRED_GEMINI_MODELS = new Set([
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'gemini-2.5-flash-lite',
  'gemini-2.0-flash',
  'gemini-2.0-flash-lite',
  'gemini-1.5-flash',
  'gemini-1.5-pro',
]);

function loadSavedSettings(): RuntimeSettings {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch {
    // ignore storage errors
  }
  return {
    provider: 'openrouter',
    model: 'openrouter/free',
    apiKey: '',
    ytKey: '',
  };
}

export function App() {
  const [urlInput, setUrlInput] = useState('');
  const [serverConfig, setServerConfig] = useState<ServerConfig | null>(null);
  const [settings, setSettings] = useState<RuntimeSettings>(loadSavedSettings);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const [samples, setSamples] = useState<SampleSummary[]>([]);
  const [activeSampleId, setActiveSampleId] = useState<string>('');
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);

  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPasteBox, setShowPasteBox] = useState(false);
  const [manualTranscript, setManualTranscript] = useState('');

  const [seekState, setSeekState] = useState<{ seconds: number; nonce: number }>({
    seconds: 0,
    nonce: 0,
  });
  const [transcriptFilter, setTranscriptFilter] = useState<{ query: string; nonce: number }>({
    query: '',
    nonce: 0,
  });

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      try {
        const [cfgRes, sampRes] = await Promise.all([
          fetch('/api/config'),
          fetch('/api/samples'),
        ]);
        if (!cancelled && cfgRes.ok) {
          const cfg: ServerConfig = await cfgRes.json();
          setServerConfig(cfg);
          setSettings((prev) => {
            const serverModel =
              cfg.provider === 'gemini' ? cfg.gemini_model : cfg.openrouter_model;
            // A model saved in the browser overrides the server env (e.g. on
            // Render) — but never keep a retired Gemini model that 404s.
            const keepSaved =
              prev.apiKey &&
              prev.model &&
              !(prev.provider === 'gemini' && RETIRED_GEMINI_MODELS.has(prev.model.trim()));
            return {
              ...prev,
              provider: prev.apiKey ? prev.provider : cfg.provider,
              model: keepSaved ? prev.model : serverModel,
            };
          });
        }
        if (!cancelled && sampRes.ok) {
          const sampData = await sampRes.json();
          setSamples(sampData.samples || []);
          if (sampData.default_sample) {
            setDashboard(sampData.default_sample);
            setActiveSampleId(sampData.default_sample.id || '');
          }
        }
      } catch {
        if (!cancelled) {
          setError('Could not connect to backend API. Ensure the FastAPI server is running.');
        }
      } finally {
        if (!cancelled) setInitialLoading(false);
      }
    }
    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSaveSettings = (next: RuntimeSettings) => {
    setSettings(next);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // ignore
    }
  };

  const handleSelectSample = async (sampleId: string) => {
    setError(null);
    setActiveSampleId(sampleId);
    setSeekState({ seconds: 0, nonce: 0 });
    try {
      const res = await fetch(`/api/samples/${encodeURIComponent(sampleId)}`);
      if (!res.ok) throw new Error('Failed to load sample report.');
      const data: DashboardPayload = await res.json();
      setDashboard(data);
    } catch (err: any) {
      setError(err.message || 'Could not load sample.');
    }
  };

  const handleAnalyzeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = urlInput.trim();
    if (!trimmed) {
      setError('Enter a valid YouTube video URL first.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: trimmed,
          provider: settings.provider,
          model: settings.model,
          api_key: settings.apiKey || undefined,
          yt_key: settings.ytKey || undefined,
          manual_transcript: manualTranscript.trim() || undefined,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = body.detail || 'Video analysis failed. Check your URL and API key.';
        if (msg.toLowerCase().includes('blocked')) {
          setShowPasteBox(true);
        }
        throw new Error(msg);
      }
      setActiveSampleId('');
      setSeekState({ seconds: 0, nonce: 0 });
      setManualTranscript('');
      setShowPasteBox(false);
      setDashboard(body);
    } catch (err: any) {
      setError(err.message || 'Unable to analyze video.');
    } finally {
      setLoading(false);
    }
  };

  const handleSeek = (seconds: number) => {
    setSeekState((prev) => ({ seconds: Math.max(0, Math.floor(seconds)), nonce: prev.nonce + 1 }));
    const el = document.getElementById('overview-section');
    if (el && window.scrollY > 420) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleFilterTranscript = (query: string) => {
    setTranscriptFilter((prev) => ({ query, nonce: prev.nonce + 1 }));
    const el = document.getElementById('transcript-explorer');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleExportMarkdown = () => {
    if (!dashboard) return;
    const md = buildMarkdownReport(dashboard);
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `video-brief-${dashboard.metadata.id}.md`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const isKeyConfigured = Boolean(
    settings.apiKey ||
      (settings.provider === 'openrouter'
        ? serverConfig?.has_openrouter_key
        : serverConfig?.has_gemini_key)
  );

  return (
    <div className="min-h-screen text-white flex flex-col">
      {/* Sticky Dark Royal Blue & White Command Header */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[#061026]/90 border-b border-blue-300/15">
        <div className="max-w-[1380px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white text-[#07132E] grid place-items-center shadow-md font-extrabold">
              <Play className="w-4 h-4 fill-current ml-0.5" />
            </div>
            <div>
              <div className="text-sm font-extrabold tracking-tight text-white flex items-center gap-2">
                VIDEO ANALYZER
                <span className="hidden sm:inline-block px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-blue-600 text-white">
                  Executive v2
                </span>
              </div>
              <div className="text-[11px] text-blue-200/75 hidden sm:block">
                Transcript-Grounded Single-Video Intelligence
              </div>
            </div>
          </div>

          {/* Section Quick-Jump Nav */}
          {dashboard && (
            <nav className="hidden xl:flex items-center gap-1 bg-[#0A1A3D] border border-blue-300/15 rounded-xl p-1 text-xs">
              <a href="#overview-section" className="px-3 py-1.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition font-medium">
                Summary &amp; Video
              </a>
              <a href="#timeline-section" className="px-3 py-1.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition font-medium">
                Timeline
              </a>
              <a href="#graphs-section" className="px-3 py-1.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition font-medium">
                Analytics Graphs
              </a>
              <a href="#takeaways-section" className="px-3 py-1.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition font-medium">
                Takeaways &amp; Terms
              </a>
              <a href="#transcript-explorer" className="px-3 py-1.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition font-medium">
                Transcript
              </a>
            </nav>
          )}

          {/* Right Action Controls */}
          <div className="flex items-center gap-2">
            {dashboard?.telemetry && (
              <div
                className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#0C1E47] border border-blue-300/20 text-[11px] font-mono text-blue-100 tabular-nums"
                title="API Call & Latency Telemetry"
              >
                <Zap className="w-3.5 h-3.5 text-blue-300" />
                {dashboard.telemetry.sample ? (
                  <span>Sample · 0 API calls</span>
                ) : dashboard.telemetry.cached ? (
                  <span>Cached · 0 API calls · {dashboard.telemetry.elapsed_ms}ms</span>
                ) : (
                  <span>
                    {dashboard.telemetry.llm_calls} LLM · {dashboard.telemetry.youtube_api_calls} YT API ·{' '}
                    {(dashboard.telemetry.elapsed_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
            )}

            {dashboard && (
              <button
                type="button"
                onClick={handleExportMarkdown}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[#0F2352] hover:bg-[#173270] text-white border border-blue-300/25 transition"
                title="Download Executive Markdown Brief"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Export .md</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-white text-[#07132E] hover:bg-blue-50 transition shadow-sm"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>API Settings</span>
              <span
                className={`w-2 h-2 rounded-full ${
                  isKeyConfigured ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
                title={isKeyConfigured ? 'LLM key configured' : 'Click to add OpenRouter or Gemini key'}
              />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="flex-1 max-w-[1380px] w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
        {/* URL Command & Sample Showcase Bar */}
        <section className="royal-card rounded-2xl p-5 sm:p-6">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest text-blue-300 mb-1">
                <Sparkles className="w-3.5 h-3.5" />
                Single-Video Deep Intelligence · Low-API Pipeline
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                Understand any YouTube video in minutes, backed by data &amp; exact timestamps.
              </h1>
            </div>

            {/* Instant Sample Switcher */}
            {samples.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] uppercase tracking-wider font-semibold text-blue-200/75 mr-1">
                  Instant Demo:
                </span>
                {samples.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => handleSelectSample(s.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition border ${
                      activeSampleId === s.id
                        ? 'bg-blue-600 text-white border-blue-400 shadow-sm'
                        : 'bg-[#081533] text-blue-100 border-blue-300/20 hover:bg-[#102452]'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* URL Input Form */}
          <form onSubmit={handleAnalyzeSubmit} className="mt-4 flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Youtube className="w-5 h-5 text-blue-300 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Paste any YouTube URL (youtube.com/watch?v=..., youtu.be/..., shorts/...) "
                disabled={loading}
                className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-[#061129] border border-blue-300/30 focus:border-white focus:outline-none text-sm text-white placeholder-blue-200/50 shadow-inner"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3.5 rounded-xl bg-white text-[#07132E] hover:bg-blue-50 disabled:opacity-60 font-extrabold text-sm transition shadow-lg inline-flex items-center justify-center gap-2 shrink-0"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing Video…
                </>
              ) : (
                <>
                  Analyze Video
                  <Sparkles className="w-4 h-4 text-blue-600" />
                </>
              )}
            </button>
          </form>

          {/* Status / Error Feedback */}
          {loading && (
            <div className="mt-4 rounded-xl bg-[#0D214F] border border-blue-400/30 px-4 py-3 flex flex-wrap items-center justify-between gap-2 text-xs text-blue-100">
              <span className="inline-flex items-center gap-2 font-semibold text-white">
                <Loader2 className="w-4 h-4 animate-spin text-blue-300" />
                Running parallel metadata + caption retrieval, then 1-call grounded LLM synthesis…
              </span>
              <span className="font-mono text-blue-200/80">Zero extra API calls for graphs</span>
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-xl bg-red-950/60 border border-red-400/40 px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-xs text-red-100">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 text-red-300 shrink-0" />
                <span>{error}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {error.toLowerCase().includes('blocked') && (
                  <button
                    type="button"
                    onClick={() => setShowPasteBox((v) => !v)}
                    className="px-3 py-1.5 rounded-lg bg-blue-600 text-white font-bold text-xs hover:bg-blue-500 transition"
                  >
                    {showPasteBox ? 'Hide Paste Box' : 'Paste Transcript'}
                  </button>
                )}
                {(error.includes('API') || error.toLowerCase().includes('gemini')) && (
                  <button
                    type="button"
                    onClick={() => setSettingsOpen(true)}
                    className="px-3 py-1.5 rounded-lg bg-white text-[#07132E] font-bold text-xs hover:bg-blue-50 transition"
                  >
                    Switch to Gemini / API Settings
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Optional Paste Transcript Drawer for Cloud-IP Blocked OpenRouter Hosts */}
          <div className="mt-2.5 flex items-center justify-end">
            <button
              type="button"
              onClick={() => setShowPasteBox((v) => !v)}
              className="text-[11px] text-blue-200/75 hover:text-white underline underline-offset-4"
            >
              {showPasteBox ? 'Hide manual transcript input' : 'Cloud IP blocked on YouTube? Paste transcript manually'}
            </button>
          </div>

          {showPasteBox && (
            <div className="mt-3 rounded-xl bg-[#07132E] border border-blue-300/25 p-4 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-white">
                  Manual Transcript Fallback (Works on Any Cloud Server)
                </span>
                <span className="text-blue-200/75">
                  On YouTube: click &ldquo;…more&rdquo; → &ldquo;Show transcript&rdquo; → Copy &amp; paste here
                </span>
              </div>
              <textarea
                rows={4}
                value={manualTranscript}
                onChange={(e) => setManualTranscript(e.target.value)}
                placeholder="Paste YouTube transcript lines (with or without timestamps) and click Analyze Video above..."
                className="w-full p-3 rounded-xl bg-[#050C1E] border border-blue-300/25 focus:border-white focus:outline-none text-xs text-white placeholder-blue-200/45 font-mono"
              />
            </div>
          )}
        </section>

        {/* Dashboard Body */}
        {initialLoading ? (
          <div className="royal-card rounded-2xl p-12 text-center">
            <Loader2 className="w-7 h-7 animate-spin text-blue-300 mx-auto mb-3" />
            <p className="text-sm font-semibold text-white">Loading Video Intelligence Dashboard…</p>
          </div>
        ) : dashboard ? (
          <div className="space-y-6">
            {/* Row 1: Video Overview (5 cols) + Executive Summary "What is this video all about?" (7 cols) */}
            <div id="overview-section" className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch scroll-mt-20">
              <div className="lg:col-span-5">
                <VideoOverviewCard
                  metadata={dashboard.metadata}
                  kpis={dashboard.analytics.kpis}
                  transcript={dashboard.transcript}
                  seekState={seekState}
                  onSeek={handleSeek}
                />
              </div>
              <div className="lg:col-span-7">
                <ExecutiveSummaryCard
                  analysis={dashboard.analysis}
                  kpis={dashboard.analytics.kpis}
                />
              </div>
            </div>

            {/* Row 2: Interactive Segmented Timeline & Important Moments */}
            <div id="timeline-section" className="scroll-mt-20">
              <InteractiveTimeline
                chapters={dashboard.analytics.chapters}
                moments={dashboard.analytics.moment_pins}
                videoUrl={dashboard.metadata.url}
                durationLabel={dashboard.analytics.kpis.duration_label}
                onSeek={handleSeek}
              />
            </div>

            {/* Row 3: Data-Grounded Analytical Graphs */}
            <div id="graphs-section" className="scroll-mt-20">
              <AnalyticsCharts
                analytics={dashboard.analytics}
                onSeek={handleSeek}
                onFilterTranscript={handleFilterTranscript}
              />
            </div>

            {/* Row 4: Key Takeaways, Topics, Audience, Action Items, Terminology */}
            <div id="takeaways-section" className="scroll-mt-20">
              <InsightsSections
                analysis={dashboard.analysis}
                onFilterTranscript={handleFilterTranscript}
              />
            </div>

            {/* Row 5: Expandable & Searchable Transcript */}
            <TranscriptExplorer
              transcript={dashboard.transcript}
              chapters={dashboard.analytics.chapters}
              externalQuery={transcriptFilter.query}
              externalNonce={transcriptFilter.nonce}
              onSeek={handleSeek}
            />
          </div>
        ) : null}
      </main>

      {/* Footer */}
      <footer className="border-t border-blue-300/15 py-5 mt-8 text-center text-xs text-blue-200/65">
        <div className="max-w-[1380px] mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Video Analyzer · Single-Video Transcript-Grounded Intelligence Dashboard</span>
          <span>AI summaries can make mistakes — click any timestamp to verify directly against the source video &amp; transcript.</span>
        </div>
      </footer>

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        serverConfig={serverConfig}
        settings={settings}
        onSave={handleSaveSettings}
      />
    </div>
  );
}

export default App;
