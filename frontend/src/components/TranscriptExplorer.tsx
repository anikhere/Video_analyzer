import React, { useEffect, useMemo, useState } from 'react';
import {
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  FileSearch,
  Play,
  Search,
  X,
} from 'lucide-react';
import { EnrichedChapter, VideoTranscript } from '../types';

interface Props {
  transcript: VideoTranscript;
  chapters: EnrichedChapter[];
  externalQuery: string;
  externalNonce: number;
  onSeek: (seconds: number) => void;
}

function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function HighlightedText({ text, query }: { text: string; query: string }) {
  const clean = query.trim();
  if (!clean) return <>{text}</>;
  const regex = new RegExp(`(${escapeRegExp(clean)})`, 'gi');
  const parts = text.split(regex);
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === clean.toLowerCase() ? (
          <mark
            key={i}
            className="bg-white text-[#07132E] font-semibold px-1 rounded-sm"
          >
            {part}
          </mark>
        ) : (
          <React.Fragment key={i}>{part}</React.Fragment>
        )
      )}
    </>
  );
}

export const TranscriptExplorer: React.FC<Props> = ({
  transcript,
  chapters,
  externalQuery,
  externalNonce,
  onSeek,
}) => {
  const [expanded, setExpanded] = useState(true);
  const [query, setQuery] = useState('');
  const [chapterIdx, setChapterIdx] = useState<number | 'all'>('all');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (externalNonce > 0) {
      setQuery(externalQuery);
      setChapterIdx('all');
      setExpanded(true);
    }
  }, [externalQuery, externalNonce]);

  const filteredSegments = useMemo(() => {
    const q = query.trim().toLowerCase();
    const selectedChap =
      chapterIdx === 'all' ? null : chapters.find((c) => c.index === chapterIdx) || null;

    return transcript.segments.filter((seg) => {
      if (selectedChap) {
        if (seg.start < selectedChap.start_seconds || seg.start >= selectedChap.end_seconds) {
          return false;
        }
      }
      if (q && !seg.text.toLowerCase().includes(q) && !seg.formatted_time.includes(q)) {
        return false;
      }
      return true;
    });
  }, [transcript.segments, query, chapterIdx, chapters]);

  const handleCopyAll = () => {
    const fullText = filteredSegments
      .map((s) => `[${s.formatted_time}] ${s.text}`)
      .join('\n');
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="transcript-explorer" className="royal-card rounded-2xl p-5 sm:p-6">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <FileSearch className="w-4 h-4 text-blue-300" />
            <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
              Searchable Source Transcript
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-white/10 text-white tabular-nums">
              {filteredSegments.length} / {transcript.segments.length} lines
            </span>
          </div>
          <p className="text-xs text-blue-200/80 mt-0.5">
            {transcript.language} ({transcript.is_generated ? 'Auto-generated' : 'Provided'} captions) · Click any timestamp to sync video playback.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopyAll}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#102452] hover:bg-[#173270] text-white border border-blue-300/20 transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied' : 'Copy Lines'}
          </button>

          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-white text-[#07132E] hover:bg-blue-50 transition shadow-sm"
          >
            {expanded ? (
              <>
                Collapse
                <ChevronUp className="w-3.5 h-3.5" />
              </>
            ) : (
              <>
                Expand Transcript
                <ChevronDown className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-blue-300/15">
          {/* Search & Chapter Filter Bar */}
          <div className="flex flex-col md:flex-row gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-blue-300 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search words, quotes, concepts, or timestamps (e.g. 05:15)..."
                className="w-full pl-10 pr-9 py-2.5 rounded-xl bg-[#07122B] border border-blue-300/25 focus:border-white focus:outline-none text-sm text-white placeholder-blue-200/50"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-200 hover:text-white"
                  aria-label="Clear transcript search"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {chapters.length > 1 && (
              <select
                value={chapterIdx}
                onChange={(e) =>
                  setChapterIdx(e.target.value === 'all' ? 'all' : Number(e.target.value))
                }
                aria-label="Filter transcript by chapter"
                className="px-3.5 py-2.5 rounded-xl bg-[#07122B] border border-blue-300/25 text-xs sm:text-sm text-white focus:border-white focus:outline-none"
              >
                <option value="all">All Chapters ({transcript.segments.length} lines)</option>
                {chapters.map((ch) => (
                  <option key={ch.index} value={ch.index}>
                    Ch {ch.index}: {ch.title} ({ch.start_time})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Scrollable Transcript List */}
          {filteredSegments.length > 0 ? (
            <div className="max-h-[420px] overflow-y-auto pr-1 space-y-1.5">
              {filteredSegments.map((seg, idx) => (
                <div
                  key={`${seg.start}-${idx}`}
                  className="group flex items-start gap-3 px-3 py-2.5 rounded-xl bg-[#091738]/75 hover:bg-[#11285C] border border-transparent hover:border-blue-300/25 transition"
                >
                  <button
                    type="button"
                    onClick={() => onSeek(Math.floor(seg.start))}
                    className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#122B63] group-hover:bg-white text-blue-100 group-hover:text-[#07132E] font-mono text-xs font-bold tabular-nums transition"
                    title="Jump video player to this line"
                  >
                    <Play className="w-2.5 h-2.5 fill-current" />
                    {seg.formatted_time}
                  </button>
                  <p className="text-xs sm:text-sm text-blue-50/95 leading-relaxed">
                    <HighlightedText text={seg.text} query={query} />
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-10 text-center rounded-xl bg-[#07122B]/80 border border-blue-300/15">
              <p className="text-sm text-white font-semibold">No matching transcript lines</p>
              <p className="text-xs text-blue-200/75 mt-1">
                Try clearing the search query or selecting &ldquo;All Chapters&rdquo;.
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
