import React, { useState } from 'react';
import { BookOpen, Check, Compass, Copy, Layers, Sparkles, Target } from 'lucide-react';
import { DashboardKPIs, VideoAnalysis } from '../types';

interface Props {
  analysis: VideoAnalysis;
  kpis: DashboardKPIs;
}

export const ExecutiveSummaryCard: React.FC<Props> = ({ analysis, kpis }) => {
  const [copied, setCopied] = useState(false);

  const handleCopySummary = () => {
    const text = `TL;DR: ${analysis.tldr}\n\nSummary:\n${analysis.summary}\n\nBottom Line:\n${analysis.conclusion}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="royal-card rounded-2xl p-5 sm:p-7 flex flex-col justify-between h-full">
      <div>
        {/* Executive Header Row */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-blue-600 text-white shadow-sm">
              <Sparkles className="w-3.5 h-3.5" />
              Executive Brief · What This Video Is All About
            </span>
            {analysis.content_type && (
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-white/10 text-white border border-white/20">
                {analysis.content_type}
              </span>
            )}
            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-[#102452] text-blue-100 border border-blue-300/20">
              {kpis.brief_read_minutes} min read · Saves {kpis.time_saved_minutes} min
            </span>
          </div>

          <button
            type="button"
            onClick={handleCopySummary}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/15 text-white border border-white/15 transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied Brief' : 'Copy Summary'}
          </button>
        </div>

        {/* Core Thesis Callout (Royal Blue & Crisp White Contrast) */}
        <div className="rounded-xl bg-gradient-to-r from-[#132C66] via-[#102556] to-[#0D1E47] border border-blue-300/25 border-l-4 border-l-white p-4 sm:p-5 shadow-md">
          <div className="text-[11px] font-bold uppercase tracking-widest text-blue-200 mb-1.5">
            Core Thesis (In Plain English)
          </div>
          <p className="text-base sm:text-lg font-bold text-white leading-relaxed">
            {analysis.tldr || analysis.summary}
          </p>
        </div>

        {/* Main Narrative Overview */}
        <div className="mt-5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-200/90 mb-2">
            <BookOpen className="w-4 h-4 text-blue-300" />
            Complete Video Overview
          </div>
          <p className="text-sm sm:text-[15px] text-blue-50/95 leading-[1.75]">
            {analysis.summary}
          </p>
        </div>
      </div>

      {/* 3-Pillar Structured Synthesis */}
      <div className="mt-6 pt-5 border-t border-blue-300/15 grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <div className="royal-subcard rounded-xl p-4 flex flex-col">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white mb-2">
            <span className="w-6 h-6 rounded-md bg-blue-600/40 border border-blue-300/30 grid place-items-center">
              <Compass className="w-3.5 h-3.5 text-white" />
            </span>
            Why It Matters
          </div>
          <p className="text-xs sm:text-[13px] text-blue-100/90 leading-relaxed">
            {analysis.premise || 'Establishes the foundational context and motivation addressed in the video.'}
          </p>
        </div>

        <div className="royal-subcard rounded-xl p-4 flex flex-col">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white mb-2">
            <span className="w-6 h-6 rounded-md bg-blue-600/40 border border-blue-300/30 grid place-items-center">
              <Layers className="w-3.5 h-3.5 text-white" />
            </span>
            How It&apos;s Covered
          </div>
          <p className="text-xs sm:text-[13px] text-blue-100/90 leading-relaxed">
            {analysis.core_breakdown || 'Walks chronologically through the core concepts, evidence, and examples.'}
          </p>
        </div>

        <div className="rounded-xl p-4 flex flex-col bg-gradient-to-b from-white/[0.11] to-white/[0.04] border border-white/25">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white mb-2">
            <span className="w-6 h-6 rounded-md bg-white text-[#081430] grid place-items-center">
              <Target className="w-3.5 h-3.5" />
            </span>
            Bottom-Line Verdict
          </div>
          <p className="text-xs sm:text-[13px] text-white/95 leading-relaxed font-medium">
            {analysis.conclusion}
          </p>
        </div>
      </div>
    </section>
  );
};
