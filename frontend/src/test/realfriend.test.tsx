import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ApiError, api, type AnalyzeResult } from '../api/client';
import { DeleteFriendButton } from '../components/DeleteFriend';
import { PrefsProvider } from '../i18n';
import { FriendsProvider } from '../lib/friends';
import { Noticed, RealFriend } from '../pages/RealFriend';

afterEach(() => vi.unstubAllGlobals());

const wrap = (ui: React.ReactNode) =>
  render(
    <PrefsProvider>
      <FriendsProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </FriendsProvider>
    </PrefsProvider>,
  );

const result = (urgency: AnalyzeResult['urgency'], signs: string[] = []): AnalyzeResult => ({
  draft: { personality: 'dry humor', situation: 'Their parents are splitting up.', sample_texts: ['idk'], guardedness: 'guarded' },
  signs,
  urgency,
});

describe('Practice for a real friend', () => {
  it('needs the consent box ticked before picking screenshots', () => {
    wrap(<RealFriend />);
    const go = screen.getByTestId('consent-continue');
    expect(go).toBeDisabled();
    fireEvent.click(screen.getByTestId('consent'));
    expect(go).toBeEnabled();
    fireEvent.click(go);
    expect(screen.getByTestId('pick-images')).toBeInTheDocument();
    expect(screen.getByTestId('fill-myself')).toBeInTheDocument();
  });

  it('shows real help before anything else when urgency is tell_an_adult_now', () => {
    wrap(<Noticed result={result('tell_an_adult_now', ['talks_about_dying', 'withdrawing'])} onContinue={() => undefined} />);
    const help = screen.getByTestId('urgent-help');
    const noticed = screen.getByTestId('noticed');
    expect(help.compareDocumentPosition(noticed) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(help).toHaveTextContent('Practice can wait');
    expect(help.querySelector('a[href="tel:988"]')).not.toBeNull();
    expect(screen.getByTestId('signs')).toHaveTextContent('talked about dying or not being here');
    expect(screen.getByText('These are warning signs to check in about, not a diagnosis.')).toBeInTheDocument();
    expect(screen.getByTestId('to-form').className).toContain('btn-ghost'); // practice is the secondary action
  });

  it('shows a gentle check-in line and no help card for check_in_soon', () => {
    wrap(<Noticed result={result('check_in_soon', ['withdrawing'])} onContinue={() => undefined} />);
    expect(screen.queryByTestId('urgent-help')).not.toBeInTheDocument();
    expect(screen.getByTestId('check-in-soon')).toHaveTextContent('It sounds like a good time to check in.');
  });

  it("passes the server's analyze error message through (needs_ai, unreadable…)", async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 503, json: () => Promise.resolve({ detail: { reason: 'needs_ai', message: 'Reading screenshots needs the AI.' } }) })),
    );
    const err = await api.analyzeFriend(['data:image/jpeg;base64,AAAA'], 'en').catch((e) => e as ApiError);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).message).toBe('Reading screenshots needs the AI.');
    expect(((err as ApiError).detail as { reason: string }).reason).toBe('needs_ai');
  });
});

describe('Delete a custom friend', () => {
  it('asks first, sends DELETE, then runs onDeleted', async () => {
    const fetchFn = vi.fn((_url: string, _init?: RequestInit) => Promise.resolve({ ok: true, status: 204, json: () => Promise.reject(new Error('no body')) }));
    vi.stubGlobal('fetch', fetchFn);
    const done = vi.fn();
    wrap(
      <Routes>
        <Route path="*" element={<DeleteFriendButton id="custom-abc" name="Alex" onDeleted={done} />} />
      </Routes>,
    );
    fireEvent.click(screen.getByTestId('delete-friend'));
    expect(screen.getByText('This ends your practice chats with them. Nothing is kept.')).toBeInTheDocument();
    expect(fetchFn).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId('delete-friend-confirm'));
    await waitFor(() => expect(done).toHaveBeenCalled());
    expect(fetchFn.mock.calls[0][0]).toBe('/api/friends/custom-abc');
    expect(fetchFn.mock.calls[0][1]?.method).toBe('DELETE');
  });
});
