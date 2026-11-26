import React, { useState } from 'react';
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Activity, BarChart3, Hash, PieChart as PieIcon } from 'lucide-react';
import { DashboardAnalytics } from '../types';

interface Props {
  analytics: DashboardAnalytics;
  onSeek: (seconds: number) => void;
  onFilterTranscript: (query: string) => void;
}

const ROYAL_PALETTE = ['#2563EB', '#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE', '#FFFFFF', '#1D4ED8', '#38BDF8'];

const PaceTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const pt = payload[0].payload;
  return (
    <div className="max-w-xs rounded-xl bg-[#07132E]/98 border border-white/25 p-3.5 shadow-2xl text-xs">
      <div className="flex items-center justify-between gap-3 mb-1.5">
        <span className="px-2 py-0.5 rounded bg-white text-[#07132E] font-mono font-bold tabular-nums">
          {pt.time} – {pt.end_time}
        </span>
        <span className="text-blue-200 font-medium">Click point to seek</span>
      </div>
      <div className="grid grid-cols-2 gap-2 my-2 pt-2 border-t border-blue-300/20">
        <div>
          <div className="text-[11px] text-blue-200/75">Speaking Pace</div>
          <div className="text-sm font-bold font-mono text-white tabular-nums">{pt.wpm} WPM</div>
        </div>
        <div>
          <div className="text-[11px] text-blue-200/75">Info Density</div>
          <div className="text-sm font-bold font-mono text-blue-300 tabular-nums">{pt.density} / 100</div>
        </div>
      </div>
      <p className="text-[11px] text-blue-100/85 italic leading-relaxed border-t border-blue-300/15 pt-2">
        &ldquo;{pt.excerpt}&rdquo;
      </p>
    </div>
  );
};

const ChapterTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const ch = payload[0].payload;
  return (
    <div className="max-w-xs rounded-xl bg-[#07132E]/98 border border-white/25 p-3 shadow-2xl text-xs">
      <div className="font-bold text-white mb-1">
        {ch.index}. {ch.title}
      </div>
      <div className="font-mono text-blue-200 tabular-nums mb-1.5">
        {ch.start_time} – {ch.end_time} · {ch.duration_label} ({ch.share_pct}%)
      </div>
      <div className="text-[11px] text-blue-100/85">{ch.summary}</div>
    </div>
  );
};

const ConceptTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0].payload;
  return (
    <div className="rounded-xl bg-[#07132E]/98 border border-white/25 p-3 shadow-2xl text-xs">
      <div className="font-bold text-white">{item.full_concept}</div>
      <div className="mt-1 font-mono text-blue-200 tabular-nums">
        {item.mentions} verified mentions · First @ {item.first_time}
      </div>
      <div className="mt-1 text-[11px] text-blue-100/80">
        Distribution: <span className="font-semibold text-white">{item.spread}</span> · Click to seek &amp; search
      </div>
    </div>
  );
};

