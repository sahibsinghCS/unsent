import type { HeadlineMetric, MetricRecord } from '../api/models';
import { formatMetric, groupRecords, localized, measuredHeadlines } from '../lib/metrics';

describe('headline metric formatting', () => {
  it('formats each kind', () => {
    expect(formatMetric(0.96, 'percent')).toBe('96%');
    expect(formatMetric(0, 'percent')).toBe('0%');
    expect(formatMetric(0.9713, 'percent')).toBe('97.1%');
    expect(formatMetric(0.8183, 'score')).toBe('0.82');
    expect(formatMetric(5, 'messages')).toBe('5');
    expect(formatMetric(1234, 'count')).toBe('1,234');
    expect(formatMetric(null, 'score')).toBe('—');
  });

  it('hides headlines that are not measured yet', () => {
    const base = { lane: 'ml', metric: 'm', split: 's', format: 'score', better: 'higher', label: { en: 'x' }, explain: { en: 'y' }, n: 1 } as const;
    const items: HeadlineMetric[] = [
      { ...base, id: 'a', found: true, value: 0.8 },
      { ...base, id: 'b', found: false, value: null },
    ];
    expect(measuredHeadlines(items).map((h) => h.id)).toEqual(['a']);
    expect(measuredHeadlines(undefined)).toEqual([]);
  });

  it('picks the UI language and falls back to English', () => {
    expect(localized({ en: 'keyword matching', es: 'buscar palabras clave' }, 'es')).toBe('buscar palabras clave');
    expect(localized({ en: 'only english' }, 'es')).toBe('only english');
  });
});

describe('full metrics table', () => {
  const records: MetricRecord[] = [
    { lane: 'safety', metric: 'self_risk_recall', value: 1, split: 'test' },
    { lane: 'ml', metric: 'macro_f1_ensemble', value: 0.82, split: 'test_freeform' },
    { lane: 'ml', metric: 'ece_after_calibration', value: 0.02, split: 'test_freeform', notes: 'Platt' },
  ];
  it('groups by lane, alphabetically', () => {
    expect(groupRecords(records).map(([lane, rows]) => [lane, rows.length])).toEqual([
      ['ml', 2],
      ['safety', 1],
    ]);
  });
  it('searches lane, metric, split and notes', () => {
    expect(groupRecords(records, 'platt')).toEqual([['ml', [records[2]]]]);
    expect(groupRecords(records, 'SAFETY')[0][0]).toBe('safety');
    expect(groupRecords(records, 'nothing-matches')).toEqual([]);
  });
});
