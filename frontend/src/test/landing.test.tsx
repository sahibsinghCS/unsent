import { screen, within } from '@testing-library/react';
import recorded from '../content/demo-transcript.json';
import { Landing } from '../pages/Landing';
import { renderApp } from './render';

describe('Landing example conversation', () => {
  it('is a recorded real run that reaches a successful ending in both languages', () => {
    expect(recorded.components.engine).toBe('real');
    for (const run of [recorded.en, recorded.es]) {
      expect(run.turns.at(-1)?.status).toBe('ended_success');
      expect(run.turns.some((t) => t.friend?.seen)).toBe(true);
      expect(run.turns.every((t) => !t.friend || t.friend.seen || t.friend.voice === 'bank')).toBe(true);
    }
  });

  it('renders every recorded turn with the numbers the engine computed', () => {
    renderApp(<Landing />);
    const rows = within(screen.getByTestId('annotated-example')).getAllByTestId('example-turn');
    expect(rows).toHaveLength(recorded.en.turns.length);
    recorded.en.turns.forEach((turn, i) => {
      const row = rows[i];
      expect(row.textContent).toContain(turn.text);
      expect(row.textContent).toContain(`${Math.round(turn.trust_before)} to ${Math.round(turn.trust_after)}`);
      expect(row.textContent).toContain(`${Math.round(turn.guardian.ms)} ms`);
    });
    expect(screen.getByTestId('real-run-note').textContent).toContain('numbers are what the engine computed');
  });
});
