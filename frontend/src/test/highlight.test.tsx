import { screen } from '@testing-library/react';
import type { Highlight } from '../api/models';
import { HighlightedText } from '../components/HighlightedText';
import { toSegments } from '../lib/highlight';
import { renderApp } from './render';

const h = (start: number, end: number, label: Highlight['label'], delta = 0.5): Highlight => ({ start, end, label, delta, text: '' });

describe('toSegments', () => {
  it('splits text around highlight spans using start/end offsets', () => {
    const text = "lol you'll be fine";
    const segs = toSegments(text, [h(4, 18, 'dismissed')]);
    expect(segs.map((s) => [s.text, s.tone])).toEqual([
      ['lol ', null],
      ["you'll be fine", 'bad'],
    ]);
  });

  it('marks helping labels green and negative labels red', () => {
    const segs = toSegments('are you ok lol', [h(0, 10, 'checked_in'), h(11, 14, 'dismissed')]);
    expect(segs.filter((s) => s.highlight).map((s) => s.tone)).toEqual(['good', 'bad']);
  });

  it('never loses or duplicates characters, even with overlapping or out-of-range spans', () => {
    const text = 'that sounds really hard';
    const segs = toSegments(text, [h(5, 18, 'validated', 0.9), h(0, 11, 'validated', 0.2), h(20, 999, 'validated'), h(-5, 2, 'checked_in'), h(7, 7, 'validated')]);
    expect(segs.map((s) => s.text).join('')).toBe(text);
  });

  it('returns the whole text when there are no highlights', () => {
    expect(toSegments('hey', [])).toEqual([{ text: 'hey', highlight: null, tone: null, intensity: null, strength: null }]);
    expect(toSegments('hey', null)).toHaveLength(1);
  });
});

describe('relative strength (Highlight.delta is a log-odds drop, ~1–15)', () => {
  it('scales by the strongest span in the message and labels it strong / some', () => {
    const segs = toSegments("i'll check on you tonight, text 988", [h(0, 25, 'follow_up', 12.36), h(27, 35, 'referred_988', 8.66), h(5, 10, 'follow_up', 1)]);
    const marked = segs.filter((s) => s.highlight);
    expect(marked.map((s) => s.strength)).toEqual(['strong', 'strong']);
    expect(marked[0].intensity).toBe(1);
    expect(marked[1].intensity).toBeCloseTo(0.7, 2);
    const weak = toSegments('hey how are you', [h(0, 3, 'checked_in', 10), h(4, 7, 'checked_in', 2)]).filter((s) => s.highlight);
    expect(weak.map((s) => s.strength)).toEqual(['strong', 'some']);
  });

  it('never shows the raw log-odds number', () => {
    renderApp(<HighlightedText text="that sounds really heavy" highlights={[h(0, 24, 'validated', 4.64)]} />);
    const mark = screen.getByTestId('highlighted').querySelector('mark')!;
    expect(mark.title).toBe('validated · strong signal');
    expect(screen.getByTestId('highlighted').textContent).not.toMatch(/4\.6/);
  });
});

describe('<HighlightedText>', () => {
  it('renders highlighted spans as <mark> with the right tone', () => {
    renderApp(<HighlightedText text="hey are you ok? lol" highlights={[h(4, 14, 'checked_in'), h(16, 19, 'dismissed')]} />);
    const marks = screen.getByTestId('highlighted').querySelectorAll('mark');
    expect(marks).toHaveLength(2);
    expect(marks[0]).toHaveTextContent('are you ok');
    expect(marks[0].dataset.tone).toBe('good');
    expect(marks[1].dataset.tone).toBe('bad');
    expect(screen.getByTestId('highlighted')).toHaveTextContent(/^hey are you ok \(checked in, strong signal\)\? lol \(dismissed, strong signal\)$/);
  });
});

describe('rewrite gain wording', () => {
  it('names the skill a rewrite adds, never a bare percentage', async () => {
    const { translate } = await import('../i18n');
    const chip = translate('en', 'feedback.gain', { skill: translate('en', 'skills_verb.listen') });
    expect(chip).toBe('adds: listening');
    expect(chip).not.toMatch(/%/);
    expect(translate('es', 'feedback.gain', { skill: translate('es', 'skills_verb.listen') })).toBe('suma: escuchar');
  });
});
