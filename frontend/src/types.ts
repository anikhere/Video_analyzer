export interface VideoMetadata {
  id: string;
  title: string;
  channel: string;
  description: string;
  published_at: string;
  thumbnail: string | null;
  duration: string;
  duration_seconds: number;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  metadata_source?: string;
  url: string;
}

export interface TimestampItem {
  time: string;
  explanation: string;
}

export interface TermItem {
  term: string;
  explanation: string;
}

export interface RawChapterItem {
  start_time: string;
  title: string;
  summary: string;
}

export interface VideoAnalysis {
  tldr: string;
  content_type: string;
  summary: string;
  premise: string;
  core_breakdown: string;
  topics: string[];
  key_takeaways: string[];
  chapters: RawChapterItem[];
  timestamps: TimestampItem[];
  action_items: string[];
  audience: string;
  terminology: TermItem[];
  conclusion: string;
}

export interface DashboardKPIs {
  duration_seconds: number;
  duration_label: string;
  word_count: number;
  segment_count: number;
  avg_wpm: number;
  pace_category: string;
  brief_read_minutes: number;
  transcript_read_minutes: number;
  time_saved_minutes: number;
  time_saved_pct: number;
  lexical_richness_pct: number;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  engagement_rate: number | null;
}

export interface PacePoint {
  index: number;
  time: string;
  end_time: string;
  start_seconds: number;
  end_seconds: number;
  wpm: number;
  concept_hits: number;
  density: number;
  excerpt: string;
}

export interface EnrichedChapter {
  index: number;
  title: string;
  summary: string;
  start_time: string;
  end_time: string;
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
  duration_minutes: number;
  duration_label: string;
  share_pct: number;
  word_count: number;
  wpm: number;
}

export interface ConceptFrequencyItem {
  concept: string;
  full_concept: string;
  mentions: number;
  first_time: string;
  first_seconds: number;
  spread: 'Early' | 'Mid' | 'Late' | 'Throughout';
}

export interface MomentPin {
  index: number;
  time: string;
  seconds: number;
  position_pct: number;
  explanation: string;
  chapter: string;
}

export interface DashboardAnalytics {
  kpis: DashboardKPIs;
  pace_series: PacePoint[];
  chapters: EnrichedChapter[];
  concept_frequency: ConceptFrequencyItem[];
  moment_pins: MomentPin[];
}

export interface TranscriptSegment {
  start: number;
  duration: number;
  text: string;
  formatted_time: string;
}

export interface VideoTranscript {
  language: string;
  language_code: string;
  is_generated: boolean;
  segments: TranscriptSegment[];
}

export interface TelemetryInfo {
  elapsed_ms: number;
  cached: boolean;
  sample?: boolean;
  llm_calls: number;
  youtube_api_calls: number;
  provider: string;
  model: string;
}

export interface DashboardPayload {
  id?: string;
  label?: string;
  metadata: VideoMetadata;
  analysis: VideoAnalysis;
  analytics: DashboardAnalytics;
  transcript: VideoTranscript;
  telemetry: TelemetryInfo;
}

export interface SampleSummary {
  id: string;
  label: string;
  video_id: string;
  title: string;
  channel: string;
  duration: string;
  thumbnail: string | null;
}

export interface ServerConfig {
  provider: 'openrouter' | 'gemini';
  openrouter_model: string;
  gemini_model: string;
  has_openrouter_key: boolean;
  has_gemini_key: boolean;
  has_yt_key: boolean;
  zero_yt_key_supported: boolean;
}

export interface RuntimeSettings {
  provider: 'openrouter' | 'gemini';
  model: string;
  apiKey: string;
  ytKey: string;
}
