// Render helper: wraps components in the providers the app uses.
import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { PrefsProvider } from '../i18n';

export function renderApp(ui: ReactElement) {
  return render(
    <PrefsProvider>
      <MemoryRouter>{ui}</MemoryRouter>
    </PrefsProvider>,
  );
}
