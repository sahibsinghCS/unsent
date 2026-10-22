// Routes. Every page renders inside <Layout> (top bar with "I need help now" + safety footer).
import { useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Chat } from './pages/Chat';
import { Feedback } from './pages/Feedback';
import { How } from './pages/How';
import { Landing } from './pages/Landing';
import { NotFound } from './pages/NotFound';
import { Practice } from './pages/Practice';
import { Privacy } from './pages/Privacy';
import { RealMode } from './pages/RealMode';
import { WhatIf } from './pages/WhatIf';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => window.scrollTo(0, 0), [pathname]);
  return null;
}

export function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Landing />} />
          <Route path="practice" element={<Practice />} />
          <Route path="chat/:sessionId" element={<Chat />} />
          <Route path="feedback/:sessionId" element={<Feedback />} />
          <Route path="whatif/:sessionId" element={<WhatIf />} />
          <Route path="real" element={<RealMode />} />
          <Route path="how" element={<How />} />
          <Route path="privacy" element={<Privacy />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  );
}
