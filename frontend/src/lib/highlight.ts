/**
 * Turns a message plus the critic's highlight spans (character offsets) into plain/highlighted
 * segments for rendering. Overlapping or out-of-range spans are handled: the earlier/stronger span
 * wins and nothing is ever dropped or duplicated from the original text.
 *
 * Highlight.delta is a log-odds drop (roughly 1–15), so it is only meaningful relative to the other
 * spans in the same message: intensity = delta / max delta. Users only ever see "strong" / "some".
 */
import type { Highlight } from '../api/models';
import { isNegative } from './labels';

export interface Segment {
  text: string;
  highlight: Highlight | null;
  tone: 'good' | 'bad' | null;
  /** 0..1 relative to the strongest span in this message (null for plain text). */
  intensity: number | null;
  strength: 'strong' | 'some' | null;
}

/** At or above this relative intensity a span counts as a "strong" signal. */
export const STRONG_AT = 0.6;

export function toSegments(text: string, highlights: Highlight[] | null | undefined): Segment[] {
  const spans = (highlights ?? [])
    .map((h) => ({ ...h, start: Math.max(0, Math.min(text.length, h.start)), end: Math.max(0, Math.min(text.length, h.end)) }))
    .filter((h) => h.end > h.start)
    .sort((a, b) => a.start - b.start || b.delta - a.delta);

  const max = Math.max(0, ...spans.map((s) => s.delta));
  const plain = (t: string): Segment => ({ text: t, highlight: null, tone: null, intensity: null, strength: null });
  const segments: Segment[] = [];
  let cursor = 0;
  for (const span of spans) {
    if (span.start < cursor) continue; // overlaps a span we already used
    if (span.start > cursor) segments.push(plain(text.slice(cursor, span.start)));
    const intensity = max > 0 ? Math.max(0, span.delta) / max : 1;
    segments.push({
      text: text.slice(span.start, span.end),
      highlight: span,
      tone: isNegative(span.label) ? 'bad' : 'good',
      intensity,
      strength: intensity >= STRONG_AT ? 'strong' : 'some',
    });
    cursor = span.end;
  }
  if (cursor < text.length) segments.push(plain(text.slice(cursor)));
  return segments;
}
