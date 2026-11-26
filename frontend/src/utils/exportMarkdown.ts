import { DashboardPayload } from '../types';

export function buildMarkdownReport(data: DashboardPayload): string {
  const { metadata, analysis, analytics } = data;
  const k = analytics.kpis;
  const lines: string[] = [
    `# ${metadata.title}`,
    `**Channel:** ${metadata.channel}  |  **Duration:** ${k.duration_label}  |  **Format:** ${analysis.content_type}`,
    `**URL:** ${metadata.url}`,
    '',
    '## Executive Thesis (What This Video Is All About)',
    `> ${analysis.tldr}`,
    '',
    '## Executive Summary',
    analysis.summary,
    '',
    `- **Premise / Context:** ${analysis.premise}`,
    `- **Core Walkthrough:** ${analysis.core_breakdown}`,
    `- **Bottom-Line Conclusion:** ${analysis.conclusion}`,
    '',
    '## Key Takeaways',
    ...analysis.key_takeaways.map((t, i) => `${i + 1}. ${t}`),
    '',
    '## Chapter Breakdown',
    ...analytics.chapters.map(
      (c) => `- **[${c.start_time} – ${c.end_time}] ${c.title}** (${c.duration_label}, ${c.share_pct}%): ${c.summary}`
    ),
    '',
    '## Important Moments',
    ...analytics.moment_pins.map(
      (m) => `- **[${m.time}](${metadata.url}&t=${m.seconds}s)** — ${m.explanation}`
    ),
    '',
    '## Action Items',
    ...(analysis.action_items.length
      ? analysis.action_items.map((a) => `- [ ] ${a}`)
      : ['- None explicitly stated in the transcript.']),
    '',
    '## Intended Audience',
    analysis.audience,
    '',
    '## Terminology Explained',
    ...analysis.terminology.map((t) => `- **${t.term}**: ${t.explanation}`),
    '',
  ];
  return lines.join('\n');
}
