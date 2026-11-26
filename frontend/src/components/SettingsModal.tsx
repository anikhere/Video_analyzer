import React, { useEffect, useState } from 'react';
import { CheckCircle2, KeyRound, ShieldCheck, X, Zap } from 'lucide-react';
import { RuntimeSettings, ServerConfig } from '../types';

interface Props {
  open: boolean;
  onClose: () => void;
  serverConfig: ServerConfig | null;
  settings: RuntimeSettings;
  onSave: (next: RuntimeSettings) => void;
}

export const SettingsModal: React.FC<Props> = ({
  open,
  onClose,
  serverConfig,
  settings,
  onSave,
}) => {
  const [draft, setDraft] = useState<RuntimeSettings>(settings);

  useEffect(() => {
    if (open) {
      setDraft(settings);
    }
  }, [open, settings]);

  if (!open) return null;

  const hasEnvKeyForSelected =
    draft.provider === 'openrouter'
      ? serverConfig?.has_openrouter_key
      : serverConfig?.has_gemini_key;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(draft);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#030816]/80 backdrop-blur-sm">
      <div className="w-full max-w-lg royal-card rounded-2xl p-6 shadow-2xl border border-white/20">
        <div className="flex items-center justify-between pb-4 border-b border-blue-300/15">
          <div className="flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-xl bg-white text-[#07132E] grid place-items-center">
              <KeyRound className="w-4 h-4" />
            </span>
            <div>
              <h3 className="text-base font-bold text-white">Low-API Engine &amp; Key Settings</h3>
              <p className="text-xs text-blue-200/80">
                Single-pass LLM pipeline · Zero YouTube API key required
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-blue-200 hover:text-white hover:bg-white/10 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Efficiency Banner */}
          <div className="rounded-xl bg-[#0F2454] border border-blue-300/25 p-3.5 text-xs text-blue-100 space-y-1">
            <div className="font-bold text-white flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-blue-300" />
              Optimized Low-API Mode Active
            </div>
            <p className="text-blue-100/85 leading-relaxed">
              Only <strong>1 LLM API key</strong> is needed. YouTube metadata uses zero-key oEmbed automatically unless you optionally supply <code className="text-white">YT_KEY</code> for view/like counts. Videos up to ~95 minutes run in <strong>1 single LLM call</strong> and cache for 24h.
            </p>
          </div>

          {/* Provider */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-blue-200 mb-2">
              LLM Provider
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() =>
                  setDraft((d) => ({
                    ...d,
                    provider: 'openrouter',
                    model: serverConfig?.openrouter_model || 'openrouter/free',
                  }))
                }
                className={`p-3 rounded-xl border text-left transition ${
                  draft.provider === 'openrouter'
                    ? 'bg-white text-[#07132E] border-white font-bold'
                    : 'bg-[#081533] text-white border-blue-300/20 hover:border-blue-300/40'
                }`}
              >
                <div className="text-sm font-bold">OpenRouter</div>
                <div className={`text-[11px] ${draft.provider === 'openrouter' ? 'text-blue-800' : 'text-blue-200/75'}`}>
                  Supports free &amp; multi-provider models
                </div>
              </button>

              <button
                type="button"
                onClick={() =>
                  setDraft((d) => ({
                    ...d,
                    provider: 'gemini',
                    model: serverConfig?.gemini_model || 'gemini-3.5-flash-lite',
                  }))
                }
                className={`p-3 rounded-xl border text-left transition ${
                  draft.provider === 'gemini'
                    ? 'bg-white text-[#07132E] border-white font-bold'
                    : 'bg-[#081533] text-white border-blue-300/20 hover:border-blue-300/40'
                }`}
              >
                <div className="text-sm font-bold">Google Gemini</div>
                <div className={`text-[11px] ${draft.provider === 'gemini' ? 'text-blue-800' : 'text-blue-200/75'}`}>
                  Fast 1M-token native JSON mode
                </div>
              </button>
            </div>
          </div>

          {/* LLM API Key */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-blue-200">
                {draft.provider === 'openrouter' ? 'OpenRouter API Key' : 'Gemini API Key'}
              </label>
              {hasEnvKeyForSelected && (
                <span className="inline-flex items-center gap-1 text-[11px] text-emerald-300 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Configured in server .env
                </span>
              )}
            </div>
            <input
              type="password"
              value={draft.apiKey}
              onChange={(e) => setDraft((d) => ({ ...d, apiKey: e.target.value }))}
              placeholder={
                hasEnvKeyForSelected
                  ? 'Using server .env key (leave blank or paste override)...'
                  : `Paste your ${draft.provider === 'openrouter' ? 'sk-or-v1-...' : 'AIza... or AQ....'} key`
              }
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#07122B] border border-blue-300/25 focus:border-white focus:outline-none text-sm text-white placeholder-blue-200/45 font-mono"
            />
            {draft.provider === 'gemini' && draft.apiKey.trim().startsWith('sk-or-') && (
              <p className="mt-1.5 text-[11px] text-amber-300">
                This looks like an OpenRouter key — Gemini needs an AI Studio key (AIza... or AQ....).
              </p>
            )}
            {draft.provider === 'openrouter' &&
              (draft.apiKey.trim().startsWith('AIza') || draft.apiKey.trim().startsWith('AQ.')) && (
                <p className="mt-1.5 text-[11px] text-amber-300">
                  This looks like a Gemini key — OpenRouter needs a sk-or-... key.
                </p>
              )}
            {draft.provider === 'gemini' && (
              <p className="mt-1.5 text-[11px] text-blue-200/70">
                Both AIza... and AQ.... keys work. Getting 403? Create a fresh key at aistudio.google.com/apikey
                and enable &ldquo;Generative Language API&rdquo; for its project.
              </p>
            )}
          </div>

          {/* Model ID */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-blue-200 mb-1.5">
              Model ID
            </label>
            <input
              type="text"
              value={draft.model}
              onChange={(e) => setDraft((d) => ({ ...d, model: e.target.value }))}
              placeholder={draft.provider === 'openrouter' ? 'openrouter/free' : 'gemini-3.5-flash-lite'}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#07122B] border border-blue-300/25 focus:border-white focus:outline-none text-sm text-white font-mono"
            />
          </div>

          {/* Optional YouTube Key */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-blue-200">
                YouTube Data API v3 Key <span className="text-blue-300 font-normal">(Optional)</span>
              </label>
              <span className="text-[11px] text-blue-200/75">
                {serverConfig?.has_yt_key ? 'Active in .env' : 'Optional — Zero-Key oEmbed active'}
              </span>
            </div>
            <input
              type="password"
              value={draft.ytKey}
              onChange={(e) => setDraft((d) => ({ ...d, ytKey: e.target.value }))}
              placeholder="Leave empty to save API setup, or add for View/Like stats"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#07122B] border border-blue-300/25 focus:border-white focus:outline-none text-sm text-white placeholder-blue-200/45 font-mono"
            />
          </div>

          <div className="pt-2 flex items-center justify-between gap-3">
            <span className="inline-flex items-center gap-1.5 text-[11px] text-blue-200/75">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-300" />
              Stored only in current browser session
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-blue-100 hover:bg-white/10 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl text-xs font-bold bg-white text-[#07132E] hover:bg-blue-50 transition shadow"
              >
                Save Settings
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
