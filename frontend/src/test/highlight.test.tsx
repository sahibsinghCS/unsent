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
    expect(toSegments('hey', [])).toEqual([{ text: 'hey', highlight: null, tone: null }]);
    expect(toSegments('hey', null)).toHaveLength(1);
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
    expect(screen.getByTestId('highlighted')).toHaveTextContent(/^hey are you ok \(checked in\)\? lol \(dismissed\)$/);
  });
});
