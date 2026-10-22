import { ApiError, api, request } from '../api/client';

function mockFetch(impl: () => Promise<Partial<Response>>) {
  const fn = vi.fn(impl);
  vi.stubGlobal('fetch', fn);
  return fn;
}
const json = (status: number, body: unknown) => () =>
  Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(body) } as Partial<Response>);

afterEach(() => vi.unstubAllGlobals());

describe('API client', () => {
  it('returns parsed JSON and calls the relative /api URL', async () => {
    const fn = mockFetch(json(200, [{ id: 'after-the-breakup' }]));
    await expect(api.scenarios()).resolves.toEqual([{ id: 'after-the-breakup' }]);
    expect(fn.mock.calls[0][0]).toBe('/api/scenarios');
  });

  it('sends POST bodies as JSON', async () => {
    const fn = mockFetch(json(200, {}));
    await api.send('s_1', 'hey', undefined);
    const [url, init] = fn.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('/api/sessions/s_1/messages');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body as string)).toEqual({ text: 'hey' });
  });

  it("uses FastAPI's string detail as the error message", async () => {
    mockFetch(json(404, { detail: 'Session not found or expired.' }));
    const error = await api.session('nope').catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(404);
    expect(error.message).toBe('Session not found or expired.');
    expect(error.offline).toBe(false);
  });

  it('reads validation errors (422 detail arrays)', async () => {
    mockFetch(json(422, { detail: [{ msg: 'String should have at least 1 character' }] }));
    await expect(request('/x')).rejects.toMatchObject({ status: 422, message: 'String should have at least 1 character' });
  });

  it('turns a network failure into a friendly offline error', async () => {
    mockFetch(() => Promise.reject(new TypeError('Failed to fetch')));
    const error = await api.health().catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.offline).toBe(true);
    expect(error.message).toMatch(/Can't reach/);
  });

  it('keeps a generic message when the error body is not JSON', async () => {
    mockFetch(() => Promise.resolve({ ok: false, status: 502, json: () => Promise.reject(new SyntaxError('bad')) }));
    await expect(request('/x')).rejects.toMatchObject({ status: 502, message: 'Something went wrong (error 502).' });
  });

  it('URL-encodes query parameters', async () => {
    const fn = mockFetch(json(200, {}));
    await api.realmode('es', '*');
    expect(fn.mock.calls[0][0]).toBe('/api/realmode?lang=es&country=*');
  });
});