export const AnalyticsCharts: React.FC<Props> = ({ analytics, onSeek, onFilterTranscript }) => {
  const [allocView, setAllocView] = useState<'donut' | 'bars'>('donut');
  const { pace_series, chapters, concept_frequency, kpis } = analytics;

  return (
    <div className="space-y-6">
      {/* Top 2 Graphs Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Graph 1: Speaking Pace & Information Density Curve (7 cols) */}
        <section className="lg:col-span-7 royal-card rounded-2xl p-5 sm:p-6 flex flex-col">
          <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-300" />
                <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  Speaking Pace &amp; Information Density Over Time
                </h3>
              </div>
              <p className="text-xs text-blue-200/80 mt-0.5">
                Words per minute (Royal Blue area) vs. concept density index (Crisp White line). Click any point to jump video.
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="inline-flex items-center gap-1.5 text-blue-100">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#3B82F6]" />
                Pace (WPM)
              </span>
              <span className="inline-flex items-center gap-1.5 text-white font-medium">
                <span className="w-3 h-0.5 bg-white rounded" />
                Info Density
              </span>
            </div>
          </div>

          <div className="h-[270px] w-full mt-auto">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={pace_series}
                margin={{ top: 10, right: 12, left: -14, bottom: 0 }}
                onClick={(state: any) => {
                  if (state && state.activePayload && state.activePayload[0]) {
                    onSeek(state.activePayload[0].payload.start_seconds);
                  }
                }}
              >
                <defs>
                  <linearGradient id="royalPaceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.62} />
                    <stop offset="95%" stopColor="#1D4ED8" stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(147, 197, 253, 0.12)" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="#93C5FD"
                  tick={{ fill: '#DBEAFE', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(147, 197, 253, 0.2)' }}
                />
                <YAxis
                  yAxisId="wpm"
                  stroke="#93C5FD"
                  tick={{ fill: '#DBEAFE', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis yAxisId="density" orientation="right" domain={[0, 100]} hide />
                <Tooltip content={<PaceTooltip />} cursor={{ stroke: '#FFFFFF', strokeOpacity: 0.35, strokeWidth: 1 }} />
                {kpis.avg_wpm > 0 && (
                  <ReferenceLine
                    yAxisId="wpm"
                    y={kpis.avg_wpm}
                    stroke="#93C5FD"
                    strokeDasharray="4 4"
                    strokeOpacity={0.65}
                    label={{
                      value: `Avg ${kpis.avg_wpm} WPM`,
                      position: 'insideTopRight',
                      fill: '#DBEAFE',
                      fontSize: 10,
                    }}
                  />
                )}
                <Area
                  yAxisId="wpm"
                  type="monotone"
                  dataKey="wpm"
                  stroke="#3B82F6"
                  strokeWidth={2.5}
                  fill="url(#royalPaceGrad)"
                  activeDot={{ r: 5, fill: '#FFFFFF', stroke: '#2563EB', strokeWidth: 2 }}
                />
                <Line
                  yAxisId="density"
                  type="monotone"
                  dataKey="density"
                  stroke="#FFFFFF"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#FFFFFF' }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Graph 2: Chapter & Topic Time Allocation (5 cols) */}
        <section className="lg:col-span-5 royal-card rounded-2xl p-5 sm:p-6 flex flex-col">
          <div className="flex items-start justify-between gap-2 mb-3">
            <div>
              <div className="flex items-center gap-2">
                <PieIcon className="w-4 h-4 text-blue-300" />
                <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  Topic &amp; Chapter Time Share
                </h3>
              </div>
              <p className="text-xs text-blue-200/80 mt-0.5">
                Where video duration is actually spent. Click slice to jump.
              </p>
            </div>

            <div className="inline-flex rounded-lg bg-[#07122B] p-0.5 border border-blue-300/15 text-[11px]">
              <button
                type="button"
                onClick={() => setAllocView('donut')}
                className={`px-2 py-1 rounded font-semibold transition ${
                  allocView === 'donut' ? 'bg-white text-[#07132E]' : 'text-blue-200/75 hover:text-white'
                }`}
              >
                Donut
              </button>
              <button
                type="button"
                onClick={() => setAllocView('bars')}
                className={`px-2 py-1 rounded font-semibold transition ${
                  allocView === 'bars' ? 'bg-white text-[#07132E]' : 'text-blue-200/75 hover:text-white'
                }`}
              >
                Bars
              </button>
            </div>
          </div>

          {allocView === 'donut' ? (
            <div className="flex-1 flex flex-col sm:flex-row items-center gap-4">
              <div className="h-[200px] w-[200px] shrink-0 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chapters}
                      dataKey="duration_seconds"
                      nameKey="title"
                      innerRadius={56}
                      outerRadius={86}
                      paddingAngle={2.5}
                      stroke="#081430"
                      strokeWidth={2}
                      onClick={(entry: any) => {
                        if (entry && typeof entry.start_seconds === 'number') {
                          onSeek(entry.start_seconds);
                        }
                      }}
                      className="cursor-pointer"
                    >
                      {chapters.map((_, idx) => (
                        <Cell key={idx} fill={ROYAL_PALETTE[idx % ROYAL_PALETTE.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChapterTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-[10px] uppercase tracking-wider text-blue-200/80 font-semibold">Total</span>
                  <span className="text-sm font-bold font-mono text-white tabular-nums">{kpis.duration_label}</span>
                </div>
              </div>

              <div className="flex-1 w-full space-y-2 max-h-[215px] overflow-y-auto pr-1">
                {chapters.map((ch, idx) => (
                  <button
                    key={ch.index}
                    type="button"
                    onClick={() => onSeek(ch.start_seconds)}
                    className="w-full text-left flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg hover:bg-white/10 transition text-xs"
                  >
                    <span className="flex items-center gap-2 min-w-0">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: ROYAL_PALETTE[idx % ROYAL_PALETTE.length] }}
                      />
                      <span className="truncate text-blue-50 font-medium">{ch.title}</span>
                    </span>
                    <span className="font-mono text-white font-semibold tabular-nums shrink-0">
                      {ch.share_pct}%
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-[235px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chapters}
                  layout="vertical"
                  margin={{ top: 4, right: 16, left: 6, bottom: 4 }}
                  onClick={(state: any) => {
                    if (state?.activePayload?.[0]) {
                      onSeek(state.activePayload[0].payload.start_seconds);
                    }
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(147, 197, 253, 0.12)" horizontal={false} />
                  <XAxis
                    type="number"
                    unit="%"
                    tick={{ fill: '#DBEAFE', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="index"
                    tickFormatter={(v) => `Ch ${v}`}
                    width={46}
                    tick={{ fill: '#FFFFFF', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<ChapterTooltip />} cursor={{ fill: 'rgba(255,255,255,0.06)' }} />
                  <Bar dataKey="share_pct" radius={[0, 6, 6, 0]} className="cursor-pointer">
                    {chapters.map((_, idx) => (
                      <Cell key={idx} fill={ROYAL_PALETTE[idx % ROYAL_PALETTE.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      </div>

      {/* Graph 3: Grounded Concept & Term Mention Frequency */}
      {concept_frequency.length > 0 && (
        <section className="royal-card rounded-2xl p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-300" />
                <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  Verified Concept &amp; Term Prominence in Transcript
                </h3>
              </div>
              <p className="text-xs text-blue-200/80 mt-0.5">
                Exact mention counts computed directly from the spoken transcript. Click any concept bar to seek its first mention and filter the transcript.
              </p>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-[#102452] text-blue-100 border border-blue-300/20">
              <Hash className="w-3 h-3 text-blue-300" />
              0 Extra LLM Calls · Deterministic Count
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-center">
            <div className="lg:col-span-8 h-[230px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={concept_frequency}
                  layout="vertical"
                  margin={{ top: 4, right: 20, left: 8, bottom: 4 }}
                  onClick={(state: any) => {
                    if (state?.activePayload?.[0]) {
                      const item = state.activePayload[0].payload;
                      onSeek(item.first_seconds);
                      onFilterTranscript(item.full_concept);
                    }
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(147, 197, 253, 0.12)" horizontal={false} />
                  <XAxis
                    type="number"
                    allowDecimals={false}
                    tick={{ fill: '#DBEAFE', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="concept"
                    width={150}
                    tick={{ fill: '#FFFFFF', fontSize: 12, fontWeight: 600 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<ConceptTooltip />} cursor={{ fill: 'rgba(255,255,255,0.06)' }} />
                  <Bar dataKey="mentions" radius={[0, 6, 6, 0]} className="cursor-pointer">
                    {concept_frequency.map((_, idx) => (
                      <Cell key={idx} fill={idx === 0 ? '#FFFFFF' : idx < 3 ? '#60A5FA' : '#2563EB'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="lg:col-span-4 space-y-2">
              {concept_frequency.slice(0, 5).map((c, idx) => (
                <button
                  key={c.full_concept}
                  type="button"
                  onClick={() => {
                    onSeek(c.first_seconds);
                    onFilterTranscript(c.full_concept);
                  }}
                  className="w-full royal-subcard hover:bg-[#16306E] rounded-xl px-3.5 py-2.5 flex items-center justify-between gap-2 text-left transition"
                >
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-white truncate">
                      {idx + 1}. {c.full_concept}
                    </div>
                    <div className="text-[11px] text-blue-200/75 font-mono tabular-nums">
                      First @ {c.first_time} · {c.spread}
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-md bg-white/10 text-white font-mono text-xs font-bold tabular-nums shrink-0">
                    {c.mentions}×
                  </span>
                </button>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
