import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PrefsProvider } from '../i18n';
import { WhatIf } from '../pages/WhatIf';

vi.mock('react-chartjs-2', () => ({ Line: () => null }));

afterEach(() => vi.unstubAllGlobals());

function mockApi(whatif: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      const body = url.includes('/whatif') ? whatif : { session_id: 's1', scenario_id: 'x', head_id: 'a', root_id: 'a', locale: 'en', state: {}, nodes: [] };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
    }),
  );
}

describe('What-if page', () => {
  it('shows a friendly message when no verified better reply exists', async () => {
    mockApi({ from_node_id: 'u1', paths: [], best_index: 0, simulated: true });
    render(
      <PrefsProvider>
        <MemoryRouter initialEntries={['/whatif/s1?node=u1']}>
          <Routes>
            <Route path="/whatif/:sessionId" element={<WhatIf />} />
          </Routes>
        </MemoryRouter>
      </PrefsProvider>,
    );
    expect(await screen.findByTestId('whatif-empty')).toHaveTextContent("We couldn't find a verified better reply for this message. Try another one.");
    expect(screen.queryByTestId('whatif-path')).not.toBeInTheDocument();
  });

  it('shows the Best rule and how many messages each path took, so a higher-trust path losing makes sense', async () => {
    const state = (trust: number, level: number) => ({ trust, level, status: 'active', last_delta: 0, last_breakdown: {} });
    const node = (id: string, role: 'user' | 'friend', trust: number, level: number) => ({ id, parent_id: null, role, bubbles: [id], state_after: state(trust, level), events: role === 'user' ? { validated: 0.9 } : null });
    const path = (strategy: string, steps: [number, number][]) => ({
      candidate_text: strategy,
      strategy,
      critic_score: 0.9,
      value: 0,
      trust_series: [34, ...steps.map(([t]) => t)],
      nodes: steps.flatMap(([t, l], i) => [node(`${strategy}-u${i}`, 'user', t, l), node(`${strategy}-f${i}`, 'friend', t, l)]),
    });
    mockApi({
      from_node_id: 'u1',
      best_index: 0,
      simulated: true,
      paths: [path('ask_directly', [[50, 2], [66, 2], [83, 3]]), path('refer', [[45, 1], [60, 2], [75, 2], [92, 3]])],
    });
    render(
      <PrefsProvider>
        <MemoryRouter initialEntries={['/whatif/s1?node=u1']}>
          <Routes>
            <Route path="/whatif/:sessionId" element={<WhatIf />} />
          </Routes>
        </MemoryRouter>
      </PrefsProvider>,
    );
    expect(await screen.findByTestId('best-rule')).toHaveTextContent('Best = the most trust and openness in the fewest messages.');
    const facts = screen.getAllByTestId('path-facts').map((el) => el.textContent);
    expect(facts[0]).toContain('in 3 messages');
    expect(facts[1]).toContain('in 4 messages');
  });
});
