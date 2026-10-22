/**
 * Turns a message plus the critic's highlight spans (character offsets) into plain/highlighted
 * segments for rendering. Overlapping or out-of-range spans are handled: the earlier/stronger span
 * wins and nothing is ever dropped or duplicated from the original text.
 */
import type { Highlight } from '../api/models';
import { isNegative } from './labels';

export interface Segment {
  text: string;
  highlight: Highlight | null;
  tone: 'good' | 'bad' | null;
}

export function toSegments(text: string, highlights: Highlight[] | null | undefined): Segment[] {
  const spans = (highlights ?? [])
    .map((h) => ({ ...h, start: Math.max(0, Math.min(text.length, h.start)), end: Math.max(0, Math.min(text.length, h.end)) }))
    .filter((h) => h.end > h.start)
    .sort((a, b) => a.start - b.start || b.delta - a.delta);

  const segments: Segment[] = [];
  let cursor = 0;
  for (const span of spans) {
    if (span.start < cursor) continue; // overlaps a span we already used
    if (span.start > cursor) segments.push({ text: text.slice(cursor, span.start), highlight: null, tone: null });
    segments.push({ text: text.slice(span.start, span.end), highlight: span, tone: isNegative(span.label) ? 'bad' : 'good' });
    cursor = span.end;
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), highlight: null, tone: null });
  return segments;
}
