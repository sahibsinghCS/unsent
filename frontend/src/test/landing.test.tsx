import { fireEvent, screen, within } from '@testing-library/react';
import recorded from '../content/demo_transcript.json';
import { Landing } from '../pages/Landing';
import { renderApp } from './render';

describe('Landing example conversation', () => {
  it('is a recorded real run with a Read dip and reviewed lines, in both languages', () => {
    for (const run of [recorded.en, recorded.es]) {
      expect(run.turns.some((t) => t.seen)).toBe(true);
      expect(run.turns.every((t) => t.seen || t.line_id)).toBe(true);
      run.turns.slice(1).forEach((t, i) => expect(t.trust_before).toBe(run.turns[i].trust_after));
    }
  });

  it('renders every recorded turn with the numbers the engine computed', () => {
    renderApp(<Landing />);
    const more = screen.getByTestId('example-more');
    expect(within(screen.getByTestId('annotated-example')).getAllByTestId('example-turn')).toHaveLength(3);
    expect(more.getAttribute('aria-expanded')).toBe('false');
    fireEvent.click(more);
    expect(more.getAttribute('aria-expanded')).toBe('true');
    const rows = within(screen.getByTestId('annotated-example')).getAllByTestId('example-turn');
    expect(rows).toHaveLength(recorded.en.turns.length);
    recorded.en.turns.forEach((turn, i) => {
      const text = rows[i].textContent ?? '';
      expect(text).toContain(turn.you);
      turn.friend.forEach((b) => expect(text).toContain(b));
      expect(text).toContain(`${Math.round(turn.trust_before)} to ${Math.round(turn.trust_after)}`);
      expect(text).toContain(`${Math.round(turn.guardian_ms)} ms`);
    });
    expect(screen.getByTestId('real-run-note').textContent).toContain('Every number is what the engine computed');
  });
});
