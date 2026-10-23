// Helpers for the Transparency page's measured numbers (GET /api/metrics).
import type { HeadlineMetric, Localized, MetricRecord } from '../api/models';

/** Text in the UI language, falling back to English. */
export const localized = (text: Localized | undefined, lang: string) => (text ? ((text as Record<string, string | undefined>)[lang] ?? text.en) : '');

/** Format a headline value: percent = value × 100 %, score = 2 decimals, messages/count = whole numbers. */
export function formatMetric(value: number | null | undefined, format: HeadlineMetric['format']): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  switch (format) {
    case 'percent': {
      const pct = value * 100;
      return `${Number.isInteger(Math.round(pct * 10) / 10) ? Math.round(pct) : pct.toFixed(1)}%`;
    }
    case 'score':
      return value.toFixed(2);
    default:
      return Math.round(value).toLocaleString('en-US');
  }
}

/** Only measured headlines are shown; new ones appear automatically as lanes report them. */
export const measuredHeadlines = (items: HeadlineMetric[] | undefined) => (items ?? []).filter((h) => h.found && h.value !== null);

/** Records matching a search across lane, metric, split and notes (case-insensitive), grouped by lane. */
export function groupRecords(records: MetricRecord[], query = ''): [string, MetricRecord[]][] {
  const q = query.trim().toLowerCase();
  const groups = new Map<string, MetricRecord[]>();
  for (const r of records) {
    const haystack = `${r.lane} ${r.metric} ${r.split ?? ''} ${r.notes ?? ''}`.toLowerCase();
    if (q && !haystack.includes(q)) continue;
    groups.set(r.lane, [...(groups.get(r.lane) ?? []), r]);
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}
