import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PrefsProvider } from '../i18n';
import { FriendsProvider } from '../lib/friends';
import { NewFriend } from '../pages/NewFriend';

const FRIEND = {
  id: 'custom-abc123',
  title: 'Alex',
  persona_name: 'Alex',
  persona_age: 16,
  guardedness: 'guarded',
  situation: 'Their parents are splitting up and they stopped coming to practice.',
  content_warning: 'Family stress, hopelessness, thoughts of suicide (no details).',
  review_status: 'custom',
  locales: ['en'],
  custom: true,
};

function mockFriendsApi(status: number, body: unknown) {
  const fn = vi.fn(() => Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(body) }));
  vi.stubGlobal('fetch', fn);
  return fn;
}

function renderPage() {
  return render(
    <PrefsProvider>
      <FriendsProvider>
        <MemoryRouter>
          <NewFriend />
        </MemoryRouter>
      </FriendsProvider>
    </PrefsProvider>,
  );
}

function fillValid() {
  fireEvent.change(screen.getByLabelText('Name or nickname'), { target: { value: 'Alex' } });
  fireEvent.change(screen.getByLabelText(/What happened recently/), { target: { value: FRIEND.situation } });
}

afterEach(() => vi.unstubAllGlobals());

describe('Add your own friend', () => {
  it('keeps Create disabled until name and situation are valid, with live counters', () => {
    renderPage();
    const create = screen.getByTestId('friend-create');
    expect(create).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Name or nickname'), { target: { value: 'Alex' } });
    fireEvent.change(screen.getByLabelText(/What happened recently/), { target: { value: 'too short' } });
    expect(create).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/What happened recently/), { target: { value: FRIEND.situation } });
    expect(create).toBeEnabled();
    expect(screen.getByText(`${FRIEND.situation.length}/400`)).toBeInTheDocument();
  });

  it('previews sample texts as received bubbles while typing', () => {
    renderPage();
    fireEvent.change(screen.getAllByTestId('friend-text')[0], { target: { value: 'idk im just tired lol' } });
    expect(screen.getByTestId('friend-preview')).toHaveTextContent('idk im just tired lol');
  });

  it('sends the spec body and shows a 422 message next to the right field', async () => {
    const fn = mockFriendsApi(422, { detail: { field: 'situation', reason: 'blocked', message: "That description can't be used. Try describing feelings, not details." } });
    renderPage();
    fillValid();
    fireEvent.click(screen.getByTestId('friend-create'));
    expect(await screen.findByText("That description can't be used. Try describing feelings, not details.")).toBeInTheDocument();
    expect(screen.getByLabelText(/What happened recently/)).toHaveAttribute('aria-invalid', 'true');
    const [url, init] = fn.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('/api/friends');
    expect(JSON.parse(init.body as string)).toEqual({
      name: 'Alex',
      age: 16,
      guardedness: 'guarded',
      personality: '',
      situation: FRIEND.situation,
      sample_texts: [],
      locale: 'en',
    });
  });

  it('maps sample_texts.N errors to that text box', async () => {
    mockFriendsApi(422, { detail: { field: 'sample_texts.0', reason: 'too_long', message: 'Too long.' } });
    renderPage();
    fillValid();
    fireEvent.change(screen.getAllByTestId('friend-text')[0], { target: { value: 'hey' } });
    fireEvent.click(screen.getByTestId('friend-create'));
    expect(await screen.findByText('Too long.')).toBeInTheDocument();
    expect(screen.getAllByTestId('friend-text')[0]).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows real help first when the server says real_help, then allows practice', async () => {
    mockFriendsApi(200, { friend: FRIEND, notice: 'real_help' });
    renderPage();
    fillValid();
    fireEvent.click(screen.getByTestId('friend-create'));
    expect(await screen.findByTestId('friend-real-help')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open the help page' })).toHaveAttribute('href', '/real');
    fireEvent.click(screen.getByRole('button', { name: 'Continue to practice' }));
    expect(await screen.findByTestId('content-warning')).toHaveTextContent(FRIEND.content_warning);
  });

  it('goes straight to the content warning without a notice, and never touches browser storage', async () => {
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    mockFriendsApi(200, { friend: FRIEND, notice: null });
    renderPage();
    fillValid();
    fireEvent.click(screen.getByTestId('friend-create'));
    expect(await screen.findByTestId('content-warning')).toBeInTheDocument();
    expect(screen.queryByTestId('friend-real-help')).not.toBeInTheDocument();
    const keys = setItem.mock.calls.map(([k]) => k);
    expect(keys.filter((k) => !['fr.lang', 'fr.theme', 'fr.country', 'fr.xray'].includes(k))).toEqual([]);
    setItem.mockRestore();
  });

  it('shows the privacy and safety notices', () => {
    renderPage();
    expect(screen.getByTestId('friend-privacy')).toHaveTextContent('deleted after 60 minutes');
    expect(screen.getByTestId('friend-privacy')).toHaveTextContent('OpenAI');
    expect(screen.getByTestId('friend-safety')).toHaveTextContent('practice can wait');
  });

  it("starts the session in the friend's own language (locales[0])", async () => {
    const calls: { url: string; body: unknown }[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string, init: RequestInit) => {
        calls.push({ url, body: init?.body ? JSON.parse(init.body as string) : null });
        const body = url === '/api/friends' ? { friend: { ...FRIEND, locales: ['es'] }, notice: null } : { session_id: 's1' };
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
      }),
    );
    renderPage();
    fillValid();
    fireEvent.click(screen.getByTestId('friend-create'));
    await screen.findByTestId('content-warning');
    fireEvent.click(screen.getByRole('button', { name: /I understand/ }));
    await vi.waitFor(() => expect(calls.some((c) => c.url === '/api/sessions')).toBe(true));
    expect(calls.find((c) => c.url === '/api/sessions')!.body).toMatchObject({ scenario_id: FRIEND.id, locale: 'es' });
  });
});
