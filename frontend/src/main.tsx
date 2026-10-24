import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from './App';
import { PrefsProvider } from './i18n';
import { FriendsProvider } from './lib/friends';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PrefsProvider>
      <FriendsProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </FriendsProvider>
    </PrefsProvider>
  </StrictMode>,
);
