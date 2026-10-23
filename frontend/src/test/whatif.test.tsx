import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PrefsProvider } from '../i18n';
import { WhatIf } from '../pages/WhatIf';

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
});
