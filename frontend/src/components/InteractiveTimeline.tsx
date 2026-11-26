import React, { useState } from 'react';
import { Clock, ExternalLink, ListOrdered, Milestone, Play } from 'lucide-react';
import { EnrichedChapter, MomentPin } from '../types';

interface Props {
  chapters: EnrichedChapter[];
  moments: MomentPin[];
  videoUrl: string;
  durationLabel: string;
  onSeek: (seconds: number) => void;
}

const SEGMENT_PALETTE = [
  'bg-[#1D4ED8] hover:bg-[#2563EB] text-white',
  'bg-[#2563EB] hover:bg-[#3B82F6] text-white',
  'bg-[#3B82F6] hover:bg-[#60A5FA] text-white',
  'bg-[#1E40AF] hover:bg-[#1D4ED8] text-white',
  'bg-[#60A5FA] hover:bg-[#93C5FD] text-[#050C1E]',
  'bg-[#DBEAFE] hover:bg-white text-[#050C1E]',
];

export const InteractiveTimeline: React.FC<Props> = ({
  chapters,
  moments,
  videoUrl,
  durationLabel,
  onSeek,
}) => {
  const [activeTab, setActiveTab] = useState<'moments' | 'chapters'>('moments');
  const [hoveredChapter, setHoveredChapter] = useState<EnrichedChapter | null>(chapters[0] || null);

  const selectedChapter = hoveredChapter || chapters[0] || null;

  return (
    <section className="royal-card rounded-2xl p-5 sm:p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Milestone className="w-4 h-4 text-blue-300" />
            <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
              Interactive Video Architecture &amp; Important Moments
            </h3>
          </div>
          <p className="text-xs text-blue-200/80 mt-0.5">
            Proportional chapter timeline (00:00 → {durationLabel}). Click any block or timestamp pin to jump the video player.
          </p>
        </div>

        <div className="inline-flex rounded-xl bg-[#07122B] p-1 border border-blue-300/15 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('moments')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition flex items-center gap-1.5 ${
              activeTab === 'moments'
                ? 'bg-white text-[#07132E] shadow'
                : 'text-blue-200/80 hover:text-white'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            Important Moments ({moments.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('chapters')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition flex items-center gap-1.5 ${
              activeTab === 'chapters'
                ? 'bg-white text-[#07132E] shadow'
                : 'text-blue-200/80 hover:text-white'
            }`}
          >
            <ListOrdered className="w-3.5 h-3.5" />
            Chapters ({chapters.length})
          </button>
        </div>
      </div>

      {/* Proportional Segmented Gantt Bar */}
      {chapters.length > 0 && (
        <div className="mb-5">
          <div className="flex w-full h-10 rounded-xl overflow-hidden border border-white/20 p-0.5 bg-[#061026] gap-0.5">
            {chapters.map((ch, idx) => {
              const colorCls = SEGMENT_PALETTE[idx % SEGMENT_PALETTE.length];
              return (
                <button
                  key={`${ch.start_time}-${ch.index}`}
                  type="button"
                  style={{ width: `${Math.max(4, ch.share_pct)}%` }}
                  onMouseEnter={() => setHoveredChapter(ch)}
                  onFocus={() => setHoveredChapter(ch)}
                  onClick={() => onSeek(ch.start_seconds)}
                  title={`${ch.start_time} – ${ch.title} (${ch.share_pct}%)`}
                  className={`${colorCls} relative h-full rounded-lg px-2 flex items-center justify-between text-xs font-semibold transition-all overflow-hidden group`}
                >
                  <span className="truncate">
                    {ch.share_pct >= 11 ? `${ch.index}. ${ch.title}` : ch.index}
                  </span>
                  {ch.share_pct >= 16 && (
                    <span className="font-mono text-[11px] opacity-85 ml-1 shrink-0 tabular-nums">
                      {ch.share_pct}%
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Moment Pins Track Along 0% - 100% */}
          {moments.length > 0 && (
            <div className="relative h-7 mt-1.5 select-none">
              <div className="absolute inset-x-0 top-3 h-px bg-blue-300/20" />
              {moments.map((m) => (
                <button
                  key={`${m.time}-${m.index}`}
                  type="button"
                  style={{ left: `${m.position_pct}%` }}
                  onClick={() => onSeek(m.seconds)}
                  title={`[${m.time}] ${m.explanation}`}
                  className="-translate-x-1/2 absolute top-1 group flex flex-col items-center"
                >
                  <span className="w-3.5 h-3.5 rounded-full bg-white border-2 border-[#2563EB] shadow group-hover:scale-125 transition" />
                </button>
              ))}
            </div>
          )}

          {/* Active / Hovered Chapter Inspector Strip */}
          {selectedChapter && (
            <div className="mt-2 rounded-xl bg-[#0F2352]/85 border border-blue-300/20 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-white text-[#07132E] font-mono font-bold tabular-nums">
                    {selectedChapter.start_time} – {selectedChapter.end_time}
                  </span>
                  <span className="font-bold text-white">{selectedChapter.title}</span>
                  <span className="text-blue-200/80 font-mono text-[11px] tabular-nums">
                    ({selectedChapter.duration_label} · {selectedChapter.share_pct}% of video · {selectedChapter.wpm} WPM)
                  </span>
                </div>
                <p className="text-xs text-blue-100/85 mt-1 leading-relaxed">{selectedChapter.summary}</p>
              </div>
              <button
                type="button"
                onClick={() => onSeek(selectedChapter.start_seconds)}
                className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                Jump to {selectedChapter.start_time}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tabbed Moment Cards / Chapter Cards */}
      {activeTab === 'moments' ? (
        moments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {moments.map((m) => (
              <div
                key={`${m.time}-${m.index}`}
                className="royal-subcard hover:bg-[#152E69] hover:border-blue-300/35 rounded-xl p-3.5 transition flex items-start gap-3 group"
              >
                <button
                  type="button"
                  onClick={() => onSeek(m.seconds)}
                  className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white text-[#07132E] group-hover:bg-blue-100 font-mono text-xs font-bold tabular-nums shadow-sm transition"
                  title="Jump embedded video player to this timestamp"
                >
                  <Play className="w-3 h-3 fill-current" />
                  {m.time}
                </button>
                <div className="min-w-0 flex-1">
                  <p className="text-xs sm:text-sm text-white/95 leading-relaxed">{m.explanation}</p>
                  <div className="mt-1.5 flex items-center justify-between text-[11px] text-blue-200/70">
                    <span className="truncate">{m.chapter}</span>
                    <a
                      href={`${videoUrl}&t=${m.seconds}s`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-blue-200 hover:text-white shrink-0 ml-2"
                    >
                      YouTube link
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-blue-200/70">No specific verified timestamps were identified in the transcript.</p>
        )
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {chapters.map((ch) => (
            <div
              key={`${ch.start_time}-${ch.index}`}
              onClick={() => onSeek(ch.start_seconds)}
              className="cursor-pointer royal-subcard hover:bg-[#152E69] hover:border-blue-300/35 rounded-xl p-3.5 transition"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-6 h-6 rounded-md bg-blue-600 text-white font-mono text-xs font-bold grid place-items-center shrink-0">
                    {String(ch.index).padStart(2, '0')}
                  </span>
                  <h4 className="text-sm font-bold text-white truncate">{ch.title}</h4>
                </div>
                <span className="font-mono text-xs font-semibold text-blue-200 tabular-nums shrink-0">
                  {ch.start_time} · {ch.duration_label}
                </span>
              </div>
              <p className="mt-2 text-xs text-blue-100/85 leading-relaxed">{ch.summary}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
