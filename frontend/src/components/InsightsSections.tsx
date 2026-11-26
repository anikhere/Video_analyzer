import React, { useState } from 'react';
import {
  BookMarked,
  CheckSquare,
  Lightbulb,
  Search,
  Square,
  Tag,
  Users,
} from 'lucide-react';
import { VideoAnalysis } from '../types';

interface Props {
  analysis: VideoAnalysis;
  onFilterTranscript: (query: string) => void;
}

export const InsightsSections: React.FC<Props> = ({ analysis, onFilterTranscript }) => {
  const [checkedItems, setCheckedItems] = useState<Record<number, boolean>>({});

  const toggleItem = (idx: number) => {
    setCheckedItems((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const completedCount = Object.values(checkedItems).filter(Boolean).length;

  return (
    <div className="space-y-6">
      {/* Row A: Key Takeaways (7 cols) + Topics & Audience (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Key Takeaways */}
        <section className="lg:col-span-7 royal-card rounded-2xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-blue-300" />
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Key Takeaways
              </h3>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-white/10 text-white tabular-nums">
              {analysis.key_takeaways.length} insights
            </span>
          </div>

          {analysis.key_takeaways.length > 0 ? (
            <div className="space-y-3">
              {analysis.key_takeaways.map((point, idx) => (
                <div
                  key={idx}
                  className="royal-subcard rounded-xl p-4 flex items-start gap-3.5 hover:border-blue-300/35 transition"
                >
                  <span className="w-7 h-7 rounded-lg bg-white text-[#07132E] font-mono text-xs font-extrabold grid place-items-center shrink-0 mt-0.5 shadow-sm">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <p className="text-sm text-white/95 leading-relaxed">{point}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-blue-200/75">No explicit takeaways were identified in the transcript.</p>
          )}
        </section>

        {/* Topics + Audience */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* Core Topics */}
          <section className="royal-card rounded-2xl p-5 sm:p-6 flex-1">
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-blue-300" />
                <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  Topics &amp; Core Themes
                </h3>
              </div>
              <span className="text-[11px] text-blue-200/75">Click pill to search transcript</span>
            </div>

            {analysis.topics.length > 0 ? (
              <div className="flex flex-wrap gap-2 mt-3">
                {analysis.topics.map((topic, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onFilterTranscript(topic)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition inline-flex items-center gap-1.5 ${
                      idx === 0
                        ? 'bg-white text-[#07132E] hover:bg-blue-50 shadow-sm'
                        : 'bg-[#12295E] hover:bg-[#19387E] text-white border border-blue-300/25'
                    }`}
                  >
                    <span>{topic}</span>
                    <Search className="w-3 h-3 opacity-70" />
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-xs text-blue-200/75">No distinct topics listed.</p>
            )}
          </section>

          {/* Intended Audience */}
          <section className="royal-card rounded-2xl p-5 sm:p-6">
            <div className="flex items-center gap-2 mb-2.5">
              <Users className="w-4 h-4 text-blue-300" />
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Intended Audience · Who Should Watch
              </h3>
            </div>
            <div className="royal-subcard rounded-xl p-4 border-l-4 border-l-blue-400">
              <p className="text-sm text-blue-50/95 leading-relaxed">{analysis.audience}</p>
            </div>
          </section>
        </div>
      </div>

      {/* Row B: Action Items (5 cols) + Terminology Glossary (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Action Items */}
        <section className="lg:col-span-5 royal-card rounded-2xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-blue-300" />
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Action Items &amp; Next Steps
              </h3>
            </div>
            {analysis.action_items.length > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-blue-600/35 border border-blue-400/30 text-white tabular-nums">
                {completedCount}/{analysis.action_items.length} done
              </span>
            )}
          </div>

          {analysis.action_items.length > 0 ? (
            <div className="space-y-2.5">
              {analysis.action_items.map((item, idx) => {
                const isDone = !!checkedItems[idx];
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => toggleItem(idx)}
                    className={`w-full text-left rounded-xl p-3.5 border transition flex items-start gap-3 ${
                      isDone
                        ? 'bg-blue-950/60 border-blue-400/20 opacity-70'
                        : 'royal-subcard hover:bg-[#152F6B] border-blue-300/20'
                    }`}
                  >
                    {isDone ? (
                      <CheckSquare className="w-4 h-4 text-white shrink-0 mt-0.5" />
                    ) : (
                      <Square className="w-4 h-4 text-blue-300 shrink-0 mt-0.5" />
                    )}
                    <span className={`text-xs sm:text-sm leading-relaxed ${isDone ? 'line-through text-blue-200/70' : 'text-white'}`}>
                      {item}
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-blue-200/75">
              No explicit action items were stated in the video transcript.
            </p>
          )}
        </section>

        {/* Terminology Explained */}
        <section className="lg:col-span-7 royal-card rounded-2xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2">
              <BookMarked className="w-4 h-4 text-blue-300" />
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Terminology &amp; Concepts Explained
              </h3>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-white/10 text-white tabular-nums">
              {analysis.terminology.length} terms
            </span>
          </div>

          {analysis.terminology.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {analysis.terminology.map((t, idx) => (
                <div
                  key={idx}
                  className="royal-subcard rounded-xl p-4 flex flex-col justify-between hover:border-blue-300/35 transition"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <h4 className="text-sm font-bold text-white">{t.term}</h4>
                      <button
                        type="button"
                        onClick={() => onFilterTranscript(t.term)}
                        className="text-[11px] text-blue-200 hover:text-white inline-flex items-center gap-1 shrink-0"
                        title="Locate term in transcript"
                      >
                        <Search className="w-3 h-3" />
                        Find
                      </button>
                    </div>
                    <p className="text-xs text-blue-100/90 leading-relaxed">{t.explanation}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-blue-200/75">No specialized terminology was extracted from this video.</p>
          )}
        </section>
      </div>
    </div>
  );
};
