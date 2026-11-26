import React, { useState } from 'react';
import {
  Calendar,
  ChevronDown,
  ChevronUp,
  Clock,
  ExternalLink,
  Eye,
  FileText,
  Gauge,
  Image as ImageIcon,
  Play,
  ThumbsUp,
  Tv,
  Zap,
} from 'lucide-react';
import { DashboardKPIs, VideoMetadata, VideoTranscript } from '../types';

interface Props {
  metadata: VideoMetadata;
  kpis: DashboardKPIs;
  transcript: VideoTranscript;
  seekState: { seconds: number; nonce: number };
  onSeek: (seconds: number) => void;
}

function formatCompactNumber(value: number | null): string {
  if (value === null || value === undefined) return '—';
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2).replace(/\.00$/, '')}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1).replace(/\.0$/, '')}K`;
  return value.toLocaleString();
}

function formatDate(iso: string): string {
  if (!iso) return 'Public YouTube Video';
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return 'Public YouTube Video';
  return parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatSec(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`
    : `${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`;
}

export const VideoOverviewCard: React.FC<Props> = ({
  metadata,
  kpis,
  transcript,
  seekState,
  onSeek,
}) => {
  const [viewMode, setViewMode] = useState<'player' | 'poster'>('player');
  const [showDesc, setShowDesc] = useState(false);

  const embedSrc = `https://www.youtube-nocookie.com/embed/${metadata.id}?start=${seekState.seconds}&autoplay=${
    seekState.nonce > 0 ? 1 : 0
  }&rel=0&modestbranding=1`;

  return (
    <section className="royal-card rounded-2xl p-5 sm:p-6 flex flex-col justify-between h-full">
      <div>
        {/* Top bar inside Video Overview */}
        <div className="flex items-center justify-between gap-2 mb-3.5">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider bg-white text-[#081430]">
              <Tv className="w-3.5 h-3.5" />
              Video Overview
            </span>
            {seekState.nonce > 0 && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium bg-blue-500/20 text-blue-100 border border-blue-400/30">
                <Play className="w-3 h-3 fill-current" />
                Synced @ {formatSec(seekState.seconds)}
              </span>
            )}
          </div>

          <div className="inline-flex rounded-lg bg-[#07122B] p-0.5 border border-blue-300/15 text-xs">
            <button
              type="button"
              onClick={() => setViewMode('player')}
              className={`px-2.5 py-1 rounded-md font-medium transition flex items-center gap-1 ${
                viewMode === 'player'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-blue-200/75 hover:text-white'
              }`}
            >
              <Play className="w-3 h-3" />
              Player
            </button>
            <button
              type="button"
              onClick={() => setViewMode('poster')}
              className={`px-2.5 py-1 rounded-md font-medium transition flex items-center gap-1 ${
                viewMode === 'poster'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-blue-200/75 hover:text-white'
              }`}
            >
              <ImageIcon className="w-3 h-3" />
              Thumbnail
            </button>
          </div>
        </div>

        {/* Video Frame */}
        <div className="relative aspect-video w-full rounded-xl overflow-hidden bg-[#040A18] border border-blue-300/20 shadow-inner">
          {viewMode === 'player' ? (
            <iframe
              key={`${metadata.id}-${seekState.nonce}`}
              src={embedSrc}
              title={metadata.title}
              className="w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <button
              type="button"
              onClick={() => {
                setViewMode('player');
                onSeek(0);
              }}
              className="group relative w-full h-full block text-left"
            >
              {metadata.thumbnail ? (
                <img
                  src={metadata.thumbnail}
                  alt={metadata.title}
                  className="w-full h-full object-cover group-hover:scale-[1.02] transition duration-300"
                />
              ) : (
                <div className="w-full h-full grid place-items-center text-blue-200/60 text-sm">
                  Thumbnail unavailable
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-[#050C1E]/90 via-[#050C1E]/25 to-transparent flex items-center justify-center">
                <span className="w-14 h-14 rounded-full bg-white text-[#081430] grid place-items-center shadow-xl group-hover:scale-105 transition">
                  <Play className="w-6 h-6 fill-current ml-0.5" />
                </span>
              </div>
              <span className="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-[#050C1E]/90 border border-white/15 font-mono text-xs text-white tabular-nums">
                {kpis.duration_label}
              </span>
            </button>
          )}
        </div>

        {/* Title & Metadata */}
        <div className="mt-4">
          <h2 className="text-lg sm:text-xl font-bold text-white leading-snug tracking-tight">
            {metadata.title}
          </h2>

          <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-blue-100/80">
            <span className="font-semibold text-white bg-blue-600/30 border border-blue-400/30 px-2.5 py-0.5 rounded-md">
              {metadata.channel}
            </span>
            <span className="inline-flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-blue-300" />
              {formatDate(metadata.published_at)}
            </span>
            <span className="inline-flex items-center gap-1 font-mono tabular-nums text-white">
              <Clock className="w-3.5 h-3.5 text-blue-300" />
              {kpis.duration_label}
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#102452] border border-blue-300/15 text-blue-100">
              {transcript.language} · {transcript.is_generated ? 'Auto Captions' : 'Verified Captions'}
            </span>
            <a
              href={metadata.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-white hover:text-blue-200 font-medium underline underline-offset-4 ml-auto"
            >
              YouTube
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>

      {/* 6-KPI Telemetry Matrix */}
      <div className="mt-5 pt-4 border-t border-blue-300/15">
        <div className="grid grid-cols-3 gap-2.5">
          <div className="royal-subcard rounded-xl p-3">
            <div className="flex items-center justify-between text-[11px] text-blue-200/75 font-medium">
              <span>Spoken Words</span>
              <FileText className="w-3.5 h-3.5 text-blue-300" />
            </div>
            <div className="mt-1 text-base sm:text-lg font-bold font-mono tabular-nums text-white">
              {kpis.word_count.toLocaleString()}
            </div>
            <div className="text-[11px] text-blue-200/65">
              ~{kpis.transcript_read_minutes}m full text
            </div>
          </div>

          <div className="royal-subcard rounded-xl p-3">
            <div className="flex items-center justify-between text-[11px] text-blue-200/75 font-medium">
              <span>Speaking Pace</span>
              <Gauge className="w-3.5 h-3.5 text-blue-300" />
            </div>
            <div className="mt-1 text-base sm:text-lg font-bold font-mono tabular-nums text-white">
              {kpis.avg_wpm} <span className="text-xs font-sans font-normal text-blue-200/80">WPM</span>
            </div>
            <div className="text-[11px] text-blue-200/65">{kpis.pace_category}</div>
          </div>

          <div className="rounded-xl p-3 bg-white text-[#07132E] shadow-sm">
            <div className="flex items-center justify-between text-[11px] text-[#1D3B7A] font-semibold">
              <span>Time Saved</span>
              <Zap className="w-3.5 h-3.5 text-blue-600" />
            </div>
            <div className="mt-1 text-base sm:text-lg font-extrabold font-mono tabular-nums text-[#050C1E]">
              {kpis.time_saved_minutes}m
            </div>
            <div className="text-[11px] font-semibold text-blue-700">
              {kpis.time_saved_pct}% faster brief
            </div>
          </div>

          <div className="royal-subcard rounded-xl p-3">
            <div className="flex items-center justify-between text-[11px] text-blue-200/75 font-medium">
              <span>{kpis.view_count !== null ? 'Total Views' : 'Segments'}</span>
              <Eye className="w-3.5 h-3.5 text-blue-300" />
            </div>
            <div className="mt-1 text-base sm:text-lg font-bold font-mono tabular-nums text-white">
              {kpis.view_count !== null
                ? formatCompactNumber(kpis.view_count)
                : kpis.segment_count.toLocaleString()}
            </div>
            <div className="text-[11px] text-blue-200/65">
              {kpis.view_count !== null ? 'YouTube reach' : 'Caption blocks'}
            </div>
          </div>

          <div className="royal-subcard rounded-xl p-3">
            <div className="flex items-center justify-between text-[11px] text-blue-200/75 font-medium">
              <span>{kpis.like_count !== null ? 'Likes' : 'Vocab Variety'}</span>
              <ThumbsUp className="w-3.5 h-3.5 text-blue-300" />
            </div>
            <div className="mt-1 text-base sm:text-lg font-bold font-mono tabular-nums text-white">
              {kpis.like_count !== null
                ? formatCompactNumber(kpis.like_count)
                : `${kpis.lexical_richness_pct}%`}
            </div>
            <div className="text-[11px] text-blue-200/65">
              {kpis.like_count !== null ? 'Viewer approval' : 'Unique key terms'}
            </div>
          </div>

          <div className="royal-subcard rounded-xl p-3">
            <div className="flex items-center justify-between text-[11px] text-blue-200/75 font-medium">
              <span>{kpis.engagement_rate !== null ? 'Engagement' : 'Brief Read'}</span>
              <Clock className="w-3.5 h-3.5 text-blue-300" />
            </div>
            <div className="mt-1 text-base sm:text-lg font-bold font-mono tabular-nums text-white">
              {kpis.engagement_rate !== null ? `${kpis.engagement_rate}%` : `${kpis.brief_read_minutes}m`}
            </div>
            <div className="text-[11px] text-blue-200/65">
              {kpis.engagement_rate !== null ? 'Likes + comments' : 'Executive digest'}
            </div>
          </div>
        </div>

        {/* Collapsible Description */}
        {metadata.description && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setShowDesc((v) => !v)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-[#081533] hover:bg-[#0D1E47] border border-blue-300/15 text-xs text-blue-100/85 transition"
            >
              <span className="font-medium">Original Creator Description</span>
              {showDesc ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {showDesc && (
              <pre className="mt-2 p-3 rounded-lg bg-[#061027] border border-blue-300/15 text-xs text-blue-100/80 whitespace-pre-wrap font-sans max-h-40 overflow-y-auto leading-relaxed">
                {metadata.description}
              </pre>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
